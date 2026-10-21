import unittest

from src.extraction import (
    masquer_donnees,
    lire_journal,
    lire_scan,
    lire_build,
)


class TestExtraction(unittest.TestCase):

    def test_masquer_donnees(self):
        texte = "Contact user@example.com"
        resultat = masquer_donnees(texte)

        self.assertNotIn("user@example.com", resultat)

    
    def test_masquer_jeton_bearer(self):
        texte = "Authorization: Bearer abc123secret"
        resultat = masquer_donnees(texte)

        self.assertNotIn("abc123secret", resultat)
        self.assertIn("Bearer [MASQUE]", resultat)

    def test_lire_journal(self):
        signal = lire_journal(
            "2026-11-27 paiement ERROR timeout",
            1,
        )

        self.assertEqual(signal.origine, "PAIEMENT")
        self.assertEqual(signal.categorie, "JOURNAL")
        self.assertEqual(signal.gravite, "MAJEUR")

    def test_lire_scan(self):
        signal = lire_scan(
            {"risque": "critique", "id_faille": "CVE-2026-7788"},
            2,
        )

        self.assertEqual(signal.origine, "SCANNER")
        self.assertEqual(signal.categorie, "FAILLE")
        self.assertEqual(signal.gravite, "BLOQUANT")

    def test_lire_build(self):
        signal = lire_build(
            {"etape": "deploiement", "resultat": "echec"},
            3,
        )

        self.assertEqual(signal.origine, "BUILD")
        self.assertEqual(signal.categorie, "BUILD_ECHEC")
        self.assertEqual(signal.gravite, "MAJEUR")


if __name__ == "__main__":
    unittest.main()