"""generer-parcours.py : reconstruit parcours/parcours-modele.md depuis parcours/bloc-*.md.

Usage : python outils/generer-parcours.py      (depuis la racine du kit)
Une ligne par skill, dans l'ordre où chaque bloc le cite pour la première fois dans un tableau.
"""
import re
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parent.parent
SKILLS = {p.name for p in (KIT / ".claude" / "skills").iterdir() if p.is_dir()}
BLOCS = {"a": "Cerveau", "b": "Méthode", "c": "Experts", "d": "Business", "e": "Contenu", "f": "Automatisation"}


def skills_du_bloc(texte: str) -> list[str]:
    vus = []
    for ligne in texte.splitlines():
        if ligne.startswith("|"):
            for nom in re.findall(r"`([a-z0-9-]+)`", ligne):
                if nom in SKILLS and nom not in vus:
                    vus.append(nom)
    return vus


def main() -> int:
    lignes = [
        "---", 'title: "Parcours Machine : où j\'en suis"', "type: map", "created: AAAA-MM-JJ", "updated: AAAA-MM-JJ", "tags: [parcours, machine]",
        'sources: ["[[blueprint]]", "[[routage]]", "[[index]]"]', "---", "# Parcours",
        "", "Suivi des briques de [[blueprint]]. Lu au début de chaque conversation. Commandes : [[routage]]. Catalogue : [[index]].",
        "", "Version du kit installée : AAAA-MM-JJ (voir CHANGELOG.md du kit).",
        "", "Légende : ✅ fait (test passé) · 🟡 partiel · ❌ absent", "",
        "| Brique | Skill | État | Date | Note |", "|:-|:-|:-|:-|:-|", "| 0 | audit (INSTALLER.md) | ❌ | | |",
    ]
    total = 0
    for lettre, nom in BLOCS.items():
        f = KIT / "parcours" / f"bloc-{lettre}.md"
        if not f.exists():
            print(f"manque {f.name}", file=sys.stderr)
            return 1
        propres = [s for s in skills_du_bloc(f.read_text(encoding="utf-8")) if f"`{s}`" not in "\n".join(lignes)]
        for i, s in enumerate(propres, 1):  # un skill cité par un bloc plus loin reste à sa première place
            lignes.append(f"| {lettre.upper()}{i} ({nom}) | `{s}` | ❌ | | |")
            total += 1
    oublies = SKILLS - {"bibliothecaire"} - set(re.findall(r"`([a-z0-9-]+)`", "\n".join(lignes)))
    lignes += ["", "## Journal du parcours", "- AAAA-MM-JJ : machine installée."]
    (KIT / "parcours" / "parcours-modele.md").write_text("\n".join(lignes) + "\n", encoding="utf-8")
    print(f"{total} briques écrites.")
    if oublies:
        print("Skills absents des tableaux de blocs :", ", ".join(sorted(oublies)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
