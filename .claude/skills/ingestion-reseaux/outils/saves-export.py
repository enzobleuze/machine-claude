#!/usr/bin/env python3
"""saves-export.py : transforme un export officiel de réseau social en liste de saves à trier.

Instagram : Paramètres > Espace Comptes > Vos informations > Télécharger vos informations,
format JSON. Le fichier utile s'appelle saved_posts.json (dossier « saved »). Les autres
réseaux (TikTok, X, LinkedIn) donnent aussi du JSON : le script cherche partout des liens
et des dates, sans dépendre de la structure exacte, qui change souvent.

Sortie : raw/reseaux/saves-AAAA-MM-JJ.md, une ligne par save NOUVEAU (dédoublonné par
lien grâce à raw/reseaux/_vus.txt). Rien n'est téléchargé, aucun compte n'est touché.

Usage :
    python scripts/saves-export.py <fichier.json ou dossier de l'export> [--reseau instagram]
    python scripts/saves-export.py --test
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
LIEN = re.compile(r"^https?://\S+$")


def extraire(noeud, auteur: str = "") -> list[dict]:
    """Parcourt le JSON : chaque objet qui porte un lien donne un save (lien, date, auteur)."""
    out = []
    if isinstance(noeud, dict):
        auteur = noeud.get("title") if isinstance(noeud.get("title"), str) else auteur
        lien = next((v for k, v in noeud.items() if k in ("href", "uri", "url", "link") and isinstance(v, str) and LIEN.match(v)), None)
        if lien:
            ts = noeud.get("timestamp") or noeud.get("creation_timestamp")
            date = dt.datetime.fromtimestamp(ts).date().isoformat() if isinstance(ts, (int, float)) and ts > 0 else ""
            out.append({"lien": lien, "date": date, "auteur": auteur or ""})
        for v in noeud.values():
            if isinstance(v, (dict, list)):
                out += extraire(v, auteur)
    elif isinstance(noeud, list):
        for v in noeud:
            out += extraire(v, auteur)
    return out


def fichiers_json(cible: Path) -> list[Path]:
    if cible.is_file():
        return [cible]
    tous = sorted(cible.rglob("*.json"))
    saves = [p for p in tous if "saved" in p.name.lower() or "favorite" in p.name.lower() or "bookmark" in p.name.lower()]
    return saves or tous


def lancer(cible: Path, reseau: str, racine: Path) -> Path | None:
    dossier = racine / "raw" / "reseaux"
    dossier.mkdir(parents=True, exist_ok=True)
    vus_f = dossier / "_vus.txt"
    vus = set(vus_f.read_text(encoding="utf-8").splitlines()) if vus_f.exists() else set()
    neufs, deja = [], set()
    for f in fichiers_json(cible):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        for s in extraire(data):
            if s["lien"] not in vus and s["lien"] not in deja:
                deja.add(s["lien"])
                neufs.append(s)
    if not neufs:
        print("Aucun save nouveau.")
        return None
    jour = dt.date.today().isoformat()
    sortie = dossier / f"saves-{reseau}-{jour}.md"
    lignes = [f"# Saves {reseau} du {jour}", "", f"{len(neufs)} saves nouveaux. À trier par /ingest (playbooks, pas une page par save).", "",
              "| date | auteur | lien |", "|:-|:-|:-|"]
    lignes += [f"| {s['date']} | {s['auteur']} | {s['lien']} |" for s in sorted(neufs, key=lambda x: x["date"], reverse=True)]
    sortie.write_text("\n".join(lignes) + "\n", encoding="utf-8")
    with vus_f.open("a", encoding="utf-8") as h:
        h.writelines(s["lien"] + "\n" for s in neufs)
    print(f"{len(neufs)} saves nouveaux -> {sortie}")
    return sortie


def auto_test() -> int:
    import tempfile
    exemple = {"saved_saved_media": [
        {"title": "un_compte", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/reel/AAA/", "timestamp": 1700000000}}},
        {"title": "autre", "string_map_data": {"Saved on": {"href": "https://www.instagram.com/p/BBB/", "timestamp": 1710000000}}}]}
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        f = r / "saved_posts.json"
        f.write_text(json.dumps(exemple), encoding="utf-8")
        s = extraire(exemple)
        assert [x["auteur"] for x in s] == ["un_compte", "autre"] and s[0]["date"], s
        assert lancer(f, "instagram", r) is not None
        assert lancer(f, "instagram", r) is None, "le deuxième passage doit tout reconnaître"
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cible", nargs="?", type=Path)
    ap.add_argument("--reseau", default="instagram")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not a.cible or not a.cible.exists():
        ap.error("donne le fichier JSON ou le dossier de l'export")
    lancer(a.cible, a.reseau, VAULT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
