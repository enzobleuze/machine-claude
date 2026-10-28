#!/usr/bin/env python3
"""Tests du Cockpit sur un faux vault temporaire. Lancer : python test_cockpit.py"""
import datetime as dt
import json
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cockpit_build as cb  # noqa: E402
import cockpit_serveur as cs  # noqa: E402

TODAY = dt.date(2027, 1, 7)  # un jeudi

PLAN = """---
title: "Plan unique"
type: strategie
cap:
  libelle: "10 000 € par mois"
  mensuel: 10000
  echeance: 2029-12-31
jalons:
  - {echeance: 2027-06-30, mensuel: 3000}
trimestre:
  nom: "T1 2027"
  fin: 2027-03-31
  objectifs:
    - {titre: "Ventes signées", cible: 6, actuel: 1, unite: "ventes"}
    - {titre: "Appels tenus", cible: 20, actuel: null, unite: "appels"}  # pas encore compté
mois:
  cible: 2000
semaine:
  debut: 2027-01-04
  chose: "Finir la page de vente"
---

# Plan unique

## Semaine du 04/01 au 10/01
- [x] Lundi 04/01, toi 20 min : relire l'offre
- [ ] Mardi 05/01, toi 15 min : valider la page
- [ ] Claude : écrire les relances

## Feuille de route
### Étape 1 : vendre (fin visée le 31/01)
- [x] Écrire l'offre
- [ ] **PROCHAINE** Page de vente : écrire le premier jet
"""

FICHE = """---
title: "{nom}"
type: {type}
statut: {statut}
attend_reponse: {attend}
prochain_pas: "Lui envoyer le lien"
---
# {nom}
"""


def faux_vault():
    v = Path(tempfile.mkdtemp(prefix="cockpit-test-"))
    (v / "wiki/strategie").mkdir(parents=True)
    (v / "wiki/strategie/plan.md").write_text(PLAN, encoding="utf-8")
    (v / "wiki/clients").mkdir(parents=True)
    for nom, typ, statut, attend in [("Alex Test", "client", "actif", "2027-01-02"), ("Sam Essai", "lead", "prospect", "2027-01-07"),
                                     ("Kim Ancien", "client", "ancien", "null")]:
        (v / "wiki/clients" / (nom.lower().replace(" ", "-") + ".md")).write_text(FICHE.format(nom=nom, type=typ, statut=statut, attend=attend), encoding="utf-8")
    (v / "wiki/clients/_index.md").write_text("# index\n", encoding="utf-8")
    (v / "wiki/clients/cassee.md").write_text("---\ntype client\n---\n", encoding="utf-8")
    return v


class TestBuild(unittest.TestCase):
    def setUp(self):
        self.v = faux_vault()

    def tearDown(self):
        shutil.rmtree(self.v, ignore_errors=True)

    def test_controles_integres(self):
        cb.check()

    def test_etat_complet(self):
        s = cb.build_state(self.v, TODAY)
        self.assertEqual(s["prochaine"], "Page de vente : écrire le premier jet")
        self.assertEqual([p["nom"] for p in s["attente"]], ["Alex Test", "Sam Essai"])  # le plus ancien d'abord
        self.assertEqual(s["attente"][0]["joursAttente"], 5)
        self.assertIsNone(s["argent"]["encaisse"])  # aucune vente notée : inconnu, jamais 0
        self.assertEqual(s["argent"]["cible"], 2000)
        self.assertEqual(s["semaine"]["titre"], "Semaine du 04/01 au 10/01")
        self.assertEqual(len(s["semaine"]["cases"]), 3)
        self.assertEqual(s["trimestre"]["objectifs"][1]["actuel"], None)
        self.assertEqual(s["clients"], {"actifs": 1, "leads": 1, "total": 3})
        a = " | ".join(s["alertes"])
        self.assertIn("Alex Test attend ta réponse depuis 5 jours", a)
        self.assertIn("05/01", a)                     # case datée passée
        self.assertIn("Appels tenus", a)               # objectif sans chiffre actuel
        self.assertIn("cassee.md", a)                  # fiche cassée signalée, pas de plantage
        self.assertTrue(s["situation"].startswith("Prochaine tâche : Page de vente"))

    def test_ventes_du_mois(self):
        cb.add_sale(self.v, "1 500", "Alex Test", TODAY)
        cb.add_sale(self.v, "500,5", "Sam Essai", TODAY)
        cb.add_sale(self.v, "900", "Ancien mois", dt.date(2026, 12, 20))
        s = cb.build_state(self.v, TODAY)
        self.assertEqual(s["argent"]["encaisse"], 2000.5)
        self.assertEqual(s["argent"]["ventes"], 2)
        with self.assertRaises(ValueError):
            cb.add_sale(self.v, "-3", "x", TODAY)

    def test_plan_absent_et_semaine_perimee(self):
        (self.v / "wiki/strategie/plan.md").unlink()
        s = cb.build_state(self.v, TODAY)
        self.assertIsNone(s["prochaine"])
        self.assertTrue(any("Plan absent" in x for x in s["alertes"]))
        (self.v / "wiki/strategie/plan.md").write_text(PLAN, encoding="utf-8")
        s = cb.build_state(self.v, dt.date(2027, 1, 12))
        self.assertTrue(any("plan du lundi" in x for x in s["alertes"]))

    def test_cli_ecrit_state(self):
        self.assertEqual(cb.main(["--vault", str(self.v)]), 0)
        state = json.loads((self.v / cb.STATE_REL).read_text(encoding="utf-8"))
        self.assertIn("situation", state)
        self.assertEqual(list((self.v / "outputs/cockpit").glob("*.tmp")), [])  # aucun fichier temporaire oublié

    def test_modele_de_plan_du_repo_se_lit(self):
        modele = HERE.parents[1] / "plan-unique/outils/plan.modele.md"
        if modele.exists():
            fm = cb.parse_frontmatter(modele.read_text(encoding="utf-8"))
            self.assertIn("trimestre", fm)
            self.assertIn("semaine", fm)


class TestServeur(unittest.TestCase):
    def test_page_et_state(self):
        v = faux_vault()
        try:
            srv = cs.http.server.ThreadingHTTPServer(("127.0.0.1", 0), cs.make_handler(str(v)))
            t = threading.Thread(target=srv.serve_forever, daemon=True)
            t.start()
            base = "http://127.0.0.1:{}".format(srv.server_address[1])
            html = urllib.request.urlopen(base + "/").read().decode("utf-8")
            self.assertIn("Attend ta réponse", html)
            state = json.loads(urllib.request.urlopen(base + "/state.json").read())
            self.assertIn("attente", state)
            r = urllib.request.urlopen(urllib.request.Request(base + "/api/rebuild", method="POST"))
            self.assertEqual(r.status, 200)
            with self.assertRaises(urllib.error.HTTPError):
                urllib.request.urlopen(base + "/../wiki/clients/alex-test.md")
            srv.shutdown()
            srv.server_close()
        finally:
            shutil.rmtree(v, ignore_errors=True)


if __name__ == "__main__":
    unittest.main(verbosity=1)
