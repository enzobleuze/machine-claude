#!/usr/bin/env python3
"""Cockpit : le petit serveur local. Sert la page, l'état, la charte et le logo sur http://127.0.0.1:PORT, rien d'autre.

Usage : python cockpit_serveur.py [--vault DOSSIER] [--port N] [--no-open] [--demo]
  --demo   ouvre un faux vault aux noms inventés, dans un dossier temporaire : rien ne touche tes vraies données.

Il écoute seulement sur 127.0.0.1 : la page n'est visible que depuis ton ordinateur. Un en-tête Host étranger est
refusé ; une écriture doit venir de la page elle-même (Origin), en JSON, 64 Ko au plus, avec un identifiant que
l'état connaît. Chaque écriture est atomique puis relance le build : ce que tu fais se voit tout de suite.
Le build tourne aussi en tâche de fond toutes les 15 minutes tant que le serveur est lancé.
Aucune écriture ne part vers une personne : ni message, ni publication. Seule exception voulue : tes tâches Linear.
"""
import datetime as dt
import http.server
import json
import mimetypes
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import webbrowser
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cockpit_build as cb  # noqa: E402
import cockpit_sources as src  # noqa: E402

CORPS_MAX = 64 * 1024
RYTHME_S = 15 * 60
PID = r"([a-z0-9][a-z0-9._-]{0,80})"
TACHE = r"([A-Za-z][A-Za-z0-9]{0,9}-\d{1,7})"
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
RESULTATS = ("vendu", "reflechit", "non", "absent")
IMAGES = {".png", ".jpg", ".jpeg", ".webp", ".svg", ".gif"}


class Refus(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def texte(corps, cle, maxi, mini=1, long=False):
    v = str(corps.get(cle) or "").strip() if long else " ".join(str(corps.get(cle) or "").split())
    if not mini <= len(v) <= maxi:
        raise Refus(400, "Le champ « {} » doit faire entre {} et {} signes.".format(cle, mini, maxi))
    return v


def date_ou_vide(corps, cle="date"):
    v = str(corps.get(cle) or "").strip()
    if v and not (DATE.match(v) and cb.as_date(v)):
        raise Refus(400, "Date attendue au format AAAA-MM-JJ.")
    return v or None


def maintenant():
    return dt.datetime.now().strftime("%Y-%m-%dT%H:%M")


class App:
    def __init__(self, vault, secrets=None, envoi_linear=None, demo=False):
        self.vault, self.secrets, self.envoi, self.demo = Path(vault), secrets, envoi_linear, demo
        self.lock = threading.RLock()
        self.erreur = None

    # ----- état -----
    def rebuild(self):
        with self.lock:   # un seul build à la fois côté serveur ; le verrou du moteur protège des tâches planifiées
            try:
                state = cb.construire(self.vault, secrets=self.secrets, envoi_linear=self.envoi)
                self.erreur = None
                return state
            except Exception as e:  # le build ne doit jamais tuer le serveur
                self.erreur = "{} : {}".format(type(e).__name__, e)[:300]
                raise

    def etat(self):
        p = self.vault / cb.STATE_REL
        if not p.exists():
            self.rebuild()
        state = json.loads(p.read_text(encoding="utf-8"))
        state.update(demo=self.demo, erreurBuild=self.erreur)
        return state

    def connu(self, genre, valeur):
        st = self.etat()
        ids = {
            "personne": lambda: {p["id"] for p in st.get("personnes", [])},
            "alerte": lambda: {a["key"] for k in ("action", "info") for a in st.get("alertesDetail", {}).get(k, [])},
            "tache": lambda: {t["id"] for k in ("enCours", "enRetard", "datees") for t in st.get("taches", {}).get(k, []) if t.get("modifiable")},
            "element": lambda: {e["id"] for e in st.get("agenda", {}).get("elements", [])},
            "commentaire": lambda: {c["id"] for c in st.get("reseaux", {}).get("commentaires", [])},
            "tournage": lambda: {"{}/{}".format(e["type"], e["slug"]) for e in st.get("tournage", {}).get("elements", [])},
        }[genre]()
        if valeur not in ids:
            raise Refus(404, "Identifiant inconnu : recharge la page, l'état a peut-être changé.")
        return st

    def decisions(self, fn):
        p = self.vault / cb.DECISIONS_REL
        with self.lock:
            try:
                d = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
            except ValueError:   # un fichier abîmé est gardé à côté avant d'être réécrit : rien ne se perd
                shutil.copy2(p, p.with_name("decisions.illisible-{}.json".format(dt.datetime.now().strftime("%Y%m%d-%H%M%S"))))
                d = {}
            fn(d)
            cb.atomic_write(p, d)

    def client(self, pid, fn):
        self.connu("personne", pid)
        self.decisions(lambda d: fn(d.setdefault("clients", {}).setdefault(pid, {})))

    def linear(self):
        cle = src.lire_secrets(self.secrets or cb.secrets_par_defaut(), "linear").get("LINEAR_API_KEY")
        if self.demo or not cle:
            raise Refus(409, "Tes tâches ne viennent pas de Linear : demande le changement à Claude." if not self.demo
                        else "Mode démo : rien n'est écrit dans Linear.")
        return src.Linear(cle, self.envoi)

    def apres_linear(self):
        try:
            (self.vault / cb.OUT_REL / "cache/taches.json").unlink()
        except OSError:
            pass


# ---------- les écritures (chacune valide ses entrées, puis le build relance) ----------

def w_rebuild(app, corps):
    return {}


def w_vente(app, corps):
    try:
        montant, doublon = cb.add_sale(app.vault, corps.get("montant"), texte(corps, "qui", 120, 0), offre=texte(corps, "offre", 80, 0) or None,
                                       rid=str(corps.get("rid") or "")[:40] or None)
    except ValueError:
        raise Refus(400, "Montant illisible. Écris par exemple 1 500 ou 1500,50.")
    return {"montant": montant, "doublon": doublon}


def w_idee(app, corps):
    try:
        return {"idee": cb.add_idea(app.vault, corps.get("texte"))}
    except ValueError as e:
        raise Refus(400, "Idée refusée : {}.".format(e))


def w_prochaine(app, corps, pid):
    t, d = texte(corps, "texte", 300, 0), date_ou_vide(corps)
    app.client(pid, lambda c: c.update(prochaine={"texte": t, "date": d}) if t else c.pop("prochaine", None))
    return {}


def w_archive(app, corps, pid):
    if not isinstance(corps.get("archive"), bool):
        raise Refus(400, "« archive » doit valoir vrai ou faux.")
    app.client(pid, lambda c: c.update(archive=corps["archive"]))
    return {}


def w_suivi(app, corps, pid):
    s = corps.get("suivi")
    if s not in ("actif", "ancien", None):
        raise Refus(400, "« suivi » vaut actif, ancien ou rien.")
    app.client(pid, lambda c: c.update(suivi=s) if s else c.pop("suivi", None))
    return {}


def w_note(app, corps, pid):
    app.connu("personne", pid)
    t = texte(corps, "texte", 4000, long=True)
    p = app.vault / cb.NOTES_REL
    with app.lock:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:   # ajout seul
            f.write(json.dumps({"date": maintenant(), "id": pid, "texte": t}, ensure_ascii=False) + "\n")
    return {}


def w_refus(app, corps, pid):
    r = {"offre": texte(corps, "offre", 80), "raison": texte(corps, "raison", 300, 0) or None, "date": dt.date.today().isoformat()}
    app.client(pid, lambda c: c.setdefault("refus", []).append(r))
    return {"refus": r}


def w_dossier(app, corps, pid):
    st = app.connu("personne", pid)
    return {"chemin": cb.ecrire_dossier(app.vault, st, pid)}


def w_vu(app, corps, cle):
    app.connu("alerte", cle)
    app.decisions(lambda d: d.setdefault("alertesVues", {}).__setitem__(cle, maintenant()))
    return {}


def w_tache_fait(app, corps, ref):
    app.connu("tache", ref)
    app.linear().changer_etat(ref, "completed")
    app.apres_linear()
    return {}


def w_tache_retirer(app, corps, ref):
    app.connu("tache", ref)
    app.linear().changer_etat(ref, "canceled")
    app.apres_linear()
    return {}


def w_tache_deplacer(app, corps, ref):
    app.connu("tache", ref)
    d = date_ou_vide(corps)
    if not d:
        raise Refus(400, "Choisis la nouvelle date.")
    app.linear().deplacer(ref, d)
    app.apres_linear()
    return {}


def w_tache_creer(app, corps):
    t, d = texte(corps, "titre", 200), date_ou_vide(corps)
    lin = app.linear()
    equipe = cb.lire_reglages(app.vault).get("linearEquipe")
    ident = lin.creer(t, d, equipe)
    app.apres_linear()
    return {"id": ident}


def w_commentaire(app, corps):
    ident = texte(corps, "id", 120)
    app.connu("element", ident)
    t = texte(corps, "texte", 2000, long=True)
    p = app.vault / cb.OUT_REL / "agenda/commentaires.json"
    with app.lock:
        d = src.lire_json(p, {})
        d.setdefault(ident, []).append({"date": maintenant(), "texte": t})
        cb.atomic_write(p, d)
    return {}


def w_releve(app, corps):
    r = src.slug(texte(corps, "reseau", 30))
    n = corps.get("abonnes")
    if not isinstance(n, int) or isinstance(n, bool) or not 0 <= n <= 10 ** 9:
        raise Refus(400, "Le nombre d'abonnés doit être un nombre entier.")
    p = app.vault / cb.OUT_REL / "reseaux/releves.jsonl"
    with app.lock:
        p.parent.mkdir(parents=True, exist_ok=True)
        with open(p, "a", encoding="utf-8") as f:
            f.write(json.dumps({"date": dt.date.today().isoformat(), "reseau": r, "abonnes": n, "source": "manuel"}) + "\n")
    return {}


def w_traite(app, corps, cid):
    traite = corps.get("traite", True) is not False
    if traite:   # remettre un commentaire déjà caché ne demande pas qu'il soit encore dans l'état
        app.connu("commentaire", cid)
    p = app.vault / cb.OUT_REL / "reseaux/traites.json"
    with app.lock:
        d = src.lire_json(p, {})
        if traite:
            d[cid] = maintenant()
        else:
            d.pop(cid, None)
        cb.atomic_write(p, d)
    return {}


def w_tournage(app, corps, type_, slug_):
    app.connu("tournage", "{}/{}".format(type_, slug_))
    etat = corps.get("etat")
    if etat not in src.ETATS_TOURNAGE:
        raise Refus(400, "État attendu : a_tourner, tournee ou publiee.")
    _, _, fichier = src.chemins_tournage(app.vault, type_, slug_)
    valeur = {"etat": etat, "le": dt.date.today().isoformat()}
    with app.lock:
        if type_ == "youtube":
            cb.atomic_write(fichier, valeur)
        else:
            d = src.lire_json(fichier, {})
            d[slug_] = valeur
            cb.atomic_write(fichier, d)
    return {}


def w_appel_fin(app, corps, pid):
    resultat = corps.get("resultat")
    if resultat not in RESULTATS:
        raise Refus(400, "Résultat attendu : vendu, reflechit, non ou absent.")
    notes = corps.get("notes") or []
    if not isinstance(notes, list) or len(notes) > 50:
        raise Refus(400, "Trop de notes.")
    fiche = {"id": pid, "date": dt.date.today().isoformat(), "fin": maintenant(), "resultat": resultat,
             "duree": corps.get("duree") if isinstance(corps.get("duree"), int) else None,
             "phase": texte(corps, "phase", 120, 0) or None, "notes": [" ".join(str(n).split())[:1000] for n in notes]}
    if pid == "essai":
        return {"essai": True}   # répétition : rien n'est écrit
    app.connu("personne", pid)
    d = app.vault / cb.APPELS_REL / fiche["date"][:4]
    cb.atomic_write(d / "{}-{}-{}.json".format(fiche["date"], pid, dt.datetime.now().strftime("%H%M%S")), fiche)
    vente = None
    if resultat == "vendu" and corps.get("montant"):
        vente = w_vente(app, {"montant": corps["montant"], "qui": next((p["nom"] for p in app.etat()["personnes"] if p["id"] == pid), pid),
                              "offre": corps.get("offre"), "rid": corps.get("rid")})
    return {"vente": vente}


POSTS = [
    (r"/api/rebuild", w_rebuild), (r"/api/vente", w_vente), (r"/api/idee", w_idee),
    (r"/api/client/{}/prochaine".format(PID), w_prochaine), (r"/api/client/{}/archive".format(PID), w_archive),
    (r"/api/client/{}/suivi".format(PID), w_suivi), (r"/api/client/{}/note".format(PID), w_note),
    (r"/api/client/{}/refus".format(PID), w_refus), (r"/api/client/{}/dossier".format(PID), w_dossier),
    (r"/api/alerte/([a-z0-9-]{1,90})/vu", w_vu),
    (r"/api/tache", w_tache_creer), (r"/api/tache/{}/fait".format(TACHE), w_tache_fait),
    (r"/api/tache/{}/retirer".format(TACHE), w_tache_retirer), (r"/api/tache/{}/deplacer".format(TACHE), w_tache_deplacer),
    (r"/api/agenda/commentaire", w_commentaire), (r"/api/reseaux/releve", w_releve),
    (r"/api/reseaux/commentaire/([\w.-]{1,120})/traite", w_traite),
    (r"/api/tournage/(youtube|court)/([a-z0-9][a-z0-9._-]{0,100})/etat", w_tournage),
    (r"/api/appel/{}/fin".format(PID), w_appel_fin),
]


def g_texte_tournage(app, query, type_, slug_):
    """Le texte d'un script. Pour le prompteur, il faut le verdict VERT, et la porte du board si elle est installée."""
    app.connu("tournage", "{}/{}".format(type_, slug_))
    script, board, _ = src.chemins_tournage(app.vault, type_, slug_)
    if "voir" not in query:
        e = next(e for e in app.etat()["tournage"]["elements"] if e["type"] == type_ and e["slug"] == slug_)
        if not e["vert"]:
            raise Refus(409, "Le board n'a pas donné VERT à ce texte : passe-le au board avant de le tourner.")
        porte = app.vault / "scripts/porte_board.py"
        if porte.exists():
            r = subprocess.run([sys.executable, str(porte), "verifier", str(script), str(board)], capture_output=True, timeout=30)
            if r.returncode != 0:
                raise Refus(409, "Le texte a changé depuis le verdict du board : relance le board sur les phrases changées.")
    return {"texte": src.sans_frontmatter(script.read_text(encoding="utf-8")).strip()}


GETS = [(r"/api/tournage/(youtube|court)/([a-z0-9][a-z0-9._-]{0,100})/texte", g_texte_tournage)]


def make_handler(app):
    class Handler(http.server.BaseHTTPRequestHandler):
        timeout = 15   # une connexion muette ne garde pas un fil

        def _send(self, code, body, ctype, extra=None):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            self.wfile.write(data)

        def _json(self, code, obj):
            self._send(code, json.dumps(obj, ensure_ascii=False), "application/json; charset=utf-8")

        def _local(self):
            # Anti « DNS rebinding » : seul un Host local est servi ; une écriture doit venir de la page elle-même.
            port = self.server.server_address[1]
            permis = {"127.0.0.1:{}".format(port), "localhost:{}".format(port)}
            if self.headers.get("Host", "") not in permis:
                return False
            origin = self.headers.get("Origin")
            return self.command != "POST" or (origin is not None and origin.split("//", 1)[-1] in permis)

        def do_GET(self):
            if not self._local():
                return self._send(403, "interdit", "text/plain; charset=utf-8")
            url = urlsplit(self.path)
            chemin, query = url.path, parse_qs(url.query)
            try:
                if chemin in ("/", "/index.html"):
                    return self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
                if chemin == "/state.json":
                    return self._json(200, app.etat())
                if chemin == "/charte.css":
                    perso = app.vault / "bibliotheque/marque/charte.css"
                    return self._send(200, (perso if perso.is_file() else HERE / "charte-simple.css").read_bytes(), "text/css; charset=utf-8")
                if chemin == "/logo":
                    logo = (src.lire_json(app.vault / cb.CHARTE_REL, {}) or {}).get("logo") or ""
                    f = (app.vault / logo).resolve() if logo else None
                    if not f or not f.is_file() or f.suffix.lower() not in IMAGES or app.vault.resolve() not in f.parents:
                        return self._send(404, "pas de logo", "text/plain; charset=utf-8")
                    return self._send(200, f.read_bytes(), mimetypes.guess_type(f.name)[0] or "application/octet-stream",
                                      {"Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'"})
                for motif, fn in GETS:
                    m = re.fullmatch(motif, chemin)
                    if m:
                        return self._json(200, fn(app, query, *m.groups()))
                self._send(404, "introuvable", "text/plain; charset=utf-8")
            except Refus as e:
                self._json(e.code, {"erreur": str(e)})
            except Exception as e:
                self._json(500, {"erreur": "Le Cockpit n'a pas pu lire ton vault ({}).".format(type(e).__name__)})

        def do_POST(self):
            if not self._local():
                return self._send(403, "interdit", "text/plain; charset=utf-8")
            chemin = urlsplit(self.path).path
            fn, groupes = next(((f, m.groups()) for motif, f in POSTS for m in [re.fullmatch(motif, chemin)] if m), (None, ()))
            if fn is None:
                return self._send(404, "introuvable", "text/plain; charset=utf-8")
            try:
                n = int(self.headers.get("Content-Length") or 0)
                if n > CORPS_MAX:
                    raise Refus(413, "Envoi trop gros.")
                if n and not (self.headers.get("Content-Type") or "").startswith("application/json"):
                    raise Refus(415, "JSON attendu.")
                try:
                    corps = json.loads(self.rfile.read(n).decode("utf-8")) if n else {}
                except ValueError:
                    raise Refus(400, "JSON illisible.")
                if not isinstance(corps, dict):
                    raise Refus(400, "Un objet JSON est attendu.")
                if not app.vault.joinpath(cb.STATE_REL).exists():
                    app.rebuild()
                reponse = fn(app, corps, *groupes)
                state = app.rebuild()
                state.update(demo=app.demo, erreurBuild=None)
                self._json(200, dict(reponse, ok=True, etat=state))
            except Refus as e:
                self._json(e.code, {"erreur": str(e)})
            except src.SourceErreur as e:
                self._json(502, {"erreur": str(e)})
            except Exception as e:  # le serveur ne meurt jamais d'une écriture ratée
                self._json(500, {"erreur": "Écriture ratée ({}). Rien n'a été perdu : réessaie.".format(type(e).__name__)})

        def log_message(self, *args):
            pass

    return Handler


def port_busy(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def rythme(app, arret):
    while not arret.wait(RYTHME_S):
        try:
            app.rebuild()
        except Exception:
            pass   # l'erreur reste dans app.erreur et la page l'affiche


def main(argv):
    vault = os.environ.get("COCKPIT_VAULT") or os.getcwd()
    port, open_it, demo = None, True, False
    i = 0
    while i < len(argv):
        if argv[i] == "--vault":
            vault, i = argv[i + 1], i + 1
        elif argv[i] == "--port":
            port, i = int(argv[i + 1]), i + 1
        elif argv[i] == "--no-open":
            open_it = False
        elif argv[i] == "--demo":
            demo = True
        i += 1
    secrets = None
    if demo:
        import cockpit_demo
        vault, secrets = cockpit_demo.faux_vault(tempfile.mkdtemp(prefix="cockpit-demo-"))
        print("Mode démo : faux vault dans {}. Rien ne touche tes vraies données.".format(vault))
    port = port or cb.lire_reglages(vault)["port"]
    url = "http://127.0.0.1:{}/".format(port)
    if port_busy(port):  # déjà lancé : on ouvre juste la page
        if open_it:
            webbrowser.open(url)
        print("Cockpit déjà ouvert : " + url)
        return 0
    app = App(vault, secrets=secrets, demo=demo)
    try:
        app.rebuild()
    except Exception as e:
        print("Build en échec ({}). La page affichera l'erreur.".format(e), file=sys.stderr)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), make_handler(app))
    arret = threading.Event()
    threading.Thread(target=rythme, args=(app, arret), daemon=True).start()
    print("Cockpit : " + url + " (Ctrl+C pour arrêter)")
    if open_it:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    arret.set()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
