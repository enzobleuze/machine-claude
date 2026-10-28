#!/usr/bin/env python3
"""depot-scan.py : la partie mécanique du tri d'un dossier « Dépôt » (Google Drive ou autre).

Claude décide OÙ va chaque fichier (il lit son contenu). Ce script fait le reste, sans risque :
  scan     : liste les fichiers du Dépôt avec un nom propre proposé (AAAA-MM-JJ_mots-en-tirets.ext)
  deplacer : déplace UN fichier vers sa destination, ne remplace jamais un fichier existant
             (ajoute -2, -3...), écrit une ligne dans le journal CSV. Ne supprime jamais rien.

Usage :
    python depot-scan.py scan [--depot <dossier>] [--garder dossier1,dossier2]
    python depot-scan.py deplacer <fichier> <dossier destination> [--nom <nouveau-nom.ext>] [--confiance 90]
    python depot-scan.py --test
Sans --depot, cherche le Dépôt dans Google Drive pour ordinateur (Windows et Mac).
Journal : <vault>/outputs/ingest-drive/journal.csv
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import json
import os
import re
import shutil
import sys
import unicodedata
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
NOM_DEPOT = "_Depot"
A_CLARIFIER = "_a-clarifier"


def racines_drive() -> list[Path]:
    c = []
    if os.name == "nt":
        for lettre in "GHIJKLMNOPQRSTUVWXYZ":
            for sous in ("My Drive", "Mon Drive"):
                c.append(Path(f"{lettre}:/{sous}"))
    c += list((Path.home() / "Library" / "CloudStorage").glob("GoogleDrive-*/My Drive"))
    c += list((Path.home() / "Library" / "CloudStorage").glob("GoogleDrive-*/Mon Drive"))
    return [p for p in c if p.is_dir()]


def trouver_depot() -> Path | None:
    for r in racines_drive():
        if (r / NOM_DEPOT).is_dir():
            return r / NOM_DEPOT
    return None


def slug(texte: str) -> str:
    t = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    t = re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()
    return re.sub(r"-{2,}", "-", t)[:70] or "fichier"


def nom_propre(p: Path, date: str | None = None) -> str:
    base = p.stem
    m = re.match(r"^(\d{4}-\d{2}-\d{2})[_ -]?(.*)$", base)
    if m:
        date, base = date or m.group(1), m.group(2) or base
    date = date or dt.date.fromtimestamp(p.stat().st_mtime).isoformat()
    return f"{date}_{slug(base)}{p.suffix.lower()}"


def scan(depot: Path, garder: set[str]) -> list[dict]:
    out = []
    for p in sorted(depot.rglob("*")):
        rel = p.relative_to(depot)
        if not p.is_file() or rel.parts[0] in garder | {A_CLARIFIER} or p.name in {"desktop.ini", ".DS_Store"}:
            continue
        out.append({"fichier": str(p), "ko": round(p.stat().st_size / 1024, 1), "propose": nom_propre(p)})
    return out


def cible_libre(dossier: Path, nom: str) -> Path:
    c = dossier / nom
    n = 2
    while c.exists():
        c = dossier / f"{Path(nom).stem}-{n}{Path(nom).suffix}"
        n += 1
    return c


def deplacer(src: Path, dossier: Path, nom: str | None, confiance: int, journal: Path) -> Path:
    if not src.is_file():
        raise FileNotFoundError(src)
    dossier.mkdir(parents=True, exist_ok=True)
    dst = cible_libre(dossier, nom or src.name)
    shutil.move(str(src), str(dst))
    journal.parent.mkdir(parents=True, exist_ok=True)
    neuf = not journal.exists()
    with journal.open("a", newline="", encoding="utf-8") as h:
        w = csv.writer(h)
        if neuf:
            w.writerow(["date", "source", "destination", "confiance"])
        w.writerow([dt.datetime.now().isoformat(timespec="seconds"), str(src), str(dst), confiance])
    return dst


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        dep = r / NOM_DEPOT
        (dep / A_CLARIFIER).mkdir(parents=True)
        (dep / "Relevé Mars (copie).PDF").write_bytes(b"x")
        (dep / A_CLARIFIER / "doute.txt").write_text("?", encoding="utf-8")
        s = scan(dep, set())
        assert len(s) == 1 and s[0]["propose"].endswith("_releve-mars-copie.pdf"), s
        (r / "Dest").mkdir()
        (r / "Dest" / "a.pdf").write_bytes(b"ancien")
        dst = deplacer(dep / "Relevé Mars (copie).PDF", r / "Dest", "a.pdf", 90, r / "j.csv")
        assert dst.name == "a-2.pdf" and (r / "Dest" / "a.pdf").read_bytes() == b"ancien"
        assert "a-2.pdf" in (r / "j.csv").read_text(encoding="utf-8")
        assert nom_propre(dst, "2024-03-31") == "2024-03-31_a-2.pdf"
    print("auto-test OK")
    return 0


def main() -> int:
    if "--test" in sys.argv:
        return auto_test()
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    s = sp.add_parser("scan")
    s.add_argument("--depot", type=Path)
    s.add_argument("--garder", default="", help="sous-dossiers permanents à ne jamais trier")
    m = sp.add_parser("deplacer")
    m.add_argument("fichier", type=Path)
    m.add_argument("destination", type=Path)
    m.add_argument("--nom")
    m.add_argument("--confiance", type=int, default=0)
    a = ap.parse_args()
    if a.cmd == "scan":
        depot = a.depot or trouver_depot()
        if not depot or not depot.is_dir():
            print("Dépôt introuvable. Crée le dossier _Depot dans ton Drive ou passe --depot.", file=sys.stderr)
            return 2
        garder = {x.strip() for x in a.garder.split(",") if x.strip()}
        print(json.dumps({"depot": str(depot), "fichiers": scan(depot, garder)}, ensure_ascii=False, indent=1))
        return 0
    dst = deplacer(a.fichier, a.destination, a.nom, a.confiance, VAULT / "outputs" / "ingest-drive" / "journal.csv")
    print(f"Déplacé : {dst}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
