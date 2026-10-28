#!/usr/bin/env python3
"""Vérifie la table de routage contre les skills et commandes installés.

  python scripts/verifier-routage.py                 (lit wiki/maps/routage.md)
  python scripts/verifier-routage.py chemin/routage.md
  python scripts/verifier-routage.py --test

Signale : les /commandes citées dans la table qui n'existent pas (lien mort), et les skills ou
commandes installés absents de la table (Claude ne saura pas quand les lancer).
Les lignes marquées « à créer » sont ignorées. Les briques du parcours (skills avec une section
Interview) sans phrase sont seulement signalées en info. Pour taire un nom : <!-- hors-routage: nom1, nom2 -->. Sort 0 si tout est bon, 1 sinon. Aucune dépendance.
"""
import glob
import os
import re
import sys


def installes(racine):
    """Rend (outils de tous les jours, briques du parcours). Une brique a une section ## Interview :
    elle sert surtout à construire, on y arrive par « on continue le parcours », une phrase est facultative."""
    outils, briques = set(), set()
    for p in glob.glob(os.path.join(racine, ".claude", "skills", "*", "SKILL.md")):
        nom = os.path.basename(os.path.dirname(p))
        try:
            brique = "\n## Interview" in open(p, encoding="utf-8").read()
        except OSError:
            brique = False
        (briques if brique else outils).add(nom)
    outils |= {os.path.splitext(os.path.basename(p))[0] for p in glob.glob(os.path.join(racine, ".claude", "commands", "*.md"))}
    return outils, briques


def cites(texte):
    noms = set()
    for ligne in texte.splitlines():
        if "à créer" in ligne.lower():
            continue
        noms |= set(re.findall(r"`/([\w:-]+)", ligne))
    return noms


def comparer(cites_, outils, briques=frozenset(), ignores=()):
    morts = sorted(n for n in cites_ - outils - briques if ":" not in n)  # « plugin:skill » vient d'un plugin
    absents = sorted(outils - cites_ - set(ignores))
    briques_sans = sorted(briques - cites_ - set(ignores))
    return morts, absents, briques_sans


if __name__ == "__main__":
    if sys.argv[1:] == ["--test"]:
        t = "| « on reprend » | `/reprise` |\n| « x » | `/fantome` |\n| « ingère » | `/ingest` (à créer) |\n"
        m, a, b = comparer(cites(t), {"reprise", "idee"}, {"hooks-ecrire"})
        assert m == ["fantome"] and a == ["idee"] and b == ["hooks-ecrire"], (m, a, b)
        print("ok")
        sys.exit(0)
    chemin = sys.argv[1] if len(sys.argv) > 1 else os.path.join("wiki", "maps", "routage.md")
    try:
        texte = open(chemin, encoding="utf-8").read()
    except OSError as e:
        sys.exit(f"Table introuvable : {e}")
    # Les skills qui sont des modes toujours actifs ou des briques d'installation n'ont pas besoin d'une phrase.
    ignores = re.findall(r"<!-- hors-routage:\s*([^>]+?)\s*-->", texte)
    ignores = [n.strip() for bloc in ignores for n in bloc.split(",")]
    outils, briques = installes(os.getcwd())
    morts, absents, briques_sans = comparer(cites(texte), outils, briques, ignores)
    for n in morts:
        print(f"Lien mort : `/{n}` est dans la table mais n'existe pas.")
    for n in absents:
        print(f"Absent : `{n}` est installé mais n'a pas de ligne dans la table.")
    if briques_sans:
        print(f"Info : {len(briques_sans)} brique(s) du parcours sans phrase (normal si elles servent seulement à construire) : "
              + ", ".join(briques_sans))
    print("Table de routage à jour." if not (morts or absents) else f"{len(morts) + len(absents)} problème(s).")
    sys.exit(1 if (morts or absents) else 0)
