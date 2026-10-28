#!/usr/bin/env python3
"""jardinier.py : entretien automatique du wiki, pensé pour tourner la nuit.

Déterministe (aucun appel d'IA, coût nul). Il ne supprime JAMAIS rien.
  1. frontmatter : complète les clés absentes, n'écrase jamais une valeur existante
  2. index.md    : régénère le catalogue entre les marqueurs JARDINIER:DEBUT et JARDINIER:FIN
  3. log.md      : déplace les entrées des trimestres finis vers logs/log-AAAA-Tn.md
  4. archivage   : DÉPLACE les vieux fichiers des dossiers listés dans scripts/jardinier.json
  5. détection   : liens morts et orphelines vont dans le résumé (Claude les répare en session)

Usage (le script vit dans scripts/, à côté de lint_wiki.py) :
    python scripts/jardinier.py                    essai à blanc : montre ce qu'il ferait
    python scripts/jardinier.py --live             écrit vraiment
    python scripts/jardinier.py --live --commit    écrit puis fait UN commit git (retour arrière facile)
    python scripts/jardinier.py --test             auto-test sur un mini vault temporaire

Sécurité : tant que le fichier .jardinier-rodage existe à la racine, --live est ignoré.
Résumé écrit dans outputs/jardinier/AAAA-MM-JJ.md à chaque passage.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import lint_wiki  # noqa: E402  (même dossier)

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

DEBUT, FIN = "<!-- JARDINIER:DEBUT -->", "<!-- JARDINIER:FIN -->"
TYPES = {"principes": "principe", "clients": "client", "sources": "source", "maps": "map",
         "contenu": "contenu", "strategie": "strategie", "journal": "journal"}
CONFIG_DEFAUT = {"prives": ["wiki/finances"], "archivage": []}
ENTREE_LOG = re.compile(r"^## \[(\d{4})-(\d{2})-(\d{2})\]", re.M)


def config(root: Path) -> dict:
    f = root / "scripts" / "jardinier.json"
    c = dict(CONFIG_DEFAUT)
    if f.exists():
        c.update(json.loads(f.read_text(encoding="utf-8")))
    return c


def prive(rel: str, c: dict) -> bool:
    return any(rel == p or rel.startswith(p.rstrip("/") + "/") for p in c["prives"])


def date_creation(root: Path, p: Path) -> str:
    try:
        out = subprocess.run(["git", "log", "--diff-filter=A", "--format=%as", "--", str(p)],
                             cwd=root, capture_output=True, text=True, timeout=20).stdout.split()
        if out:
            return out[-1]
    except Exception:
        pass
    return dt.date.fromtimestamp(p.stat().st_mtime).isoformat()


def plan_frontmatter(root: Path, c: dict) -> list[tuple[Path, str]]:
    out = []
    for p in sorted((root / "wiki").rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if prive(rel, c) or any(i in p.parts for i in lint_wiki.IGNORES):
            continue
        texte = p.read_text(encoding="utf-8", errors="ignore")
        fm, corps = lint_wiki.parse_fm(texte)
        manque = [k for k in lint_wiki.CLES_FM if k not in fm]
        if not manque:
            continue
        h1 = re.search(r"^# (.+)$", corps, re.M)
        dossier = p.relative_to(root / "wiki").parts[0] if len(p.relative_to(root / "wiki").parts) > 1 else ""
        valeurs = {
            "title": '"' + (h1.group(1).strip() if h1 else p.stem.replace("-", " ")).replace('"', "'") + '"',
            "type": TYPES.get(dossier, "note"),
            "created": date_creation(root, p),
            "updated": dt.date.fromtimestamp(p.stat().st_mtime).isoformat(),
            "tags": "[]",
            "sources": "[]",
        }
        ajout = "".join(f"{k}: {valeurs[k]}\n" for k in manque)
        if fm or texte.lstrip("﻿").startswith("---"):
            neuf = re.sub(r"\r?\n---\r?\n", lambda m: "\n" + ajout + "---\n", texte, count=1)
        else:
            neuf = "---\n" + ajout + "---\n" + texte
        out.append((p, neuf))
    return out


def plan_index(root: Path, c: dict) -> str | None:
    f = root / "index.md"
    if not f.exists():
        return None
    groupes: dict[str, list[str]] = {}
    for p in sorted((root / "wiki").rglob("*.md")):
        rel = p.relative_to(root).as_posix()
        if prive(rel, c) or "archive" in p.parts or p.stem.lower() in lint_wiki.NAVIGATION:
            continue
        parts = p.relative_to(root / "wiki").parts
        fm, _ = lint_wiki.parse_fm(p.read_text(encoding="utf-8", errors="ignore"))
        titre = fm.get("title", "").strip('"\'') or p.stem
        groupes.setdefault(parts[0] if len(parts) > 1 else "(racine)", []).append(f"- [[{p.stem}]] : {titre}")
    bloc = [DEBUT, "*Section tenue par le jardinier : ne pas éditer à la main.*", ""]
    for g in sorted(groupes):
        bloc += [f"### {g} ({len(groupes[g])})", *groupes[g], ""]
    bloc.append(FIN)
    texte = f.read_text(encoding="utf-8")
    if DEBUT in texte and FIN in texte:
        neuf = texte[:texte.index(DEBUT)] + "\n".join(bloc) + texte[texte.index(FIN) + len(FIN):]
    else:
        neuf = texte.rstrip() + "\n\n## Catalogue\n\n" + "\n".join(bloc) + "\n"
    return None if neuf == texte else neuf


def trimestre(annee: int, mois: int) -> tuple[int, int]:
    return annee, (mois - 1) // 3 + 1


def plan_log(root: Path, aujourd_hui: dt.date) -> tuple[str, dict[str, str]] | None:
    f = root / "log.md"
    if not f.exists():
        return None
    texte = f.read_text(encoding="utf-8")
    pos = [m.start() for m in ENTREE_LOG.finditer(texte)]
    if not pos:
        return None
    courant = trimestre(aujourd_hui.year, aujourd_hui.month)
    garde, sortants = [texte[:pos[0]]], {}
    for i, d in enumerate(pos):
        bloc = texte[d:pos[i + 1] if i + 1 < len(pos) else len(texte)]
        m = ENTREE_LOG.match(bloc)
        t = trimestre(int(m.group(1)), int(m.group(2)))
        if t < courant:
            sortants.setdefault(f"logs/log-{t[0]}-T{t[1]}.md", "")
            sortants[f"logs/log-{t[0]}-T{t[1]}.md"] += bloc
        else:
            garde.append(bloc)
    return ("".join(garde), sortants) if sortants else None


def plan_archivage(root: Path, c: dict, aujourd_hui: dt.date) -> list[tuple[Path, Path]]:
    out = []
    for regle in c.get("archivage", []):
        dossier = root / regle["dossier"]
        if not dossier.is_dir():
            continue
        for p in sorted(dossier.glob("*.md")):
            age = (aujourd_hui - dt.date.fromtimestamp(p.stat().st_mtime)).days
            if age >= int(regle["age_jours"]) and p.name != "_index.md":
                cible = root / "wiki" / "archive" / p.relative_to(root / "wiki")
                if not cible.exists():
                    out.append((p, cible))
    return out


def ecrire(p: Path, texte: str) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(texte, encoding="utf-8")


def passage(root: Path, live: bool, commit: bool, aujourd_hui: dt.date | None = None) -> dict:
    aujourd_hui = aujourd_hui or dt.date.today()
    c = config(root)
    if (root / ".jardinier-rodage").exists() and live:
        print("Rodage : le fichier .jardinier-rodage existe, passage à blanc forcé.")
        live = False
    fm = plan_frontmatter(root, c)
    archives = plan_archivage(root, c, aujourd_hui)
    log = plan_log(root, aujourd_hui)
    if live:
        for p, t in fm:
            ecrire(p, t)
        for src, dst in archives:
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dst))  # déplacement, jamais de suppression
            ancien = src.relative_to(root).as_posix()[:-3]
            nouveau = dst.relative_to(root).as_posix()[:-3]
            for page in (root / "wiki").rglob("*.md"):  # liens écrits avec le chemin complet
                t = page.read_text(encoding="utf-8", errors="ignore")
                if f"[[{ancien}" in t:
                    ecrire(page, t.replace(f"[[{ancien}", f"[[{nouveau}"))
        if log:
            garde, sortants = log
            for rel, bloc in sortants.items():
                cible = root / rel
                avant = cible.read_text(encoding="utf-8") if cible.exists() else f"# Journal archivé {cible.stem}\n\n"
                ecrire(cible, avant + bloc)
            ecrire(root / "log.md", garde)
    index = plan_index(root, c)  # après l'archivage pour refléter les déplacements
    if live and index:
        ecrire(root / "index.md", index)
    b = lint_wiki.bilan(root)
    resume = {
        "date": aujourd_hui.isoformat(), "mode": "écriture" if live else "à blanc",
        "frontmatter_completes": [p.relative_to(root).as_posix() for p, _ in fm],
        "archives": [f"{s.relative_to(root).as_posix()} -> {d.relative_to(root).as_posix()}" for s, d in archives],
        "log_rotation": sorted(log[1]) if log else [],
        "index_mis_a_jour": bool(index),
        "liens_morts": len(b["liens_morts"]), "orphelines": len(b["orphelines"]),
    }
    lignes = [f"# Jardinier {resume['date']} ({resume['mode']})", "",
              f"- Frontmatter complétés : {len(resume['frontmatter_completes'])}",
              f"- Fichiers archivés : {len(resume['archives'])}",
              f"- Journaux trimestriels : {', '.join(resume['log_rotation']) or 'aucun'}",
              f"- Index régénéré : {'oui' if resume['index_mis_a_jour'] else 'rien à changer'}",
              f"- À réparer en session : {resume['liens_morts']} liens morts, {resume['orphelines']} orphelines",
              "", "Détail :", *[f"- {x}" for x in resume["frontmatter_completes"] + resume["archives"]]]
    ecrire(root / "outputs" / "jardinier" / f"{resume['date']}.md", "\n".join(lignes) + "\n")
    print("\n".join(lignes[:7]))
    if live and commit:
        chemins = [x for x in ("wiki", "index.md", "log.md", "logs") if (root / x).exists()]
        subprocess.run(["git", "add", "-A", *chemins], cwd=root, check=False)
        if subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=root).returncode != 0:
            r = subprocess.run(["git", "commit", "-m", f"jardinier: entretien {resume['date']}"], cwd=root)
            if r.returncode != 0:
                print("Commit git échoué : les changements sont écrits mais pas commités.", file=sys.stderr)
    return resume


def auto_test() -> int:
    import tempfile
    with tempfile.TemporaryDirectory() as d:
        r = Path(d)
        (r / "wiki" / "principes").mkdir(parents=True)
        (r / "wiki" / "finances").mkdir()
        (r / "wiki" / "principes" / "ecoute.md").write_text("# L'écoute\n[[autre]]\n", encoding="utf-8")
        (r / "wiki" / "principes" / "autre.md").write_text("---\ntitle: Autre\ntype: principe\n---\ntexte\n", encoding="utf-8")
        (r / "wiki" / "finances" / "secret.md").write_text("sans frontmatter\n", encoding="utf-8")
        (r / "index.md").write_text("# Index\n", encoding="utf-8")
        (r / "log.md").write_text("# Log\n\n## [2020-01-05] vieux\nx\n\n## [2999-01-01] futur\ny\n", encoding="utf-8")
        avant = (r / "wiki" / "principes" / "ecoute.md").read_text(encoding="utf-8")
        passage(r, live=False, commit=False)
        assert (r / "wiki" / "principes" / "ecoute.md").read_text(encoding="utf-8") == avant, "à blanc a écrit"
        passage(r, live=True, commit=False)
        e = (r / "wiki" / "principes" / "ecoute.md").read_text(encoding="utf-8")
        assert e.startswith("---\n") and "type: principe" in e and "[[autre]]" in e, e
        a = (r / "wiki" / "principes" / "autre.md").read_text(encoding="utf-8")
        assert "title: Autre" in a and a.count("title:") == 1 and "tags: []" in a, a
        assert (r / "wiki" / "finances" / "secret.md").read_text(encoding="utf-8") == "sans frontmatter\n"
        assert DEBUT in (r / "index.md").read_text(encoding="utf-8")
        assert "vieux" in (r / "logs" / "log-2020-T1.md").read_text(encoding="utf-8")
        assert "vieux" not in (r / "log.md").read_text(encoding="utf-8")
        (r / ".jardinier-rodage").write_text("", encoding="utf-8")
        assert passage(r, live=True, commit=False)["mode"] == "à blanc"
    print("auto-test OK")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Entretien automatique du wiki (ne supprime jamais).")
    ap.add_argument("--vault", type=Path, default=Path(__file__).resolve().parent.parent)
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--commit", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        return auto_test()
    if not (a.vault / "wiki").is_dir():
        print(f"Dossier wiki/ introuvable sous {a.vault}.", file=sys.stderr)
        return 2
    passage(a.vault, a.live, a.commit)
    return 0


if __name__ == "__main__":
    sys.exit(main())
