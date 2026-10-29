"""broll.py : un plan de coupe filmé (B-roll) gratuit et libre de droits, trouvé sur Pexels, avec sa trace de licence.

  python broll.py "woman walking morning street" [--orientation portrait|landscape] [--duree 3] [-o bibliotheque/broll]
  python broll.py --test

Licence Pexels : usage commercial permis, attribution non obligatoire (pexels.com/license). On garde quand même la page,
l'auteur et l'empreinte de chaque fichier dans bibliotheque/broll/registre.json, avec les vidéos où il a servi :
un même plan d'une vidéo à l'autre se remarque, les plans neufs passent donc d'abord.
Clé gratuite (pexels.com/api) : variable PEXELS_API_KEY, ou une ligne PEXELS_API_KEY=... dans ~/.claude/secrets/pexels.env.
La requête s'écrit en anglais : une action précise et un lieu (« man waiting phone kitchen »), jamais un concept.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import urllib.parse
import urllib.request
from pathlib import Path

SECRET = Path.home() / ".claude/secrets/pexels.env"


def cle() -> str | None:
    k = os.environ.get("PEXELS_API_KEY")
    if not k and SECRET.exists():
        for l in SECRET.read_text(encoding="utf-8").splitlines():
            if l.strip().startswith("PEXELS_API_KEY="):
                k = l.split("=", 1)[1].strip().strip('"')
    return k or None


def meilleur_fichier(v: dict, orientation: str) -> dict | None:
    """Le fichier MP4 dans la bonne orientation, au moins 1080 px sur le petit côté (720 à défaut), le plus léger."""
    fs = [f for f in v.get("video_files", []) if f.get("file_type") == "video/mp4" and f.get("width") and f.get("height")]
    bons = [f for f in fs if min(f["width"], f["height"]) >= 1080] or [f for f in fs if min(f["width"], f["height"]) >= 720]
    vertical = orientation == "portrait"
    return min(bons, key=lambda f: ((f["height"] > f["width"]) != vertical, f["width"] * f["height"])) if bons else None


def inscrire(registre: Path, v: dict, fichier: Path, requete: str, usage: str) -> dict:
    reg = json.loads(registre.read_text(encoding="utf-8")) if registre.exists() else {}
    e = reg.setdefault(str(v["id"]), {"page": v.get("url"), "auteur": (v.get("user") or {}).get("name"), "requete": requete,
                                      "licence": "Pexels (usage commercial, attribution facultative)",
                                      "sha256": hashlib.sha256(fichier.read_bytes()).hexdigest(), "fichier": fichier.name,
                                      "usages": []})
    if usage and usage not in e["usages"]:
        e["usages"].append(usage)
    registre.parent.mkdir(parents=True, exist_ok=True)
    registre.write_text(json.dumps(reg, ensure_ascii=False, indent=1), encoding="utf-8")
    return e


def chercher(requete, dossier="bibliotheque/broll", orientation="landscape", duree_min=2.0, usage="", deja=()):
    """Télécharge le meilleur plan neuf. -> chemin du fichier, ou None (pas de clé, rien trouvé, réseau)."""
    k = cle()
    if not k:
        print(f"Pas de clé Pexels : crée {SECRET} avec PEXELS_API_KEY=... (gratuit sur pexels.com/api).")
        return None
    dossier = Path(dossier)
    q = urllib.parse.urlencode({"query": requete, "orientation": orientation, "per_page": 15})
    try:
        req = urllib.request.Request(f"https://api.pexels.com/videos/search?{q}", headers={"Authorization": k, "User-Agent": "kit-video/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            vs = json.loads(r.read()).get("videos", [])
    except OSError as e:
        print(f"Pexels : recherche impossible ({e})")
        return None
    registre = dossier / "registre.json"
    vus = json.loads(registre.read_text(encoding="utf-8")) if registre.exists() else {}
    vs = sorted((v for v in vs if v["id"] not in deja and v.get("duration", 0) >= duree_min), key=lambda v: str(v["id"]) in vus)
    for v in vs:
        f = meilleur_fichier(v, orientation)
        if not f:
            continue
        dossier.mkdir(parents=True, exist_ok=True)
        chemin = dossier / f"pexels-{v['id']}.mp4"
        if not chemin.exists():
            try:
                with urllib.request.urlopen(urllib.request.Request(f["link"], headers={"User-Agent": "kit-video/1.0"}), timeout=120) as r:
                    chemin.with_suffix(".part").write_bytes(r.read())
                chemin.with_suffix(".part").replace(chemin)
            except OSError as e:
                print(f"Pexels : téléchargement raté ({e})")
                continue
        e = inscrire(registre, v, chemin, requete, usage)
        print(f"{chemin} ({e['auteur']}, {e['page']})")
        return chemin
    print("Rien trouvé : reformule (action précise + lieu, en anglais).")
    return None


def auto_test():
    v = {"id": 7, "url": "https://www.pexels.com/video/7/", "user": {"name": "Auteur"}, "duration": 8, "video_files": [
        {"file_type": "video/mp4", "width": 1920, "height": 1080, "link": "h"}, {"file_type": "video/mp4", "width": 1080, "height": 1920, "link": "v"},
        {"file_type": "video/mp4", "width": 3840, "height": 2160, "link": "h4k"}, {"file_type": "video/mp4", "width": 640, "height": 360, "link": "p"}]}
    assert meilleur_fichier(v, "landscape")["link"] == "h" and meilleur_fichier(v, "portrait")["link"] == "v"
    assert meilleur_fichier({"video_files": [{"file_type": "video/mp4", "width": 640, "height": 360}]}, "landscape") is None
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "pexels-7.mp4"
        f.write_bytes(b"video")
        reg = Path(tmp) / "registre.json"
        inscrire(reg, v, f, "man walking", "video-a")
        e = inscrire(reg, v, f, "man walking", "video-b")
        assert e["usages"] == ["video-a", "video-b"] and e["auteur"] == "Auteur" and len(e["sha256"]) == 64
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Plan de coupe libre (Pexels) avec trace de licence.")
    ap.add_argument("requete", nargs="?")
    ap.add_argument("--orientation", choices=("portrait", "landscape"), default="landscape")
    ap.add_argument("--duree", type=float, default=2.0)
    ap.add_argument("--usage", default="", help="la vidéo où le plan sert (pour le registre)")
    ap.add_argument("-o", "--dossier", default="bibliotheque/broll")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.requete:
        sys.exit(0 if chercher(a.requete, a.dossier, a.orientation, a.duree, a.usage) else 1)
    else:
        ap.print_help()
