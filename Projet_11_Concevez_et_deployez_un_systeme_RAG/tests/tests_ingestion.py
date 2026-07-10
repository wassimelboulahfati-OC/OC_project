import os
import sys
import unittest

# Permet d'importer les fonctions depuis src/ingestion
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "ingestion"))
from openagenda_ingest import is_valid, extract_event_details   # <-- si ta fonction s'appelle encore est_valide, adapte ici


class TestIsValid(unittest.TestCase):

    def test_document_complet(self):
        """Un document complet doit être valide."""
        document = {
            "text": "Un événement",
            "metadata": {"city": "Montpellier", "start_date": "2026-04-18"}
        }
        self.assertTrue(is_valid(document))

    def test_city_vide(self):
        """Un document avec une ville vide doit être rejeté."""
        document = {
            "text": "Un événement",
            "metadata": {"city": "", "start_date": "2026-04-18"}
        }
        self.assertFalse(is_valid(document))   # <-- quelle assertion ? (True/False)

    def test_text_vide(self):
        """Un document avec un texte vide doit être rejeté."""
        document = {
            "text": "",
            "metadata": {"city": "Montpellier", "start_date": "2026-04-18"}
        }
        self.assertFalse(is_valid(document))

    def test_sans_metadata(self):
        """Un document sans clé metadata ne doit pas planter et doit être rejeté."""
        document = {"text": "Un événement"}
        self.assertFalse(is_valid(document))

class TestExtractEventDetails(unittest.TestCase):

    def test_evenement_complet(self):
        """Un événement complet doit être extrait correctement."""
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

        # Le titre doit apparaître dans le texte
        self.assertIn("Concert", result["text"])
        # Vérifier quelques métadonnées
        self.assertEqual(result["metadata"]["uid"], 123)
        self.assertEqual(result["metadata"]["city"], "Montpellier")
        self.assertEqual(result["metadata"]["place"], "Zénith")

    def test_evenement_champs_manquants(self):
        """Un événement sans title/description/location ne doit pas planter."""
        evenement = {"uid": 999}   # presque tout manque
        result = extract_event_details(evenement)

        # Ne doit pas lever d'erreur, et renvoyer des valeurs vides
        self.assertEqual(result["metadata"]["city"], "")
        self.assertEqual(result["metadata"]["place"], "")
        self.assertEqual(result["metadata"]["uid"], 999)
        
if __name__ == "__main__":
    unittest.main()
