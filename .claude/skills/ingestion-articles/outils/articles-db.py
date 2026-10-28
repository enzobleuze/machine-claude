#!/usr/bin/env python3
"""articles-db.py : tient la base des articles d'auteurs clippés (Obsidian Web Clipper ou copie).

Chaque article clippé est un .md dans raw/articles/<auteur>/ avec au moins « source: <url> »
ou « url: <url> » dans son frontmatter (le Web Clipper le remplit seul). Le script :
  - nettoie le texte (frontmatter, lignes de pub et de partage) avant de compter les mots
  - marque « court » un article sous le seuil (souvent un mur payant ou un extrait) : on ne l'utilise pas
  - dédoublonne par URL, et rafraîchit une ligne si l'article a été reclippé plus long
  - écrit wiki/sources/articles-db.md (tableau trié par date de clip)

Usage :
    python scripts/articles-db.py                 met à jour la base
    python scripts/articles-db.py --seuil 400     seuil de mots (défaut 400)
    python scripts/articles-db.py --test
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
BRUIT = re.compile(r"(?i)^(share|partager|subscribe|abonne|newsletter|cookie|advertisement|publicit|related|tweet|follow)")


def lire(p: Path) -> tuple[dict, str]:
    t = p.read_text(encoding="utf-8", errors="ignore")
    m = re.match(r"\A---\r?\n(.*?)\r?\n---\r?\n?", t, re.S)
    fm = {}
    if m:
        for l in m.group(1).splitlines():
            k = re.match(r"^(\w+)\s*:\s*\"?(.*?)\"?\s*$", l)
            if k:
                fm[k.group(1).lower()] = k.group(2)
        t = t[m.end():]
    propre = "\n".join(l for l in t.splitlines() if l.strip() and not BRUIT.match(l.strip()))
    return fm, propre


def bilan(racine: Path, seuil: int) -> list[dict]:
    par_url: dict[str, dict] = {}
    for p in sorted((racine / "raw" / "articles").rglob("*.md")):
        fm, texte = lire(p)
        url = fm.get("source") or fm.get("url") or ""
        if not url.startswith("http"):
            url = "sans-url:" + p.relative_to(racine).as_posix()
        mots = len(re.findall(r"\w+", texte))
        ligne = {"date": fm.get("created", "")[:10] or dt.date.fromtimestamp(p.stat().st_mtime).isoformat(),
                 "auteur": p.parent.name, "titre": (fm.get("title") or p.stem).replace("|", "/"),
                 "mots": mots, "statut": "ok" if mots >= seuil else "court", "fichier": p.relative_to(racine).as_posix(),
                 "url": url}
        if url not in par_url or mots > par_url[url]["mots"]:  # le clip le plus complet gagne
            par_url[url] = ligne
    return sorted(par_url.values(), key=lambda x: x["date"], reverse=True)


def ecrire(racine: Path, lignes: list[dict]) -> Path:
    f = racine / "wiki" / "sources" / "articles-db.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    j = dt.date.today().isoformat()
    ok = sum(1 for l in lignes if l["statut"] == "ok")
    out = ["---", 'title: "Base des articles d\'auteurs"', "type: source", f"created: {j}", f"updated: {j}",
           "tags: [sources, articles]", "sources: []", "---", "# Base des articles d'auteurs", "",
           f"Tenue par `scripts/articles-db.py`, ne pas éditer à la main. {ok} utilisables sur {len(lignes)}.",
           "Voir aussi [[index]], la carte des sources [[wiki/sources/_index|sources]] et [[log]].", "",
           "| date | auteur | titre | mots | statut | fichier |", "|:-|:-|:-|-:|:-|:-|"]
    out += [f"| {l['date']} | {l['auteur']} | {l['titre']} | {l['mots']} | {l['statut']} | [[{l['fichier']}]] |" for l in lignes]
    f.write_text("\n".join(out) + "\n", encoding="utf-8")
    return f


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        a = r / "raw" / "articles" / "auteur-x"
        a.mkdir(parents=True)
        long = " ".join(["mot"] * 500)
        (a / "v1.md").write_text("---\nsource: https://ex.org/a\ntitle: A\n---\nteaser\nShare this\n", encoding="utf-8")
        (a / "v2.md").write_text(f"---\nsource: https://ex.org/a\ntitle: A\n---\n{long}\n", encoding="utf-8")
        (a / "b.md").write_text("---\nurl: https://ex.org/b\n---\ncourt\n", encoding="utf-8")
        l = bilan(r, 400)
        assert len(l) == 2, l
        assert {x["url"]: x["statut"] for x in l} == {"https://ex.org/a": "ok", "https://ex.org/b": "court"}
        assert "v2.md" in ecrire(r, l).read_text(encoding="utf-8")
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seuil", type=int, default=400)
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not (VAULT / "raw" / "articles").is_dir():
        print("raw/articles/ absent : crée-le et règle le Web Clipper dessus.", file=sys.stderr)
        return 2
    lignes = bilan(VAULT, a.seuil)
    f = ecrire(VAULT, lignes)
    print(f"{len(lignes)} article(s), {sum(l['statut'] == 'court' for l in lignes)} trop court(s) -> {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
