#!/usr/bin/env python3
"""Serveur d'une app locale : sert index.html et l'état JSON, sur cette machine seulement.

  python scripts/<app>/serveur.py                 ouvre http://127.0.0.1:8787 dans le navigateur
  python scripts/<app>/serveur.py --port 8790 --no-open
  python scripts/<app>/serveur.py --state scripts/<app>/fixture_state.json     (mode démo : fausses données)
  python scripts/<app>/serveur.py --test

Routes : GET / (index.html), GET /api/state (state.json relu à chaque appel),
POST /api/rebuild (relance construire-etat.py, un seul à la fois). Tout le reste : 404.
Écoute sur 127.0.0.1 seulement. Aucune dépendance.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.environ.get("VAULT", os.getcwd())
ETAT = os.path.join(RACINE, "outputs", os.environ.get("APP_NOM", "mon-app"), "state.json")
VERROU = threading.Lock()
DEMO = False


def lire_etat():
    try:
        with open(ETAT, encoding="utf-8") as h:
            return 200, h.read()
    except OSError:
        return 200, json.dumps({"sections": {}, "erreurs": {"etat": "pas encore construit : clique Rafraîchir"}})


def reconstruire():
    if DEMO:
        return 200, json.dumps({"ok": True, "sortie": "mode démo : rien reconstruit"})
    if not VERROU.acquire(blocking=False):
        return 409, json.dumps({"ok": False, "raison": "déjà en cours"})
    try:
        r = subprocess.run([sys.executable, os.path.join(ICI, "construire-etat.py")], cwd=RACINE,
                           capture_output=True, text=True, timeout=240)
        return 200, json.dumps({"ok": r.returncode == 0, "sortie": r.stdout[-500:], "erreur": r.stderr[-500:]})
    except subprocess.TimeoutExpired:
        return 504, json.dumps({"ok": False, "raison": "trop long"})
    finally:
        VERROU.release()


class Gestion(BaseHTTPRequestHandler):
    def envoyer(self, code, corps, type_="application/json; charset=utf-8"):
        b = corps.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", type_)
        self.send_header("Content-Length", str(len(b)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(ICI, "index.html"), encoding="utf-8") as h:
                return self.envoyer(200, h.read(), "text/html; charset=utf-8")
        if self.path == "/api/state":
            return self.envoyer(*lire_etat())
        self.envoyer(404, json.dumps({"erreur": "inconnu"}))

    def do_POST(self):
        if self.path == "/api/rebuild":
            return self.envoyer(*reconstruire())
        self.envoyer(404, json.dumps({"erreur": "inconnu"}))

    def log_message(self, *args):
        pass  # silence dans le terminal


def auto_test():
    import urllib.request
    srv = ThreadingHTTPServer(("127.0.0.1", 0), Gestion)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    base = f"http://127.0.0.1:{srv.server_address[1]}"
    assert "<html" in urllib.request.urlopen(base + "/").read().decode("utf-8").lower()
    assert "sections" in json.loads(urllib.request.urlopen(base + "/api/state").read())
    try:
        urllib.request.urlopen(base + "/../secret")
        raise AssertionError("404 attendu")
    except urllib.error.HTTPError as e:
        assert e.code == 404
    srv.shutdown()
    print("ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=int(os.environ.get("APP_PORT", "8787")))
    ap.add_argument("--no-open", action="store_true")
    ap.add_argument("--test", action="store_true")
    ap.add_argument("--state", help="lire ce fichier d'état (mode démo, le moteur n'est jamais lancé)")
    a = ap.parse_args()
    if a.state:
        ETAT, DEMO = os.path.abspath(a.state), True
    if a.test:
        auto_test()
        sys.exit(0)
    url = f"http://127.0.0.1:{a.port}"
    try:
        srv = ThreadingHTTPServer(("127.0.0.1", a.port), Gestion)
    except OSError:
        print(f"Le port {a.port} est pris : l'app tourne sans doute déjà. J'ouvre {url}.")
        webbrowser.open(url)
        sys.exit(0)
    print(f"App ouverte sur {url} (Ctrl+C pour arrêter)")
    if not a.no_open:
        webbrowser.open(url)
    srv.serve_forever()
