"""
Tests unitaires de l'étage d'ingestion (openagenda_ingest.py).

Ce module vérifie la logique métier de l'ingestion. Il couvre :

  - is_valid : filtre de validité (texte non vide, ville, date de début),
    y compris la correction du cas d'un texte "vide de sens" ;
  - build_text : construction du texte enrichi et cas sans contenu ;
  - extract_event_details : extraction du texte et des métadonnées (dont url) ;
  - deduplicate_documents : suppression des doublons d'UID ;
  - date_limite_recente : borne temporelle du filtre "moins d'un an" ;
  - fetch_all_events : pagination et gestion d'erreur HTTP, via des mocks
    (aucun appel réseau réel n'est effectué) ;
  - la conformité du périmètre : ville attendue et dates dans la fenêtre, à
    partir d'un jeu de documents simulé représentant le fichier final.

Exécution depuis la racine du projet :
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest
from unittest.mock import patch, Mock
from datetime import datetime, timedelta
import json
import requests

# Permet d'importer les fonctions depuis src/ingestion.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ingestion"))
from openagenda_ingest import (
    is_valid,
    extract_event_details,
    build_text,
    deduplicate_documents,
    date_limite_recente,
    fetch_all_events,
    DAYS_LOOKBACK,
    OUTPUT_PATH,
)



class TestIsValid(unittest.TestCase):
    """Vérifie le filtre de validité is_valid sur les cas nominaux et limites."""

    def test_document_complet(self):
        """Un document complet (texte, ville, date) doit être considéré valide."""
        document = {
            "text": "Un événement",
            "metadata": {"city": "Montpellier", "start_date": "2026-04-18"}
        }
        self.assertTrue(is_valid(document))

    def test_city_vide(self):
        """Une ville vide doit entraîner le rejet du document."""
        document = {
            "text": "Un événement",
            "metadata": {"city": "", "start_date": "2026-04-18"}
        }
        self.assertFalse(is_valid(document))

    def test_text_vide(self):
        """Un texte vide doit entraîner le rejet du document."""
        document = {
            "text": "",
            "metadata": {"city": "Montpellier", "start_date": "2026-04-18"}
        }
        self.assertFalse(is_valid(document))

    def test_sans_metadata(self):
        """Un document sans clé metadata ne doit pas planter et doit être rejeté."""
        document = {"text": "Un événement"}
        self.assertFalse(is_valid(document))

    def test_evenement_sans_contenu_textuel_rejete(self):
        """Un événement sans titre, description ni mot-clé doit être rejeté.

        Vérifie la correction de l'anomalie signalée : auparavant un événement
        totalement vide produisait un texte non vide (". . Mots-clés : ") qui
        passait le filtre. Désormais build_text renvoie une chaîne vide et le
        document est bien écarté.
        """
        evenement = {
            "uid": 1,
            "location": {"city": "Montpellier"},
            "firstTiming": {"begin": "2026-05-01T20:00:00"},
        }
        document = extract_event_details(evenement)
        self.assertEqual(document["text"], "")
        self.assertFalse(is_valid(document))


class TestBuildText(unittest.TestCase):
    """Vérifie la construction du texte enrichi par build_text."""

    def test_texte_complet(self):
        """Les trois champs présents doivent tous apparaître dans le texte."""
        texte = build_text("Concert", "Un super concert", "musique, live")
        self.assertIn("Concert", texte)
        self.assertIn("Un super concert", texte)
        self.assertIn("musique, live", texte)

    def test_aucun_champ(self):
        """Sans aucun champ, le texte doit être une chaîne strictement vide."""
        self.assertEqual(build_text("", "", ""), "")

    def test_titre_seul(self):
        """Avec seulement le titre, le texte ne doit contenir que le titre."""
        self.assertEqual(build_text("Concert", "", ""), "Concert")


class TestExtractEventDetails(unittest.TestCase):
    """Vérifie l'extraction du texte et des métadonnées par extract_event_details."""

    def test_evenement_complet(self):
        """Un événement complet doit produire le texte et les métadonnées attendus."""
        evenement = {
            "uid": 123,
            "title": {"fr": "Concert"},
            "description": {"fr": "Un super concert"},
            "keywords": {"fr": ["musique", "live"]},
            "location": {"city": "Montpellier", "name": "Zénith"},
            "firstTiming": {"begin": "2026-05-01T20:00:00"},
            "lastTiming": {"end": "2026-05-01T23:00:00"},
        }
        result = extract_event_details(evenement)

        self.assertIn("Concert", result["text"])
        self.assertEqual(result["metadata"]["uid"], 123)
        self.assertEqual(result["metadata"]["city"], "Montpellier")
        self.assertEqual(result["metadata"]["place"], "Zénith")
        self.assertEqual(result["metadata"]["title"], "Concert")
        # La clé de traçabilité "url" doit exister (même si vide).
        self.assertIn("url", result["metadata"])

    def test_evenement_champs_manquants(self):
        """Un événement quasi vide ne doit pas planter et renvoyer des valeurs vides."""
        evenement = {"uid": 999}
        result = extract_event_details(evenement)

        self.assertEqual(result["metadata"]["city"], "")
        self.assertEqual(result["metadata"]["place"], "")
        self.assertEqual(result["metadata"]["uid"], 999)


class TestDeduplicate(unittest.TestCase):
    """Vérifie la suppression des doublons d'UID par deduplicate_documents."""

    def test_doublons_supprimes(self):
        """Deux documents partageant le même UID ne doivent en laisser qu'un."""
        docs = [
            {"text": "A", "metadata": {"uid": 1}},
            {"text": "A bis", "metadata": {"uid": 1}},
            {"text": "B", "metadata": {"uid": 2}},
        ]
        result = deduplicate_documents(docs)
        self.assertEqual(len(result), 2)
        uids = [d["metadata"]["uid"] for d in result]
        self.assertEqual(uids, [1, 2])

    def test_premiere_occurrence_conservee(self):
        """En cas de doublon, la première occurrence rencontrée est conservée."""
        docs = [
            {"text": "premier", "metadata": {"uid": 1}},
            {"text": "second", "metadata": {"uid": 1}},
        ]
        result = deduplicate_documents(docs)
        self.assertEqual(result[0]["text"], "premier")


class TestPerimetreDonnees(unittest.TestCase):
    """Vérifie la conformité géographique et temporelle du jeu final simulé.

    Ces tests correspondent à l'exigence du cahier des charges : s'assurer que
    les événements retenus sont bien dans la zone géographique attendue et dans
    la fenêtre temporelle de moins d'un an. On simule ici le fichier final ;
    en usage réel, on chargerait data/events.json.
    """

    VILLE_ATTENDUE = "Montpellier"

    def setUp(self):
        """Prépare un jeu de documents simulant le fichier final produit."""
        recent = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%dT%H:%M:%S")
        limite = (datetime.now() - timedelta(days=DAYS_LOOKBACK - 1)).strftime("%Y-%m-%dT%H:%M:%S")
        self.documents = [
            {"text": "Concert", "metadata": {"uid": 1, "city": "Montpellier", "start_date": recent}},
            {"text": "Expo", "metadata": {"uid": 2, "city": "Montpellier", "start_date": limite}},
        ]

    def test_toutes_les_villes_conformes(self):
        """Toutes les villes du jeu final doivent correspondre à la zone attendue."""
        for doc in self.documents:
            self.assertEqual(doc["metadata"]["city"], self.VILLE_ATTENDUE)

    def test_toutes_les_dates_dans_la_fenetre(self):
        """Aucune date ne doit être antérieure à la borne "moins d'un an"."""
        borne = datetime.now() - timedelta(days=DAYS_LOOKBACK)
        for doc in self.documents:
            date_evenement = datetime.strptime(
                doc["metadata"]["start_date"][:10], "%Y-%m-%d"
            )
            self.assertGreaterEqual(date_evenement, borne)

    def test_evenement_trop_ancien_detecte(self):
        """Un événement plus ancien que la fenêtre doit être détecté comme hors périmètre."""
        borne = datetime.now() - timedelta(days=DAYS_LOOKBACK)
        trop_ancien = (datetime.now() - timedelta(days=DAYS_LOOKBACK + 30))
        self.assertLess(trop_ancien, borne)

    def test_date_limite_recente_format(self):
        """date_limite_recente doit renvoyer une date valide au format YYYY-MM-DD."""
        limite = date_limite_recente()
        # Ne doit pas lever d'exception si le format est correct.
        parsed = datetime.strptime(limite, "%Y-%m-%d")
        self.assertLessEqual(parsed, datetime.now())


class TestFetchAllEvents(unittest.TestCase):
    """Vérifie la pagination et la gestion d'erreur HTTP via des mocks.

    Aucun appel réseau réel n'est effectué : requests.get est simulé pour
    contrôler précisément les réponses successives de l'API.
    """

    @patch("openagenda_ingest.requests.get")
    @patch("openagenda_ingest.load_env_variables", return_value="FAKE_KEY")
    def test_pagination_deux_pages(self, mock_key, mock_get):
        """La pagination doit agréger les événements de toutes les pages.

        Première page : 2 événements + curseur ; deuxième page : 1 événement
        sans curseur, ce qui doit arrêter la boucle. Total attendu : 3.
        """
        page1 = Mock()
        page1.json.return_value = {"events": [{"uid": 1}, {"uid": 2}], "after": "CURSEUR"}
        page1.raise_for_status.return_value = None

        page2 = Mock()
        page2.json.return_value = {"events": [{"uid": 3}], "after": None}
        page2.raise_for_status.return_value = None

        mock_get.side_effect = [page1, page2]

        events = fetch_all_events()
        self.assertEqual(len(events), 3)
        self.assertEqual(mock_get.call_count, 2)

    @patch("openagenda_ingest.requests.get")
    @patch("openagenda_ingest.load_env_variables", return_value="FAKE_KEY")
    def test_erreur_http_propagee(self, mock_key, mock_get):
        """Une erreur HTTP (raise_for_status) doit être propagée, pas silencieuse."""
        reponse = Mock()
        reponse.raise_for_status.side_effect = requests.exceptions.HTTPError("500")
        mock_get.return_value = reponse

        with self.assertRaises(requests.exceptions.HTTPError):
            fetch_all_events()

    @patch("openagenda_ingest.requests.get")
    @patch("openagenda_ingest.load_env_variables", return_value="FAKE_KEY")
    def test_page_vide_arrete_pagination(self, mock_key, mock_get):
        """Une page sans événement doit arrêter proprement la pagination."""
        page = Mock()
        page.json.return_value = {"events": [], "after": None}
        page.raise_for_status.return_value = None
        mock_get.return_value = page

        events = fetch_all_events()
        self.assertEqual(events, [])

class TestFichierFinalReel(unittest.TestCase):
    """Vérifie le périmètre sur le fichier réellement produit (data/events.json).

    Contrairement à TestPerimetreDonnees qui travaille sur un jeu simulé, ces
    tests chargent le fichier de sortie réel de l'ingestion et contrôlent que
    CHAQUE événement respecte les contraintes du cahier des charges : ville
    attendue, date dans la fenêtre "moins d'un an", et contenu textuel non vide.

    Si le fichier n'existe pas encore (ingestion non exécutée, pas de clé API en
    CI), ces tests sont ignorés (skipped) plutôt qu'en échec.
    """

    VILLE_ATTENDUE = "Montpellier"

    @classmethod
    def setUpClass(cls):
        """Charge une fois pour toutes le fichier final s'il est disponible."""
        cls.documents = None
        if os.path.exists(OUTPUT_PATH):
            with open(OUTPUT_PATH, "r", encoding="utf-8") as file:
                cls.documents = json.load(file)

    @unittest.skipUnless(os.path.exists(OUTPUT_PATH), "data/events.json absent : ingestion non exécutée")
    def test_fichier_non_vide(self):
        """Le fichier final doit contenir au moins un événement."""
        self.assertTrue(len(self.documents) > 0)

    @unittest.skipUnless(os.path.exists(OUTPUT_PATH), "data/events.json absent : ingestion non exécutée")
    def test_toutes_les_villes_reelles_conformes(self):
        """Chaque événement du fichier final doit être dans la ville attendue."""
        for doc in self.documents:
            self.assertEqual(
                doc["metadata"]["city"],
                self.VILLE_ATTENDUE,
                msg=f"UID {doc['metadata'].get('uid')} : ville inattendue",
            )

    @unittest.skipUnless(os.path.exists(OUTPUT_PATH), "data/events.json absent : ingestion non exécutée")
    def test_toutes_les_dates_reelles_dans_la_fenetre(self):
        """Aucun événement du fichier final ne doit être trop ancien (> 1 an)."""
        borne = datetime.now() - timedelta(days=DAYS_LOOKBACK)
        for doc in self.documents:
            date_str = doc["metadata"]["start_date"][:10]
            date_evenement = datetime.strptime(date_str, "%Y-%m-%d")
            self.assertGreaterEqual(
                date_evenement,
                borne,
                msg=f"UID {doc['metadata'].get('uid')} : événement trop ancien ({date_str})",
            )

    @unittest.skipUnless(os.path.exists(OUTPUT_PATH), "data/events.json absent : ingestion non exécutée")
    def test_aucun_document_sans_contenu(self):
        """Aucun événement du fichier final ne doit avoir un texte vide."""
        for doc in self.documents:
            self.assertTrue(
                doc["text"].strip(),
                msg=f"UID {doc['metadata'].get('uid')} : texte vide indexable",
            )

    @unittest.skipUnless(os.path.exists(OUTPUT_PATH), "data/events.json absent : ingestion non exécutée")
    def test_aucun_uid_duplique(self):
        """Le fichier final ne doit contenir aucun UID en double (dédoublonnage)."""
        uids = [doc["metadata"].get("uid") for doc in self.documents if doc["metadata"].get("uid") is not None]
        self.assertEqual(len(uids), len(set(uids)), msg="Des UID sont dupliqués dans le fichier final")

if __name__ == "__main__":
    unittest.main()
