#!/usr/bin/env python3
"""memoire-check.py : vérifie que la mémoire en fichiers reste lisible par Claude.

Claude Code charge MEMORY.md au début de chaque conversation et le tronque au-delà d'une
certaine taille. Ce script contrôle, en lecture seule :
  - MEMORY.md : nombre de lignes, poids, longueur de chaque ligne
  - chaque lien (fichier.md) de l'index pointe vers un fichier qui existe
  - chaque fichier mémoire est indexé (sinon Claude ne le verra jamais)
  - chaque fichier a un frontmatter name, description, type

Usage :
    python memoire-check.py                      dossier mémoire du projet courant (déduit)
    python memoire-check.py --dir <dossier>      dossier mémoire explicite
    python memoire-check.py --max-lignes 45 --max-octets 24000
    python memoire-check.py --test
Sort 0 si tout est bon, 1 sinon. Aucune dépendance.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

TYPES = {"user", "feedback", "project", "reference"}


def dossier_defaut(projet: Path) -> Path:
    # Claude Code range la mémoire sous ~/.claude/projects/<chemin du projet, caractères spéciaux en tirets>/memory
    slug = re.sub(r"[^A-Za-z0-9]", "-", str(projet.resolve()))
    return Path.home() / ".claude" / "projects" / slug / "memory"


def controler(d: Path, max_lignes: int, max_octets: int, max_car: int = 200) -> list[str]:
    pb = []
    idx = d / "MEMORY.md"
    if not idx.exists():
        return [f"MEMORY.md absent dans {d}"]
    brut = idx.read_bytes()
    lignes = brut.decode("utf-8", errors="replace").splitlines()
    if len(lignes) > max_lignes:
        pb.append(f"MEMORY.md fait {len(lignes)} lignes (max {max_lignes}) : archive les entrées closes.")
    if len(brut) > max_octets:
        pb.append(f"MEMORY.md pèse {len(brut)} octets (max {max_octets}) : risque de troncature.")
    for n, l in enumerate(lignes, 1):
        if len(l) > max_car:
            pb.append(f"ligne {n} trop longue ({len(l)} car.) : une ligne = un crochet, le détail va dans le fichier.")
    lies = set()
    for cible in re.findall(r"\]\(([^)]+\.md)\)", "\n".join(lignes)):
        lies.add(Path(cible).name)
        if not (d / cible).exists():
            pb.append(f"lien mort dans MEMORY.md : {cible}")
    for f in sorted(d.glob("*.md")):
        if f.name == "MEMORY.md":
            continue
        if f.name not in lies:
            pb.append(f"fichier non indexé (invisible pour Claude) : {f.name}")
        t = f.read_text(encoding="utf-8", errors="ignore")
        m = re.match(r"\A---\r?\n(.*?)\r?\n---", t, re.S)
        bloc = m.group(1) if m else ""
        for cle in ("name", "description"):
            if not re.search(rf"^{cle}\s*:", bloc, re.M):
                pb.append(f"{f.name} : frontmatter sans « {cle} »")
        typ = re.search(r"^\s*type\s*:\s*(\w+)", bloc, re.M)
        if not typ or typ.group(1) not in TYPES:
            pb.append(f"{f.name} : type absent ou inconnu (attendu : {', '.join(sorted(TYPES))})")
    return pb


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        d = Path(t)
        (d / "MEMORY.md").write_text("- [Ok](feedback_a.md) : court\n- [Mort](absent.md)\n", encoding="utf-8")
        (d / "feedback_a.md").write_text("---\nname: a\ndescription: b\ntype: feedback\n---\nx\n", encoding="utf-8")
        (d / "orphelin.md").write_text("pas de frontmatter\n", encoding="utf-8")
        pb = controler(d, 45, 24000)
        assert any("absent.md" in p for p in pb) and any("orphelin.md" in p and "indexé" in p for p in pb), pb
        assert not any("feedback_a.md" in p for p in pb), pb
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", type=Path)
    ap.add_argument("--max-lignes", type=int, default=45)
    ap.add_argument("--max-octets", type=int, default=24000)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    d = a.dir or dossier_defaut(Path.cwd())
    pb = controler(d, a.max_lignes, a.max_octets)
    print(f"Mémoire : {d}")
    print("OK : mémoire saine." if not pb else "\n".join("- " + p for p in pb))
    return 1 if pb else 0


if __name__ == "__main__":
    sys.exit(main())
