import unittest

from src.analyse import chercher_fiches, compter_incidents, est_repete, evaluer
from src.contrat import FICHES, Signal


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

    def test_chercher_fiches(self):
        conseils = chercher_fiches(sig(), FICHES)
        self.assertEqual(conseils, [FICHES["timeout"]])

    def test_chercher_fiches_casse_ignoree(self):
        conseils = chercher_fiches(sig(texte="TIMEOUT sur la passerelle"), FICHES)
        self.assertEqual(conseils, [FICHES["timeout"]])

    def test_chercher_fiches_ordre_de_la_base(self):
        conseils = chercher_fiches(sig(texte="faille puis build puis timeout"), FICHES)
        self.assertEqual(conseils, [FICHES["timeout"], FICHES["build"], FICHES["faille"]])

    def test_chercher_fiches_aucune(self):
        self.assertEqual(chercher_fiches(sig(texte="service demarre"), FICHES), [])
    
    def test_evaluer_panne_en_boucle(self):
        s = sig()
        self.assertEqual(evaluer(s, 4), "BLOQUANT")
        self.assertEqual(evaluer(s, 3), "MAJEUR")

    def test_evaluer_gravite_du_signal(self):
        self.assertEqual(evaluer(sig(gravite="MODERE")), "MODERE")
        self.assertEqual(evaluer(sig(gravite="MINEUR"), 0), "MINEUR")

    def test_evaluer_seuil_depasse(self):
        self.assertEqual(evaluer(sig(gravite="MINEUR"), 10), "BLOQUANT")
if __name__ == "__main__":
    unittest.main()