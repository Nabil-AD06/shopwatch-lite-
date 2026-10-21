import unittest

from src.analyse import (chercher_fiches, compter_incidents, diagnostiquer,
                         est_repete, evaluer)
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
        
    def test_diagnostiquer_cause_connue(self):
        d = diagnostiquer(sig(), FICHES)
        self.assertEqual(d.cause, FICHES["timeout"])
        self.assertEqual(d.niveau, "MAJEUR")
        self.assertEqual(d.action, "Observer")
        self.assertFalse(d.critique)
        self.assertEqual(d.origines, ["PAIEMENT"])
        self.assertEqual(d.signal_ref, "SH-0001")

    def test_diagnostiquer_cause_inconnue(self):
        d = diagnostiquer(sig(texte="service demarre", gravite="MINEUR"), FICHES)
        self.assertEqual(d.cause, "Cause inconnue : verification manuelle")

    def test_diagnostiquer_causes_multiples(self):
        d = diagnostiquer(sig(texte="timeout pendant le build"), FICHES)
        self.assertEqual(d.cause, FICHES["timeout"] + " ; " + FICHES["build"])

    def test_diagnostiquer_isoler_et_critique(self):
        d = diagnostiquer(sig(), FICHES, 4)
        self.assertEqual(d.niveau, "BLOQUANT")
        self.assertEqual(d.action, "Isoler le service paiement")
        self.assertTrue(d.critique)

    def test_diagnostiquer_faille(self):
        s = sig(categorie="FAILLE", gravite="BLOQUANT", service="lib-panier",
                texte="Faille CVE-2026-7788 dans lib-panier")
        d = diagnostiquer(s, FICHES)
        self.assertEqual(d.action, "Corriger la dependance lib-panier")
        self.assertFalse(d.critique)

    def test_diagnostiquer_build_echec(self):
        s = sig(categorie="BUILD_ECHEC", gravite="MAJEUR", service="deploiement",
                texte="Build deploiement : echec")
        d = diagnostiquer(s, FICHES)
        self.assertEqual(d.action, "Rejouer le build deploiement")
        self.assertFalse(d.critique)

    def test_diagnostiquer_etat_evalue(self):
        s = sig()
        self.assertEqual(s.etat, "RECU")
        diagnostiquer(s, FICHES)
        self.assertEqual(s.etat, "EVALUE")    
if __name__ == "__main__":
    unittest.main()