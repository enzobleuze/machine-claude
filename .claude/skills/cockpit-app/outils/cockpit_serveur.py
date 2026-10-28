#!/usr/bin/env python3
"""Cockpit : petit serveur local. Sert la page et state.json sur http://127.0.0.1:PORT, rien d'autre.

Usage : python cockpit_serveur.py [--vault DOSSIER] [--port 8787] [--no-open]
Au démarrage et à chaque clic « Rafraîchir », il relance cockpit_build.py.
Il écoute seulement sur 127.0.0.1 : la page n'est visible que depuis ton ordinateur.
"""
import http.server
import json
import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import cockpit_build  # noqa: E402

LOCK = threading.Lock()


def rebuild(vault):
    with LOCK:  # un seul build à la fois
        state = cockpit_build.build_state(vault)
        cockpit_build.atomic_write(Path(vault) / cockpit_build.STATE_REL, state)
        return state


def make_handler(vault):
    class Handler(http.server.BaseHTTPRequestHandler):
        def _send(self, code, body, ctype):
            data = body.encode("utf-8") if isinstance(body, str) else body
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Content-Length", str(len(data)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            if self.path in ("/", "/index.html"):
                self._send(200, (HERE / "index.html").read_bytes(), "text/html; charset=utf-8")
            elif self.path.startswith("/state.json"):
                p = Path(vault) / cockpit_build.STATE_REL
                if not p.exists():
                    rebuild(vault)
                self._send(200, p.read_bytes(), "application/json; charset=utf-8")
            else:
                self._send(404, "introuvable", "text/plain; charset=utf-8")

        def do_POST(self):
            if self.path != "/api/rebuild":
                return self._send(404, "introuvable", "text/plain; charset=utf-8")
            try:
                state = rebuild(vault)
                self._send(200, json.dumps(state, ensure_ascii=False), "application/json; charset=utf-8")
            except Exception as e:  # le build ne doit jamais tuer le serveur
                self._send(500, json.dumps({"erreur": str(e)}, ensure_ascii=False), "application/json; charset=utf-8")

        def log_message(self, *args):
            pass

    return Handler


def port_busy(port):
    with socket.socket() as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def main(argv):
    vault = os.environ.get("COCKPIT_VAULT") or os.getcwd()
    port, open_it = 8787, True
    i = 0
    while i < len(argv):
        if argv[i] == "--vault":
            vault, i = argv[i + 1], i + 1
        elif argv[i] == "--port":
            port, i = int(argv[i + 1]), i + 1
        elif argv[i] == "--no-open":
            open_it = False
        i += 1
    url = "http://127.0.0.1:{}/".format(port)
    if port_busy(port):  # déjà lancé : on ouvre juste la page
        if open_it:
            webbrowser.open(url)
        print("Cockpit déjà ouvert : " + url)
        return 0
    try:
        rebuild(vault)
    except Exception as e:
        print("Build en échec ({}). La page affichera l'erreur.".format(e), file=sys.stderr)
    server = http.server.ThreadingHTTPServer(("127.0.0.1", port), make_handler(vault))
    print("Cockpit : " + url + " (Ctrl+C pour arrêter)")
    if open_it:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
