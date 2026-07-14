"""
Tests unitaires de l'étage RAG (build_rag.py).

Ce module teste les fonctions du système RAG relevant de la logique « pure »,
qui ne dépendent d'aucun service externe :

  - format_context : mise en forme des résultats en un contexte textuel tracé
    (titre, UID, lieu, dates, URL source) destiné au LLM ;
  - filter_by_threshold : filtrage des résultats selon le seuil de pertinence,
    incluant le cas de refus (aucun résultat sous le seuil) ;
  - format_sources : construction de la liste des sources restituées à
    l'utilisateur (traçabilité).

Les fonctions load_index, generate_answer et answer_question ne sont pas testées
ici car elles dépendent d'appels réseau (chargement de l'index, API Mistral) :
leurs sorties sont non déterministes, coûteuses en quota et sensibles à la
latence. En production, elles seraient testées via des mocks ; ce point est
documenté comme limite dans le rapport technique.

Pour s'affranchir de FAISS, on utilise un faux objet résultat (FakeResult) qui
imite l'interface attendue (attributs page_content et metadata).

Exécution depuis la racine du projet :
    python -m unittest discover -s tests -v
"""

import os
import sys
import unittest

# Permet d'importer les fonctions depuis src/rag.
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "rag"))
from build_rag import format_context, filter_by_threshold, format_sources, SIMILARITY_THRESHOLD


class FakeResult:
    """Faux résultat imitant un objet renvoyé par FAISS.

    Reproduit uniquement l'interface consommée par les fonctions testées, à savoir
    les attributs page_content (texte de l'événement) et metadata (dictionnaire
    des métadonnées). Cela évite de dépendre d'un vrai index FAISS dans les tests.
    """
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


class TestFormatContext(unittest.TestCase):
    """Vérifie la mise en forme du contexte par format_context."""

    def test_formatage_simple(self):
        """Le contexte formaté doit contenir le texte et les métadonnées de traçabilité.

        Avec un seul résultat, on vérifie que le texte, le lieu, la ville, mais
        aussi les champs de traçabilité (titre, UID, URL) apparaissent bien.
        """
        resultats = [
            FakeResult(
                "Concert de jazz",
                {"title": "Soirée Jazz", "uid": 42, "url": "https://openagenda.com/e/42",
                 "place": "Zénith", "city": "Montpellier",
                 "start_date": "2026-05-01", "end_date": "2026-05-01"}
            )
        ]
        contexte = format_context(resultats)

        self.assertIn("Concert de jazz", contexte)   # texte de l'événement
        self.assertIn("Zénith", contexte)            # lieu
        self.assertIn("Montpellier", contexte)       # ville
        self.assertIn("Soirée Jazz", contexte)       # titre (traçabilité)
        self.assertIn("42", contexte)                # UID (traçabilité)
        self.assertIn("https://openagenda.com/e/42", contexte)  # URL source

    def test_plusieurs_resultats(self):
        """Avec plusieurs résultats, tous doivent apparaître dans le contexte."""
        resultats = [
            FakeResult("Evenement A", {"title": "A", "uid": 1, "url": "",
                                       "place": "Lieu A", "city": "Montpellier",
                                       "start_date": "2026-01-01", "end_date": "2026-01-01"}),
            FakeResult("Evenement B", {"title": "B", "uid": 2, "url": "",
                                       "place": "Lieu B", "city": "Montpellier",
                                       "start_date": "2026-02-01", "end_date": "2026-02-01"}),
        ]
        contexte = format_context(resultats)

        self.assertIn("Evenement A", contexte)
        self.assertIn("Evenement B", contexte)

    def test_champs_metadata_absents(self):
        """Des métadonnées absentes ne doivent pas provoquer d'erreur."""
        resultats = [FakeResult("Texte seul", {})]
        # Ne doit pas lever d'exception malgré l'absence de toutes les clés.
        contexte = format_context(resultats)
        self.assertIn("Texte seul", contexte)


class TestFilterByThreshold(unittest.TestCase):
    """Vérifie le filtrage par seuil de similarité et la stratégie de refus.

    Rappel : avec la distance L2 de FAISS, un score BAS = forte proximité. Un
    résultat est conservé si son score est inférieur ou égal au seuil.
    """

    def _resultat(self, texte):
        """Fabrique un FakeResult minimal pour les tests de seuil."""
        return FakeResult(texte, {"title": texte, "uid": 0, "url": ""})

    def test_conserve_les_scores_sous_le_seuil(self):
        """Un résultat dont le score est sous le seuil doit être conservé."""
        couples = [(self._resultat("pertinent"), SIMILARITY_THRESHOLD - 0.1)]
        retenus = filter_by_threshold(couples)
        self.assertEqual(len(retenus), 1)

    def test_ecarte_les_scores_au_dessus_du_seuil(self):
        """Un résultat dont le score dépasse le seuil doit être écarté."""
        couples = [(self._resultat("hors-sujet"), SIMILARITY_THRESHOLD + 0.5)]
        retenus = filter_by_threshold(couples)
        self.assertEqual(retenus, [])

    def test_refus_quand_tout_depasse_le_seuil(self):
        """Si aucun résultat n'est pertinent, la liste retournée doit être vide.

        C'est le cas qui déclenche le refus explicite dans answer_question :
        le système ne doit pas forcer une réponse sur des documents hors-sujet.
        """
        couples = [
            (self._resultat("a"), SIMILARITY_THRESHOLD + 1.0),
            (self._resultat("b"), SIMILARITY_THRESHOLD + 2.0),
        ]
        retenus = filter_by_threshold(couples)
        self.assertEqual(retenus, [])

    def test_filtrage_mixte(self):
        """Seuls les résultats sous le seuil doivent être conservés, dans l'ordre."""
        couples = [
            (self._resultat("garde1"), SIMILARITY_THRESHOLD - 0.2),
            (self._resultat("jette"), SIMILARITY_THRESHOLD + 0.3),
            (self._resultat("garde2"), SIMILARITY_THRESHOLD - 0.05),
        ]
        retenus = filter_by_threshold(couples)
        textes = [r.page_content for r in retenus]
        self.assertEqual(textes, ["garde1", "garde2"])


class TestFormatSources(unittest.TestCase):
    """Vérifie la construction de la liste des sources par format_sources."""

    def test_sources_titre_et_url(self):
        """Chaque source doit afficher le titre et l'URL de l'événement."""
        resultats = [
            FakeResult("txt", {"title": "Expo Photo", "url": "https://openagenda.com/e/7"})
        ]
        sources = format_sources(resultats)
        self.assertIn("Expo Photo", sources)
        self.assertIn("https://openagenda.com/e/7", sources)

    def test_champs_manquants_geres(self):
        """Un titre ou une URL absent doit être remplacé par une mention lisible."""
        resultats = [FakeResult("txt", {})]
        sources = format_sources(resultats)
        self.assertIn("(sans titre)", sources)
        self.assertIn("(URL non disponible)", sources)


if __name__ == "__main__":
    unittest.main()
