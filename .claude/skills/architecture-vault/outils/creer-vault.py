#!/usr/bin/env python3
"""creer-vault.py : pose le squelette du vault sans jamais écraser un fichier existant.

Usage :
    python creer-vault.py <racine du vault> [--dossiers clients,principes,sources,...] [--essai]
    python creer-vault.py --test

Crée : raw/ (dépôt immuable), wiki/<dossiers>/ avec un _index.md chacun, wiki/maps/,
outputs/, logs/, index.md, log.md, .gitignore. Un fichier déjà présent est laissé tel quel
(il est listé « gardé »). --essai affiche le plan sans rien écrire. Aucune dépendance.
"""
from __future__ import annotations

import argparse
import datetime as dt
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DOSSIERS_DEFAUT = ["principes", "clients", "sources", "contenu", "strategie", "maps"]
GITIGNORE = """# Secrets : jamais dans le vault (ils vivent dans ~/.claude/secrets/)
*.env
*.key
*.pem
secrets/
credentials*.json
# Bruit des outils
.obsidian/workspace*.json
.obsidian/cache/
.trash/
__pycache__/
node_modules/
.venv/
# Caches et gros fichiers régénérables
outputs/cerveau-cache.npz
*.mp4
*.mov
"""


def fm(titre: str, typ: str, jour: str, liens: str) -> str:
    return (f'---\ntitle: "{titre}"\ntype: {typ}\ncreated: {jour}\nupdated: {jour}\n'
            f'tags: [{typ}]\nsources: []\n---\n# {titre}\n\n{liens}\n')


def plan(root: Path, dossiers: list[str]) -> dict[Path, str]:
    j = dt.date.today().isoformat()
    out: dict[Path, str] = {
        root / "raw" / "LISEZMOI.md": "# raw/\n\nDépose ici tout ce qui entre (PDF, notes, exports, transcriptions).\n"
                                      "Claude le lit et ne le modifie jamais. Ensuite dis « ingère ».\n",
        root / "outputs" / ".garder": "",
        root / "logs" / ".garder": "",
        root / ".gitignore": GITIGNORE,
        root / "index.md": "# Index\n\nCatalogue des pages du wiki. Point d'entrée de Claude avant toute recherche.\n\n"
                           "## Cartes\n\n- [[parcours]] : où on en est\n- [[routage]] : ce que je dis, ce que Claude lance\n",
        root / "log.md": f"# Journal\n\nUne entrée par session, la plus récente en bas. Format : `## [AAAA-MM-JJ] type | quoi`.\n\n"
                         f"## [{j}] installation | squelette du vault posé\n",
    }
    for d in dossiers:
        autres = " ".join(f"[[wiki/{x}/_index|{x}]]" for x in dossiers if x != d)
        out[root / "wiki" / d / "_index.md"] = fm(d.capitalize(), "map", j, f"Pages de {d}. Voisins : {autres}. Retour : [[index]].")
    return out


def creer(root: Path, dossiers: list[str], essai: bool) -> tuple[list[Path], list[Path]]:
    crees, gardes = [], []
    for p, contenu in plan(root, dossiers).items():
        if p.exists():
            gardes.append(p)
            continue
        crees.append(p)
        if not essai:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(contenu, encoding="utf-8")
    return crees, gardes


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "index.md").write_text("MON INDEX", encoding="utf-8")
        crees, gardes = creer(r, DOSSIERS_DEFAUT, essai=False)
        assert (r / "index.md").read_text(encoding="utf-8") == "MON INDEX"
        assert r / "index.md" in gardes and (r / "wiki" / "clients" / "_index.md").exists()
        crees2, _ = creer(r, DOSSIERS_DEFAUT, essai=False)
        assert crees2 == [], "deuxième passage doit être vide"
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("racine", nargs="?", type=Path)
    ap.add_argument("--dossiers", default=",".join(DOSSIERS_DEFAUT))
    ap.add_argument("--essai", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not a.racine:
        ap.error("donne la racine du vault")
    dossiers = [x.strip() for x in a.dossiers.split(",") if x.strip()]
    if "maps" not in dossiers:
        dossiers.append("maps")
    crees, gardes = creer(a.racine.resolve(), dossiers, a.essai)
    print(("Plan (rien écrit) :" if a.essai else "Créés :"), len(crees))
    for p in crees:
        print("  +", p.relative_to(a.racine.resolve()).as_posix())
    for p in gardes:
        print("  = gardé :", p.relative_to(a.racine.resolve()).as_posix())
    return 0


if __name__ == "__main__":
    sys.exit(main())
