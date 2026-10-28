#!/usr/bin/env python3
"""Vérifie qu'un skill (SKILL.md) ou une commande (.claude/commands/*.md) respecte le format.

  python scripts/verifier-skill.py .claude/skills/mon-skill/SKILL.md
  python scripts/verifier-skill.py .claude/skills .claude/commands      (tout un dossier)
  python scripts/verifier-skill.py --test                                (auto-test)

Sort 0 si tout est bon, 1 sinon (avec la liste des problèmes). Aucune dépendance.
"""
import os
import re
import sys

SECTIONS = ["Pourquoi", "Prérequis", "Interview", "Construire", "Test", "Pièges vécus",
            "Entretien dans le temps", "Après"]
TIRETS = ("\u2014", "\u2013")  # tiret long et tiret moyen


def frontmatter(texte):
    m = re.match(r"﻿?---\r?\n(.*?)\r?\n---", texte, re.S)
    if not m:
        return None
    champs, cle = {}, None
    for ligne in m.group(1).splitlines():
        kv = re.match(r"^([\w-]+):\s*(.*)$", ligne)
        if kv:
            cle = kv.group(1)
            champs[cle] = kv.group(2).strip().strip('"').strip(">").strip()
        elif cle:  # description sur plusieurs lignes
            champs[cle] = (champs[cle] + " " + ligne.strip()).strip()
    return champs


def verifier(chemin, texte):
    pb = []
    fm = frontmatter(texte)
    est_skill = os.path.basename(chemin) == "SKILL.md"
    if fm is None:
        return ["pas de frontmatter --- en tête"]
    desc = fm.get("description", "")
    if not desc:
        pb.append("description absente")
    elif "Utiliser quand" not in desc:
        pb.append("la description ne dit pas « Utiliser quand l'utilisateur dit … » (c'est le déclencheur)")
    if est_skill:
        nom = fm.get("name", "")
        dossier = os.path.basename(os.path.dirname(os.path.abspath(chemin)))
        if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", nom):
            pb.append(f"name « {nom} » n'est pas en kebab-case")
        elif nom != dossier:
            pb.append(f"name « {nom} » différent du dossier « {dossier} »")
        titres = re.findall(r"^##\s+(.+?)\s*$", texte, re.M)
        for s in SECTIONS:
            if s not in titres:
                pb.append(f"section manquante : ## {s}")
    for i, ligne in enumerate(texte.splitlines(), 1):
        if any(t in ligne for t in TIRETS):
            pb.append(f"ligne {i} : tiret long ou moyen")
        if "{{" in ligne and "}}" in ligne and not est_skill:
            pb.append(f"ligne {i} : placeholder {{{{…}}}} oublié")
    return pb


def fichiers(cibles):
    for c in cibles:
        if os.path.isdir(c):
            for racine, _, noms in os.walk(c):
                for n in noms:
                    if n == "SKILL.md" or (n.endswith(".md") and os.path.basename(racine) == "commands"):
                        yield os.path.join(racine, n)
        else:
            yield c


def auto_test():
    bon = ("---\nname: x\ndescription: \"Fait X. Utiliser quand l'utilisateur dit « x ».\"\n---\n# X\n"
           + "".join(f"## {s}\nok\n" for s in SECTIONS))
    assert frontmatter(bon)["name"] == "x"
    assert verifier("/k/x/SKILL.md", bon) == [], verifier("/k/x/SKILL.md", bon)
    mauvais = "---\nname: Mon Skill\ndescription: fait des choses\n---\n# Y \u2014 titre\n"
    p = verifier("/k/y/SKILL.md", mauvais)
    assert any("kebab" in x for x in p) and any("Utiliser quand" in x for x in p) and any("tiret" in x for x in p)
    cmd = "---\ndescription: \"Fait Z. Utiliser quand l'utilisateur dit « z ».\"\n---\n# /z\n"
    assert verifier("/v/.claude/commands/z.md", cmd) == []
    print("ok")


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        auto_test()
        sys.exit(0)
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    total = 0
    for f in fichiers(sys.argv[1:]):
        try:
            with open(f, encoding="utf-8") as h:
                problemes = verifier(f, h.read())
        except OSError as e:
            problemes = [f"illisible : {e}"]
        if problemes:
            total += len(problemes)
            print(f"\n{f}")
            for p in problemes:
                print(f"  - {p}")
    print(f"\n{total} problème(s)." if total else "Tout est conforme.")
    sys.exit(1 if total else 0)
