#!/usr/bin/env python3
"""lint_wiki.py : bilan de santé du wiki, en lecture seule.

Contrôles : liens morts, pages orphelines, pages maigres, frontmatter incomplet,
pages avec moins de 3 liens, pages absentes de index.md.

Usage (depuis la racine du vault, le script vit dans scripts/) :
    python scripts/lint_wiki.py            rapport lisible
    python scripts/lint_wiki.py --json     sortie JSON (pour le jardinier ou un autre script)
    python scripts/lint_wiki.py --strict   sort 1 s'il reste des liens morts
    python scripts/lint_wiki.py --test     auto-test sur un mini vault temporaire

N'écrit jamais rien. Python 3.9+, aucune dépendance.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

CLES_FM = ("title", "type", "created", "updated", "tags", "sources")
IGNORES = (".obsidian", ".git", ".trash", "node_modules", "__pycache__")
NAVIGATION = {"index", "log", "_index"}
LIEN = re.compile(r"!?\[\[([^\]\n]+?)\]\]")
SEUIL_LIENS = 3
SEUIL_LIGNES = 20


def fichiers(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file() and not any(i in p.parts for i in IGNORES)]


def parse_fm(texte: str) -> tuple[dict, str]:
    """Frontmatter YAML simple (clés de premier niveau). Retourne (dict, corps)."""
    m = re.match(r"\A﻿?---\r?\n(.*?)\r?\n---\r?\n?", texte, flags=re.S)
    if not m:
        return {}, texte
    fm = {}
    for ligne in m.group(1).splitlines():
        k = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", ligne)
        if k:
            fm[k.group(1)] = k.group(2).strip()
    return fm, texte[m.end():]


def sans_code(texte: str) -> str:
    texte = re.sub(r"```.*?```", "", texte, flags=re.S)
    return re.sub(r"`[^`\n]*`", "", texte)


def cibles(texte: str) -> list[str]:
    out = []
    for brut in LIEN.findall(sans_code(texte)):
        c = brut.split("|")[0].split("#")[0].strip().replace("\\", "/")
        if c:
            out.append(c)
    return out


class Vault:
    def __init__(self, root: Path):
        self.root = root
        self.wiki = root / "wiki"
        tous = fichiers(root)
        self.par_nom: dict[str, list[Path]] = {}
        self.par_chemin: dict[str, Path] = {}
        for p in tous:
            rel = p.relative_to(root).as_posix().lower()
            self.par_chemin[rel] = p
            if p.suffix == ".md":
                self.par_chemin[rel[:-3]] = p
                self.par_nom.setdefault(p.stem.lower(), []).append(p)
            self.par_nom.setdefault(p.name.lower(), []).append(p)
        self.pages = sorted(p for p in tous if p.suffix == ".md" and self.wiki in p.parents)

    def resoudre(self, cible: str) -> Path | None:
        c = cible.lower().strip("/")
        if c in self.par_chemin:
            return self.par_chemin[c]
        if "wiki/" + c in self.par_chemin:
            return self.par_chemin["wiki/" + c]
        nom = c.split("/")[-1]
        trouves = self.par_nom.get(nom) or self.par_nom.get(nom.removesuffix(".md"))
        return trouves[0] if trouves else None


def bilan(root: Path) -> dict:
    v = Vault(root)
    entrants: dict[Path, int] = {p: 0 for p in v.pages}
    morts, peu_liens, maigres, fm_incomplet = [], [], [], []
    index_txt = (root / "index.md").read_text(encoding="utf-8", errors="ignore") if (root / "index.md").exists() else ""
    dans_index = {v.resoudre(c) for c in cibles(index_txt)}

    sources = list(v.pages) + [p for p in (root / "index.md", root / "log.md") if p.exists()]
    for p in sources:
        texte = p.read_text(encoding="utf-8", errors="ignore")
        rel = p.relative_to(root).as_posix()
        fm, corps = parse_fm(texte)
        utiles = 0
        for c in cibles(texte):
            cible = v.resoudre(c)
            if cible is None:
                morts.append({"page": rel, "lien": c})
                continue
            if cible != p and cible in entrants:
                entrants[cible] += 1
            if cible != p and cible.stem.lower() not in NAVIGATION:
                utiles += 1
        if p not in v.pages or "archive" in p.parts or p.stem.lower() in NAVIGATION:
            continue
        manque = [k for k in CLES_FM if k not in fm]
        if manque:
            fm_incomplet.append({"page": rel, "manque": manque})
        if utiles < SEUIL_LIENS:
            peu_liens.append({"page": rel, "liens": utiles})
        lignes = [l for l in corps.splitlines() if l.strip()]
        if len(lignes) < SEUIL_LIGNES:
            maigres.append({"page": rel, "lignes": len(lignes)})

    orphelines = [p.relative_to(root).as_posix() for p, n in entrants.items()
                  if n == 0 and p.stem.lower() not in NAVIGATION and "archive" not in p.parts]
    hors_index = [p.relative_to(root).as_posix() for p in v.pages
                  if p not in dans_index and p.stem.lower() not in NAVIGATION and "archive" not in p.parts]
    return {
        "pages": len(v.pages),
        "liens_morts": morts,
        "orphelines": orphelines,
        "maigres": maigres,
        "frontmatter_incomplet": fm_incomplet,
        "moins_de_3_liens": peu_liens,
        "hors_index": hors_index,
    }


def afficher(b: dict) -> None:
    print(f"## Bilan du wiki : {b['pages']} pages\n")
    print(f"### Critique\n- Liens morts : {len(b['liens_morts'])}")
    for x in b["liens_morts"][:30]:
        print(f"  - {x['page']} -> [[{x['lien']}]]")
    print(f"\n### À corriger bientôt\n- Orphelines (aucun lien entrant) : {len(b['orphelines'])}")
    for x in b["orphelines"][:30]:
        print(f"  - {x}")
    print(f"- Frontmatter incomplet : {len(b['frontmatter_incomplet'])}")
    for x in b["frontmatter_incomplet"][:30]:
        print(f"  - {x['page']} (manque : {', '.join(x['manque'])})")
    print(f"- Moins de {SEUIL_LIENS} liens : {len(b['moins_de_3_liens'])}")
    for x in b["moins_de_3_liens"][:30]:
        print(f"  - {x['page']} ({x['liens']})")
    print(f"\n### Info\n- Pages maigres (< {SEUIL_LIGNES} lignes) : {len(b['maigres'])}")
    print(f"- Absentes de index.md : {len(b['hors_index'])}")
    for x in b["hors_index"][:30]:
        print(f"  - {x}")


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "wiki" / "maps").mkdir(parents=True)
        fm = "---\ntitle: x\ntype: map\ncreated: 2026-01-01\nupdated: 2026-01-01\ntags: []\nsources: []\n---\n"
        (r / "wiki" / "maps" / "a.md").write_text(fm + "[[b]] [[c]] [[fantome]] [[b|alias]]\n", encoding="utf-8")
        (r / "wiki" / "b.md").write_text("# b\n[[a]]\n", encoding="utf-8")
        (r / "wiki" / "c.md").write_text(fm + "`[[pas-un-lien]]`\n", encoding="utf-8")
        (r / "index.md").write_text("[[a]]\n", encoding="utf-8")
        b = bilan(r)
        assert [x["lien"] for x in b["liens_morts"]] == ["fantome"], b["liens_morts"]
        assert b["orphelines"] == [], b["orphelines"]
        assert {x["page"] for x in b["frontmatter_incomplet"]} == {"wiki/b.md"}
        assert set(b["hors_index"]) == {"wiki/b.md", "wiki/c.md"}
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Bilan de santé du wiki (lecture seule).")
    ap.add_argument("--vault", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not (a.vault / "wiki").is_dir():
        print(f"Dossier wiki/ introuvable sous {a.vault}. Passe --vault <racine du vault>.", file=sys.stderr)
        return 2
    b = bilan(a.vault)
    print(json.dumps(b, ensure_ascii=False, indent=1)) if a.json else afficher(b)
    return 1 if a.strict and b["liens_morts"] else 0


if __name__ == "__main__":
    sys.exit(main())
