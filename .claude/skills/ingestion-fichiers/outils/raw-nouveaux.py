#!/usr/bin/env python3
"""raw-nouveaux.py : liste ce qui attend d'être ingéré dans raw/.

Un fichier est « déjà ingéré » s'il figure dans outputs/ingest/deja-ingere.txt.
Le script ne touche jamais raw/ : il lit seulement.

Usage (le script vit dans scripts/) :
    python scripts/raw-nouveaux.py                    liste les nouveaux fichiers (chemin, taille, date)
    python scripts/raw-nouveaux.py --json
    python scripts/raw-nouveaux.py --marquer raw/a.pdf raw/b.md   à lancer APRÈS l'ingestion réussie
    python scripts/raw-nouveaux.py --test
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

IGNORES = {"LISEZMOI.md", ".DS_Store", "desktop.ini", "Thumbs.db"}


def etat(root: Path) -> Path:
    return root / "outputs" / "ingest" / "deja-ingere.txt"


def nouveaux(root: Path) -> list[dict]:
    vus = set(etat(root).read_text(encoding="utf-8").splitlines()) if etat(root).exists() else set()
    out = []
    for p in sorted((root / "raw").rglob("*")):
        if not p.is_file() or p.name in IGNORES or p.name.startswith(("_", ".")):
            continue
        rel = p.relative_to(root).as_posix()
        if rel in vus:
            continue
        s = p.stat()
        out.append({"chemin": rel, "ko": round(s.st_size / 1024, 1),
                    "modifie": dt.datetime.fromtimestamp(s.st_mtime).strftime("%Y-%m-%d"),
                    "type": p.suffix.lower() or "?"})
    return out


def marquer(root: Path, chemins: list[str]) -> None:
    f = etat(root)
    f.parent.mkdir(parents=True, exist_ok=True)
    deja = set(f.read_text(encoding="utf-8").splitlines()) if f.exists() else set()
    with f.open("a", encoding="utf-8") as h:
        for c in chemins:
            c = Path(c).as_posix()
            if c not in deja:
                h.write(c + "\n")


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "raw" / "sous").mkdir(parents=True)
        (r / "raw" / "a.md").write_text("a", encoding="utf-8")
        (r / "raw" / "sous" / "b.pdf").write_bytes(b"%PDF")
        (r / "raw" / "_etat.json").write_text("{}", encoding="utf-8")
        assert [x["chemin"] for x in nouveaux(r)] == ["raw/a.md", "raw/sous/b.pdf"]
        marquer(r, ["raw/a.md"])
        assert [x["chemin"] for x in nouveaux(r)] == ["raw/sous/b.pdf"]
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--marquer", nargs="+")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not (a.vault / "raw").is_dir():
        print(f"raw/ introuvable sous {a.vault}", file=sys.stderr)
        return 2
    if a.marquer:
        marquer(a.vault, a.marquer)
        print(f"{len(a.marquer)} fichier(s) marqué(s) comme ingéré(s).")
        return 0
    n = nouveaux(a.vault)
    if a.json:
        print(json.dumps(n, ensure_ascii=False, indent=1))
    else:
        print(f"{len(n)} fichier(s) à ingérer")
        for x in n:
            print(f"  {x['modifie']}  {x['ko']:>8} Ko  {x['chemin']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
