#!/usr/bin/env python3
"""Tests du Cockpit sur un faux vault temporaire (cockpit_demo.py). Aucun réseau : Linear est simulé, l'agenda est un fichier local.
Lancer : python -X utf8 test_cockpit.py      (tout doit finir par OK)
"""
import datetime as dt
import json
import re
import shutil
import sys
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cockpit_build as cb  # noqa: E402
import cockpit_demo  # noqa: E402
import cockpit_serveur as cs  # noqa: E402
import cockpit_sources as src  # noqa: E402

TODAY = dt.date(2027, 1, 7)  # un jeudi


class FauxLinear:
    """Répond comme l'API Linear, sans réseau. Garde la trace des demandes."""

    def __init__(self, refuse=False):
        self.demandes, self.refuse = [], refuse

    def __call__(self, q, v):
        self.demandes.append((q, v))
        if self.refuse:
            raise urllib.error.HTTPError("https://api.linear.app/graphql", 401, "refus", {}, None)
        if "issues(" in q:
            return {"data": {"issues": {"nodes": [
                {"identifier": "ABC-1", "title": "Écrire la page", "url": "https://linear.app/x/issue/ABC-1", "dueDate": "2027-01-05",
                 "startedAt": "2027-01-02T10:00:00Z", "state": {"type": "started"}},
                {"identifier": "ABC-2", "title": "Relancer", "url": None, "dueDate": "2027-01-20", "startedAt": None, "state": {"type": "unstarted"}}]}}}
        if "issue(id" in q:
            return {"data": {"issue": {"id": "id-1", "team": {"states": {"nodes": [{"id": "s-fait", "type": "completed"}, {"id": "s-annule", "type": "canceled"}]}}}}}
        if "issueUpdate" in q:
            return {"data": {"issueUpdate": {"success": True}}}
        if "teams(" in q:
            return {"data": {"teams": {"nodes": [{"id": "equipe-1"}]}}}
        if "issueCreate" in q:
            return {"data": {"issueCreate": {"success": True, "issue": {"identifier": "ABC-3"}}}}
        return {"errors": [{"message": "inconnu"}]}


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="cockpit-test-")
        self.v, self.s = cockpit_demo.faux_vault(self.tmp, TODAY)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def etat(self, **kw):
        return cb.build_state(self.v, TODAY, secrets=self.s, **kw)

    def pers(self, st, pid):
        return next(p for p in st["personnes"] if p["id"] == pid)


class TestMoteur(Base):
    def test_controles_integres(self):
        cb.check()

    def test_etat_complet(self):
        s = self.etat()
        self.assertEqual(s["prochaine"], "Page de vente : écrire le premier jet")
        self.assertEqual(s["etape"], {"titre": "Étape 1 : vendre", "faites": 1, "total": 3})
        self.assertEqual([p["nom"] for p in s["attente"]], ["Alex Test", "Sam Essai"])  # le plus ancien d'abord
        self.assertEqual(s["attente"][0]["joursAttente"], 5)
        self.assertEqual(s["argent"]["encaisse"], 450.0)
        self.assertEqual(s["argent"]["cible"], 2000)
        self.assertEqual(s["semaine"]["titre"], "Semaine du 04/01 au 10/01")
        self.assertEqual([c["qui"] for c in s["semaine"]["cases"]], ["toi", "toi", "claude"])
        self.assertTrue(s["semaine"]["cases"][1]["enRetard"])
        self.assertIsNone(s["trimestre"]["objectifs"][1]["actuel"])
        a = " | ".join(s["alertes"])
        for attendu in ("Alex Test attend ta réponse depuis 5 jours", "05/01", "Appels tenus", "cassee.md", "Sauvegarde"):
            self.assertIn(attendu, a)
        self.assertIn("Rapport du matin écrit", [x["titre"] for x in s["alertesDetail"]["info"]])
        self.assertTrue(s["situation"].startswith("Prochaine tâche : Page de vente"))
        self.assertEqual(s["entonnoir"], {"mois": "Janvier", "prospects": 1, "appels": 0, "paiements": 1})
        self.assertFalse(s["charte"]["trouvee"])

    def test_groupes_et_ce_qui_manque(self):
        s = self.etat()
        g = {p["id"]: (p["groupe"], p["archive"]) for p in s["personnes"]}
        self.assertEqual(g, {"alex-test": ("actif", False), "sam-essai": ("prospect", False), "kim-ancien": ("ancien", True),
                             "lou-exemple": ("ancien", False), "noa-demo": ("lead", True)})
        self.assertIn("La fiche dit actif", self.pers(s, "lou-exemple")["constat"])   # « actif » sans échange depuis 3 mois
        alex = self.pers(s, "alex-test")
        self.assertEqual(alex["contrat"], {"valeur": 900, "paye": 450, "reste": 450, "noteAuCockpit": 450.0, "texte": "- Contrat : signé"})
        self.assertEqual(alex["manque"], [])
        self.assertIn("Coordonnées absentes", self.pers(s, "sam-essai")["manque"])
        self.assertEqual(alex["journal"][0]["canal"], "message")

    def test_inconnu_jamais_zero(self):
        (self.v / cb.SALES_REL).unlink()
        s = self.etat()
        self.assertIsNone(s["argent"]["encaisse"])
        self.assertIn("inconnu", s["situation"])

    def test_ventes(self):
        v, doublon = cb.add_sale(self.v, "1 500", "Alex Test", TODAY, offre="Séance privée", rid="r1")
        self.assertEqual((v, doublon), (1500.0, False))
        self.assertTrue(cb.add_sale(self.v, "1 500", "Alex Test", TODAY, rid="r1")[1])   # double envoi : une seule ligne
        cb.add_sale(self.v, "500,5", "Sam Essai", TODAY)
        s = self.etat()
        self.assertEqual(s["argent"]["encaisse"], 2450.5)
        self.assertIn("Séance privée", [a["offre"] for a in self.pers(s, "alex-test")["achats"]])
        for mauvais in ("-3", "abc", "2000000"):
            with self.assertRaises(ValueError):
                cb.add_sale(self.v, mauvais, "x", TODAY)

    def test_plan_absent_et_semaine_perimee(self):
        plan = (self.v / cb.PLAN_REL).read_text(encoding="utf-8")
        (self.v / cb.PLAN_REL).unlink()
        s = self.etat()
        self.assertIsNone(s["prochaine"])
        self.assertTrue(any("Plan absent" in x for x in s["alertes"]))
        (self.v / cb.PLAN_REL).write_text(plan, encoding="utf-8")
        s = cb.build_state(self.v, dt.date(2027, 1, 12), secrets=self.s)
        self.assertTrue(any("plan du lundi" in x for x in s["alertes"]))

    def test_plan_etapes_et_chantiers(self):
        p = self.etat()["plan"]
        self.assertEqual([(e["titre"], e["faites"], e["total"], e["fin"], e["ouverte"]) for e in p["etapes"]],
                         [("Étape 1 : vendre", 1, 3, "2027-01-31", True), ("Étape 2 : remplir l'agenda", 0, 2, "2027-03-08", False)])
        self.assertEqual(p["etapes"][0]["preuve"], "trois ventes notées dans le Cockpit.")
        self.assertEqual([c["titre"] for c in p["chantiers"]], ["Site : nouvelle page d'accueil"])
        self.assertEqual(p["prochainJalon"]["mensuel"], 2500)

    def test_idees(self):
        self.assertEqual(self.etat()["idees"]["total"], 2)
        cb.add_idea(self.v, "  Une   idée\npropre ", TODAY)
        i = self.etat()["idees"]
        self.assertEqual(i["total"], 3)
        self.assertEqual(i["sections"][0]["items"][0], {"date": "2027-01-07", "source": "cockpit", "texte": "Une idée propre"})
        with self.assertRaises(ValueError):
            cb.add_idea(self.v, "x" * 1001)
        (self.v / cb.PARKING_REL).unlink()
        cb.add_idea(self.v, "Première idée", TODAY)   # le parking se crée avec sa section « À trier »
        self.assertEqual(self.etat()["idees"]["sections"][0]["nom"], "À trier")

    def test_echelle(self):
        e = self.etat()["echelle"]
        self.assertEqual([m["id"] for m in e["marches"]], ["guide-gratuit", "atelier-du-mois", "accompagnement-3-mois", "seance-privee"])
        self.assertEqual(e["marches"][1]["prix"], 29.0)
        self.assertEqual(e["comptes"]["atelier-du-mois"], 1)
        self.assertEqual(e["comptes"]["pasEncore"], 1)
        props = {a["id"]: a["nom"] for a in e["aProposer"]}
        self.assertEqual(props["lou-exemple"], "Accompagnement 3 mois")
        self.assertEqual(props["alex-test"], "Séance privée")   # la marche suivante écrite dans le tableau
        cb.atomic_write(self.v / cb.DECISIONS_REL, {"clients": {"lou-exemple": {"refus": [{"offre": "Accompagnement 3 mois", "raison": "pas maintenant"}]}}})
        s = self.etat()
        self.assertIsNone(self.pers(s, "lou-exemple")["echelle"]["suivante"])   # un refus n'est jamais reproposé seul
        self.assertEqual(s["echelle"]["comptes"]["refus"], 1)
        (self.v / "wiki/business/echelle-offres.md").unlink()
        self.assertEqual(self.etat()["echelle"]["etat"], "non-branche")

    def test_taches_fichier(self):
        t = self.etat()["taches"]
        self.assertEqual((t["source"], t["etat"], len(t["enCours"])), ("fichier", "ok", 2))
        self.assertEqual([x["titre"] for x in t["enRetard"]], ["Envoyer la facture de janvier"])
        (self.v / "wiki/maps/taches.md").unlink()
        t = self.etat()["taches"]
        self.assertEqual(t["etat"], "non-branche")
        self.assertIn("linear.env", t["consigne"])

    def test_taches_linear(self):
        (self.s / "linear.env").write_text("LINEAR_API_KEY=cle-de-test\n", encoding="utf-8")
        faux = FauxLinear()
        s = self.etat(envoi_linear=faux)
        self.assertEqual(s["taches"]["source"], "linear")
        self.assertEqual([t["id"] for t in s["taches"]["enCours"]], ["ABC-1"])
        self.assertEqual([t["id"] for t in s["taches"]["enRetard"]], ["ABC-1"])
        self.assertIn("tache:ABC-2", [e["id"] for e in s["agenda"]["elements"]])
        self.etat(envoi_linear=faux)
        self.assertEqual(sum("issues(" in q for q, _ in faux.demandes), 1)   # relu dans le cache, pas sur le réseau
        lin = src.Linear("cle", faux)
        lin.changer_etat("ABC-1", "completed")
        self.assertEqual(faux.demandes[-1][1], {"id": "id-1", "e": {"stateId": "s-fait"}})
        self.assertEqual(lin.creer("Nouvelle", "2027-01-09"), "ABC-3")
        (self.v / cb.OUT_REL / "cache/taches.json").unlink()
        s = self.etat(envoi_linear=FauxLinear(refuse=True))
        self.assertEqual(s["taches"]["etat"], "erreur")
        self.assertIn("refuse la clé", s["taches"]["erreur"])
        self.assertNotIn("cle-de-test", json.dumps(s))   # jamais la clé dans l'état

    def test_ligne_sans_reseau(self):
        (self.s / "linear.env").write_text("LINEAR_API_KEY=cle-de-test\n", encoding="utf-8")
        faux = FauxLinear()
        cb.build_state(self.v, TODAY, secrets=self.s, envoi_linear=faux, reseau=False)
        self.assertEqual(faux.demandes, [])   # la ligne du début de conversation n'attend jamais le réseau

    def test_agenda(self):
        a = self.etat()["agenda"]
        self.assertEqual(a["etat"], "ok")
        ev = [e for e in a["elements"] if e["type"] == "evenement"]
        self.assertEqual([e["debut"] for e in ev if e["titre"] == "Atelier du mardi"][:2], ["2027-01-05T18:00", "2027-01-12T18:00"])
        self.assertTrue(next(e for e in ev if e["titre"] == "Journée sans écran")["journee"])
        types = {e["type"] for e in a["elements"]}
        self.assertTrue({"tache", "evenement", "etape", "jalon"} <= types)
        (self.s / "agenda.env").write_text("AGENDA_ICAL_URL=file:///introuvable/secret-123.ics\n", encoding="utf-8")
        shutil.rmtree(self.v / cb.OUT_REL / "cache")
        a = self.etat()["agenda"]
        self.assertIn("injoignable", a["erreur"])
        self.assertNotIn("secret-123", a["erreur"])   # l'adresse donne accès à tout l'agenda : jamais affichée
        (self.s / "agenda.env").unlink()
        self.assertEqual(self.etat()["agenda"]["etat"], "non-branche")

    def test_reseaux(self):
        r = self.etat()["reseaux"]
        self.assertEqual(r["total"], 1440)
        ig = next(x for x in r["reseaux"] if x["id"] == "instagram")
        self.assertEqual((ig["delta7"], ig["delta30"], ig["etat"]), (80, 180, "ok"))
        self.assertEqual(next(x for x in r["reseaux"] if x["id"] == "youtube")["etat"], "ancien")
        self.assertEqual(r["meilleurs"][0]["titre"], "La matinée calme")
        self.assertEqual(r["meilleurs"][0]["facteur"], 4.2)
        self.assertEqual(r["aRepondre"], 2)
        cb.atomic_write(self.v / cb.OUT_REL / "reseaux/traites.json", {"c1": "2027-01-07T10:00"})
        self.assertEqual(self.etat()["reseaux"]["aRepondre"], 1)
        shutil.rmtree(self.v / cb.OUT_REL / "reseaux")
        r = self.etat()["reseaux"]
        self.assertEqual((r["etat"], r["total"]), ("non-branche", None))   # aucun relevé : inconnu, jamais 0

    def test_tournage_et_appel(self):
        s = self.etat()
        self.assertEqual(s["tournage"]["repartition"], {"prets": 2, "attente": 2, "tournes": 0, "publiees": 0})
        self.assertTrue(next(e for e in s["tournage"]["elements"] if e["slug"] == "premiere-video")["vert"])
        self.assertEqual([p["titre"] for p in s["appel"]["phases"]], ["Accueil", "Situation", "Proposition", "Fin"])
        self.assertTrue(s["appel"]["phases"][0]["blocs"][0]["dit"])
        self.assertFalse(s["appel"]["phases"][0]["blocs"][1]["dit"])
        self.assertIn("secours", s["appel"]["securite"])
        self.assertEqual(len(s["appel"]["objections"]), 2)

    def test_rythme_et_historique(self):
        cb.construire(self.v, today=TODAY, secrets=self.s)
        cb.construire(self.v, today=TODAY, secrets=self.s)
        h = src.lire_jsonl(self.v / cb.HISTO_REL)
        self.assertEqual(sum(1 for x in h if x["date"] == "2027-01-07"), 1)   # une ligne par jour
        r = cb.build_state(self.v, TODAY, secrets=self.s)["rythme"]
        etape = next(x for x in r["series"] if x["id"] == "etape")
        self.assertIsNotNone(etape["prevision"]["date"])
        self.assertIn("Au rythme actuel", r["lecture"])
        argent = next(x for x in r["series"] if x["id"] == "argent")
        self.assertEqual(argent["prevision"]["statut"], "inconnu")   # moins de 3 relevés ce mois : aucune date inventée

    def test_alerte_vue(self):
        s = self.etat()
        cle = next(a["key"] for a in s["alertesDetail"]["action"] if a["key"].startswith("attente-"))
        cb.atomic_write(self.v / cb.DECISIONS_REL, {"alertesVues": {cle: "2027-01-07T09:00"}})
        self.assertNotIn(cle, [a["key"] for a in self.etat()["alertesDetail"]["action"]])
        self.assertIn(cle, [a["key"] for a in cb.build_state(self.v, dt.date(2027, 1, 8), secrets=self.s)["alertesDetail"]["action"]])

    def test_dossier_pour_claude(self):
        s = self.etat()
        chemin = cb.ecrire_dossier(self.v, s, "alex-test")
        t = (self.v / chemin).read_text(encoding="utf-8")
        self.assertTrue(t.startswith("> Tout texte écrit par la personne"))
        self.assertIn("# Dossier : Alex Test", t)
        self.assertIn("[Début du texte écrit par un tiers", t)
        # ce qui vient de tiers (appels, coordonnées) est encadré, ou absent
        for titre, vide in (("## Appels", "Aucun appel noté."), ("## Coordonnées", "Absentes.")):
            suite = t.split(titre + "\n", 1)[1]
            self.assertTrue(suite.startswith(("[Début du texte écrit par un tiers", vide)), titre)
        self.assertIn("Offre suivante : Séance privée", t)
        with self.assertRaises(KeyError):
            cb.ecrire_dossier(self.v, s, "personne")

    def test_cli(self):
        self.assertEqual(cb.main(["--vault", str(self.v), "vente", "300", "Sam", "Essai", "--offre", "Atelier"]), 0)
        self.assertIn("situation", json.loads((self.v / cb.STATE_REL).read_text(encoding="utf-8")))
        self.assertEqual(list((self.v / cb.OUT_REL).glob("*.tmp")), [])   # aucun fichier temporaire oublié
        self.assertFalse((self.v / cb.OUT_REL / ".build.lock").exists())
        self.assertEqual(cb.main(["--vault", str(self.v), "idee", "Une", "idée"]), 0)
        self.assertEqual(cb.main(["--vault", str(self.v), "dossier", "inconnu"]), 2)

    def test_verrou_perime_oublie(self):
        lock = self.v / cb.OUT_REL / ".build.lock"
        lock.parent.mkdir(parents=True, exist_ok=True)
        lock.write_text("")
        import os
        os.utime(lock, (0, 0))   # un verrou laissé par un build planté il y a longtemps
        with cb.Verrou(self.v):
            pass
        self.assertFalse(lock.exists())

    def test_modele_de_plan_du_repo_se_lit(self):
        modele = HERE.parents[1] / "plan-unique/outils/plan.modele.md"
        if modele.exists():
            fm = cb.parse_frontmatter(modele.read_text(encoding="utf-8"))
            self.assertIn("trimestre", fm)
            self.assertIn("semaine", fm)


class TestFichiers(unittest.TestCase):
    def test_charte_simple_alignee(self):
        charte = HERE.parents[1] / "charte-graphique/outils"
        if not (charte / "charte.py").exists():
            self.skipTest("charte.py absent")
        sys.path.insert(0, str(charte))
        import charte as ch
        attendu = ch.css(ch.jetons(ch.PROPOSITIONS["simple"]))
        servi = (HERE / "charte-simple.css").read_text(encoding="utf-8")
        self.assertEqual(attendu.split("\n", 1)[1], servi.split("\n", 1)[1])   # même charte que le preset « simple »

    def test_page_sans_couleur_ecrite_et_sure(self):
        html = (HERE / "index.html").read_text(encoding="utf-8")
        style = re.search(r"<style>(.*?)</style>", html, re.S).group(1)
        self.assertEqual(re.findall(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", style), [])   # toutes les couleurs viennent de charte.css
        for v in ("--fond", "--surface", "--surface-2", "--ligne", "--texte", "--texte-doux", "--accent", "--accent-texte", "--ok", "--alerte",
                  "--erreur", "--police-titres", "--police-texte", "--rayon"):
            self.assertIn("var({})".format(v), html)
        self.assertEqual(len(re.findall(r"\.innerHTML\s*=", html)), 1)   # une seule porte d'entrée pour le HTML, toujours après esc()
        for ecran in ("ecranToday", "ecranClients", "ecranEchelle", "ecranAgenda", "ecranReseaux", "ecranTournage", "ecranPlan", "ecranAppel"):
            self.assertIn("function " + ecran, html)

    def test_aucun_tiret_long(self):
        for f in HERE.iterdir():
            if f.suffix in (".py", ".html", ".css", ".bat", ".command", ".md", ".json"):
                t = f.read_text(encoding="utf-8")
                self.assertFalse(chr(0x2014) in t or chr(0x2013) in t, f.name)


class TestServeur(Base):
    def setUp(self):
        super().setUp()
        shutil.rmtree(self.tmp, ignore_errors=True)   # le serveur calcule sur la vraie date : le faux vault suit aujourd'hui
        self.v, self.s = cockpit_demo.faux_vault(self.tmp, dt.date.today())
        self.faux = FauxLinear()
        self.app = cs.App(self.v, secrets=self.s, envoi_linear=self.faux)
        self.srv = cs.http.server.ThreadingHTTPServer(("127.0.0.1", 0), cs.make_handler(self.app))
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.base = "http://127.0.0.1:{}".format(self.srv.server_address[1])

    def tearDown(self):
        self.srv.shutdown()
        self.srv.server_close()
        super().tearDown()

    def call(self, chemin, corps=None, origin=True, host=None, methode=None, brut=None):
        h = {"Content-Type": "application/json"}
        if origin:
            h["Origin"] = self.base if origin is True else origin
        if host:
            h["Host"] = host
        data = brut if brut is not None else (json.dumps(corps).encode() if corps is not None else None)
        req = urllib.request.Request(self.base + chemin, data=data, headers=h, method=methode or ("POST" if data is not None else "GET"))
        try:
            with urllib.request.urlopen(req) as r:
                b, ct = r.read(), r.headers.get("Content-Type", "")
                return r.status, (json.loads(b) if "json" in ct else b.decode("utf-8") if ct.startswith("text") else b)
        except urllib.error.HTTPError as e:
            b = e.read()
            e.close()
            try:
                return e.code, json.loads(b)
            except ValueError:
                return e.code, b.decode("utf-8", "replace")

    def test_page_etat_charte_logo(self):
        code, html = self.call("/", origin=False)
        self.assertEqual(code, 200)
        self.assertIn("charte.css", html)
        code, st = self.call("/state.json", origin=False)
        self.assertEqual((code, st["demo"]), (200, False))
        self.assertIn("--accent:#2f5bd3", self.call("/charte.css", origin=False)[1])   # charte « simple » tant qu'il n'y en a pas
        m = self.v / "bibliotheque/marque"
        m.mkdir(parents=True)
        (m / "charte.css").write_text(":root{--accent:#123456}", encoding="utf-8")
        (m / "logo.png").write_bytes(b"\x89PNG\r\n\x1a\n")
        cb.atomic_write(m / "charte-jetons.json", {"nom": "Atelier Test", "principal": "sombre", "logo": "bibliotheque/marque/logo.png"})
        self.assertIn("#123456", self.call("/charte.css", origin=False)[1])
        self.assertEqual(self.call("/logo", origin=False)[0], 200)
        cb.atomic_write(m / "charte-jetons.json", {"logo": "../dehors.png"})
        self.assertEqual(self.call("/logo", origin=False)[0], 404)   # jamais un fichier hors du vault

    def test_securite(self):
        self.assertEqual(self.call("/api/rebuild", {}, origin=False)[0], 403)              # écriture sans origine
        self.assertEqual(self.call("/api/rebuild", {}, origin="http://autre.example")[0], 403)
        self.assertEqual(self.call("/state.json", origin=False, host="autre.example")[0], 403)   # DNS rebinding
        self.assertEqual(self.call("/../wiki/clients/alex-test.md", origin=False)[0], 404)
        self.assertEqual(self.call("/api/vente", brut=b"pas du json")[0], 400)
        self.assertEqual(self.call("/api/vente", brut=json.dumps({"x": "a" * 70000}).encode())[0], 413)
        self.assertEqual(self.call("/api/client/inconnu/note", {"texte": "x"})[0], 404)   # seul un identifiant connu reçoit une écriture
        self.assertEqual(self.call("/api/client/alex-test/note", {"texte": ""})[0], 400)

    def test_ventes_idees_decisions(self):
        avant = self.call("/state.json", origin=False)[1]["argent"]["encaisse"] or 0
        code, r = self.call("/api/vente", {"montant": "1 200", "qui": "Alex Test", "rid": "f1"})
        self.assertEqual((code, r["doublon"], r["etat"]["argent"]["encaisse"]), (200, False, avant + 1200))
        self.assertTrue(self.call("/api/vente", {"montant": "1 200", "qui": "Alex Test", "rid": "f1"})[1]["doublon"])
        self.assertEqual(self.call("/api/vente", {"montant": "zéro"})[0], 400)
        self.assertEqual(self.call("/api/idee", {"texte": "Un atelier du samedi"})[1]["etat"]["idees"]["total"], 3)
        r = self.call("/api/client/alex-test/prochaine", {"texte": "Envoyer le bilan", "date": "2027-01-09"})[1]
        self.assertEqual(self.pers(r["etat"], "alex-test")["prochaine"], {"texte": "Envoyer le bilan", "date": "2027-01-09"})
        self.assertEqual(self.call("/api/client/alex-test/prochaine", {"texte": "x", "date": "09/01"})[0], 400)
        r = self.call("/api/client/lou-exemple/archive", {"archive": True})[1]
        self.assertTrue(self.pers(r["etat"], "lou-exemple")["archive"])
        r = self.call("/api/client/lou-exemple/suivi", {"suivi": "actif"})[1]
        self.assertEqual(self.pers(r["etat"], "lou-exemple")["groupe"], "actif")
        r = self.call("/api/client/alex-test/note", {"texte": "A parlé de son\nnouveau travail"})[1]
        self.assertEqual(self.pers(r["etat"], "alex-test")["notes"][0]["texte"], "A parlé de son\nnouveau travail")
        r = self.call("/api/client/alex-test/refus", {"offre": "Séance privée", "raison": "trop tôt"})[1]
        self.assertEqual(self.pers(r["etat"], "alex-test")["refus"][0]["raison"], "trop tôt")
        r = self.call("/api/client/alex-test/dossier", {})[1]
        self.assertTrue((self.v / r["chemin"]).exists())
        (self.v / cb.DECISIONS_REL).write_text("{abîmé", encoding="utf-8")
        self.assertEqual(self.call("/api/client/alex-test/archive", {"archive": False})[0], 200)
        self.assertEqual(len(list((self.v / cb.OUT_REL).glob("decisions.illisible-*.json"))), 1)   # gardé à côté, rien ne se perd

    def test_alertes_agenda_reseaux(self):
        st = self.call("/state.json", origin=False)[1]
        cle = st["alertesDetail"]["action"][0]["key"]
        r = self.call("/api/alerte/{}/vu".format(cle), {})[1]
        self.assertNotIn(cle, [a["key"] for a in r["etat"]["alertesDetail"]["action"]])
        self.assertEqual(self.call("/api/alerte/inconnue/vu", {})[0], 404)
        el = st["agenda"]["elements"][0]["id"]
        r = self.call("/api/agenda/commentaire", {"id": el, "texte": "À faire le matin"})[1]
        self.assertEqual(r["etat"]["agenda"]["commentaires"][el][0]["texte"], "À faire le matin")
        self.assertEqual(self.call("/api/agenda/commentaire", {"id": "inconnu", "texte": "x"})[0], 404)
        r = self.call("/api/reseaux/releve", {"reseau": "TikTok", "abonnes": 75})[1]
        self.assertIn("tiktok", [x["id"] for x in r["etat"]["reseaux"]["reseaux"]])
        self.assertEqual(self.call("/api/reseaux/releve", {"reseau": "tiktok", "abonnes": "beaucoup"})[0], 400)
        self.assertEqual(self.call("/api/reseaux/commentaire/c1/traite", {"traite": True})[1]["etat"]["reseaux"]["aRepondre"], 1)

    def test_taches_linear_et_fichier(self):
        self.assertEqual(self.call("/api/tache/T1/fait", {})[0], 404)   # tâche du fichier : pas modifiable ici
        self.assertEqual(self.call("/api/tache", {"titre": "Essai", "date": "2027-01-09"})[0], 409)
        (self.s / "linear.env").write_text("LINEAR_API_KEY=cle-de-test\n", encoding="utf-8")
        self.app.rebuild()
        self.assertEqual(self.call("/api/tache/ABC-1/fait", {})[0], 200)
        self.assertTrue(any("issueUpdate" in q for q, _ in self.faux.demandes))
        self.assertEqual(self.call("/api/tache/ABC-1/deplacer", {"date": "2027-01-15"})[0], 200)
        self.assertEqual(self.call("/api/tache/ABC-1/retirer", {})[0], 200)
        self.assertEqual(self.call("/api/tache", {"titre": "Préparer l'atelier", "date": "2027-01-09"})[1]["id"], "ABC-3")
        self.assertEqual(self.call("/api/tache/ZZZ-9/fait", {})[0], 404)

    def test_tournage(self):
        self.assertEqual(self.call("/api/tournage/youtube/deuxieme-video/texte", origin=False)[0], 409)   # pas de VERT, pas de prompteur
        code, r = self.call("/api/tournage/youtube/deuxieme-video/texte?voir=1", origin=False)
        self.assertEqual(code, 200)
        self.assertIn("matinées calmes", r["texte"])
        self.assertIn("matinées calmes", self.call("/api/tournage/youtube/premiere-video/texte", origin=False)[1]["texte"])
        r = self.call("/api/tournage/youtube/premiere-video/etat", {"etat": "tournee"})[1]
        self.assertEqual(r["etat"]["tournage"]["repartition"]["tournes"], 1)
        r = self.call("/api/tournage/court/2-le-carnet/etat", {"etat": "tournee"})[1]
        self.assertEqual(r["etat"]["tournage"]["repartition"]["tournes"], 2)
        self.assertEqual(self.call("/api/tournage/court/2-le-carnet/etat", {"etat": "brulee"})[0], 400)
        self.assertEqual(self.call("/api/tournage/court/inconnu/etat", {"etat": "tournee"})[0], 404)

    def test_appel(self):
        r = self.call("/api/appel/essai/fin", {"resultat": "vendu", "montant": "900", "notes": ["a"]})[1]
        self.assertTrue(r["essai"])
        self.assertFalse((self.v / cb.APPELS_REL).exists())   # répétition : rien n'est écrit
        r = self.call("/api/appel/sam-essai/fin", {"resultat": "vendu", "montant": "900", "offre": "Accompagnement 3 mois",
                                                   "notes": ["veut commencer lundi"], "duree": 34, "rid": "a1"})[1]
        self.assertEqual(r["vente"]["montant"], 900.0)
        self.assertEqual(len(list((self.v / cb.APPELS_REL).glob("*/*.json"))), 1)
        self.assertEqual(r["etat"]["entonnoir"]["appels"], 1)
        self.assertEqual(self.call("/api/appel/sam-essai/fin", {"resultat": "peut-être"})[0], 400)


if __name__ == "__main__":
    unittest.main(verbosity=1)
