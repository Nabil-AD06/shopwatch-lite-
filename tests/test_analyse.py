import unittest

from src.analyse import compter_incidents, est_repete
from src.contrat import Signal


def sig(categorie="JOURNAL", gravite="MAJEUR", texte="timeout passerelle apres 30s",
        service="paiement", date="2026-11-27T17:00:00Z"):
    return Signal("SH-0001", date, "PAIEMENT", service,
                  "production", categorie, gravite, texte)


class TestAnalyse(unittest.TestCase):

    def test_repete(self):
        vus = set()
        self.assertFalse(est_repete(sig(), vus))
        self.assertTrue(est_repete(sig(), vus))

    def test_non_repete_secondes_differentes(self):
        vus = set()
        self.assertFalse(est_repete(sig(date="2026-11-27T17:02:11Z"), vus))
        self.assertFalse(est_repete(sig(date="2026-11-27T17:02:12Z"), vus))

    def test_compter_incidents(self):
        compteur = {}
        self.assertEqual(compter_incidents(sig(), compteur), 1)
        self.assertEqual(compter_incidents(sig(gravite="BLOQUANT"), compteur), 2)
        self.assertEqual(compteur, {"paiement": 2})

    def test_compter_incidents_ignore(self):
        compteur = {}
        self.assertEqual(compter_incidents(sig(gravite="MINEUR"), compteur), 0)
        self.assertEqual(compter_incidents(sig(categorie="FAILLE"), compteur), 0)
        self.assertEqual(compteur, {})


if __name__ == "__main__":
    unittest.main()