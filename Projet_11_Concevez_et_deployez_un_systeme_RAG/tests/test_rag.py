import os
import sys
import unittest

# Permet d'importer les fonctions depuis src/rag
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "src", "rag"))
from build_rag import format_context


class FakeResult:
    """Faux résultat imitant un objet renvoyé par FAISS (page_content + metadata)."""
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


class TestFormatContext(unittest.TestCase):

    def test_formatage_simple(self):
        """Le contexte formaté doit contenir le texte et les métadonnées."""
        resultats = [
            FakeResult(
                "Concert de jazz",
                {"place": "Zénith", "city": "Montpellier",
                 "start_date": "2026-05-01", "end_date": "2026-05-01"}
            )
        ]
        contexte = format_context(resultats)

        # Le texte de l'événement doit apparaître
        self.assertIn("Concert de jazz", contexte)
        # Le lieu doit apparaître
        self.assertIn("Zénith", contexte)
        # La ville doit apparaître
        self.assertIn("Montpellier", contexte)

    def test_plusieurs_resultats(self):
        """Avec plusieurs résultats, ils doivent tous apparaître, séparés."""
        resultats = [
            FakeResult("Evenement A", {"place": "Lieu A", "city": "Montpellier",
                                       "start_date": "2026-01-01", "end_date": "2026-01-01"}),
            FakeResult("Evenement B", {"place": "Lieu B", "city": "Montpellier",
                                       "start_date": "2026-02-01", "end_date": "2026-02-01"}),
        ]
        contexte = format_context(resultats)

        self.assertIn("Evenement A", contexte)
        self.assertIn("Evenement B", contexte)


if __name__ == "__main__":
    unittest.main()
