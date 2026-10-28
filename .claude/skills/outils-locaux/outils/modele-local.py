#!/usr/bin/env python3
"""Appelle un modèle installé sur l'ordinateur (Ollama) pour une tâche mécanique, avec repli.

  python scripts/modele-local.py "Classe ce message : vente, question ou autre. Réponds par un mot." --modele qwen3:8b
  echo "texte long" | python scripts/modele-local.py "Résume en 3 lignes :" --modele gemma3:12b
  python scripts/modele-local.py --dispo        (sort 0 si Ollama répond, 3 sinon)
  python scripts/modele-local.py --test

Codes de sortie : 0 réponse écrite sur stdout ; 3 modèle local indisponible (le script appelant
repasse alors sur Claude) ; 1 autre erreur. Aucune dépendance. Ne parle qu'à 127.0.0.1.
Ne sert JAMAIS pour un texte dans la voix de la personne ni pour une citation exacte.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request

HOTE = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/")


def local_seulement(url):
    # shortcut: on refuse tout hôte qui n'est pas la machine, pour ne jamais envoyer de données dehors par erreur
    return url.startswith(("http://127.0.0.1", "http://localhost", "http://[::1]"))


def disponible(delai=2):
    try:
        with urllib.request.urlopen(HOTE + "/api/tags", timeout=delai) as r:
            return r.status == 200
    except (urllib.error.URLError, OSError, ValueError):
        return False


def corps(modele, consigne, contexte=None, json_sortie=False):
    c = {"model": modele, "prompt": consigne, "stream": False,
         # Ollama coupe à un petit contexte par défaut, sans prévenir : on le fixe.
         "options": {"num_ctx": int(os.environ.get("MODELE_LOCAL_CONTEXTE", "32768")), "temperature": 0.2}}
    if contexte:
        c["prompt"] = consigne + "\n\n" + contexte
    if json_sortie:
        c["format"] = "json"
    if modele.endswith(":cloud"):
        raise ValueError("modèle « :cloud » refusé : il envoie les données hors de l'ordinateur")
    return c


def appeler(modele, consigne, contexte=None, json_sortie=False, delai=300):
    donnees = json.dumps(corps(modele, consigne, contexte, json_sortie)).encode("utf-8")
    req = urllib.request.Request(HOTE + "/api/generate", data=donnees, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=delai) as r:
        rep = json.loads(r.read().decode("utf-8"))
    tronque = rep.get("prompt_eval_count", 0) >= corps(modele, "")["options"]["num_ctx"]
    return rep.get("response", "").strip(), tronque


def auto_test():
    c = corps("m", "Q", "C", True)
    assert c["prompt"] == "Q\n\nC" and c["format"] == "json" and c["options"]["num_ctx"] >= 4096
    try:
        corps("x:cloud", "q")
        raise AssertionError("le :cloud aurait dû être refusé")
    except ValueError:
        pass
    assert local_seulement("http://127.0.0.1:11434") and not local_seulement("https://exemple.com")
    print("ok")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("consigne", nargs="?")
    ap.add_argument("--modele", default=os.environ.get("MODELE_LOCAL", "qwen3:8b"))
    ap.add_argument("--json", action="store_true", help="demande une sortie JSON")
    ap.add_argument("--dispo", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
        sys.exit(0)
    if not local_seulement(HOTE):
        sys.exit(f"Refusé : OLLAMA_HOST={HOTE} n'est pas cette machine.")
    if a.dispo:
        sys.exit(0 if disponible() else 3)
    if not a.consigne:
        ap.error("consigne manquante")
    if not disponible():
        print("Modèle local indisponible (Ollama ne répond pas) : repasse sur Claude.", file=sys.stderr)
        sys.exit(3)
    contexte = None if sys.stdin.isatty() else sys.stdin.read()
    try:
        texte, tronque = appeler(a.modele, a.consigne, contexte, a.json)
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"Échec du modèle local : {e}", file=sys.stderr)
        sys.exit(3)
    if tronque:
        print("ATTENTION : le texte a peut-être été coupé (contexte plein). Augmente MODELE_LOCAL_CONTEXTE.", file=sys.stderr)
    print(texte)
