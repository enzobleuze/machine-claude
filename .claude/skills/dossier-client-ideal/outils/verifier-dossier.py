"""verifier-dossier.py : contrôle le dossier du client idéal d'un vault.

Usage : python scripts/verifier-dossier.py <vault> [--min N]   (sortie 0 = complet, 1 = à compléter)
        python scripts/verifier-dossier.py --test
Lit wiki/business/client-ideal.md (sections 1 à 12, N entrées citées chacune, N = 3 par défaut),
wiki/business/precision-emotionnelle.md (niveau 3 et bibliothèque de micro-moments) et
wiki/business/pensees-client/*.md (sections 1 à 6). Refuse : une citation « » sans sa source entre
parenthèses juste après, un mythe ou une fausse solution sans « Vrai : », un gabarit <...> non rempli,
un fichier de situation absent, un tiret long. Bibliothèque standard seulement.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

GABARIT = re.compile(r"<[a-zà-ÿ][^<>]*>")
SOURCE_APRES = re.compile(r"»\s*\(")
LIEN_SITUATION = re.compile(r"\[\[pensees-client/([^\]|#]+)")


def lire(chemin: Path) -> str:
    # les commentaires <!-- --> sont les consignes des gabarits, pas du contenu
    return re.sub(r"<!--.*?-->", "", chemin.read_text(encoding="utf-8"), flags=re.S)


def sections(texte: str) -> dict[str, list[str]]:
    """{'1': [lignes], ...} pour chaque titre « ## N. ». Les autres titres ## ferment la section."""
    res: dict[str, list[str]] = {}
    courant = None
    for ligne in texte.splitlines():
        if ligne.startswith("## "):
            m = re.match(r"## (\d+)\.", ligne)
            courant = m.group(1) if m else None
            if courant:
                res[courant] = []
        elif courant and ligne.strip():
            res[courant].append(ligne)
    return res


def controles_communs(nom: str, texte: str, pb: list[str]) -> None:
    for i, ligne in enumerate(texte.splitlines(), 1):
        if "\u2014" in ligne or "\u2013" in ligne:
            pb.append(f"{nom}:{i} tiret long")
        if GABARIT.search(ligne):
            pb.append(f"{nom}:{i} gabarit non rempli : {GABARIT.search(ligne).group(0)}")
        if "«" in ligne and not ligne.startswith("#") and not SOURCE_APRES.search(ligne):
            pb.append(f"{nom}:{i} citation sans source juste après")


def verifier(vault: Path, mini: int = 3) -> list[str]:
    pb: list[str] = []
    biz = vault / "wiki" / "business"
    fiche, precision, pensees = biz / "client-ideal.md", biz / "precision-emotionnelle.md", biz / "pensees-client"
    for f in (fiche, precision):
        if not f.exists():
            pb.append(f"absent : {f.relative_to(vault)}")
    if pb:
        return pb

    texte = lire(fiche)
    controles_communs("client-ideal.md", texte, pb)
    secs = sections(texte)
    for n in range(1, 13):
        entrees = [l for l in secs.get(str(n), []) if "«" in l]
        if str(n) not in secs:
            pb.append(f"client-ideal.md : section « ## {n}. » absente")
        elif len(entrees) < mini:
            pb.append(f"client-ideal.md : section {n}, {len(entrees)} entrée(s) citée(s) sur {mini}")
        if n in (6, 7):
            pb += [f"client-ideal.md : section {n}, « Vrai : » manquant : {l[:60]}" for l in entrees if "Vrai :" not in l]
    for nom in sorted(set(LIEN_SITUATION.findall(texte))):
        if not nom.startswith("_") and not (pensees / f"{nom.strip()}.md").exists():
            pb.append(f"situation sans fichier : pensees-client/{nom.strip()}.md")

    texte = lire(precision)
    controles_communs("precision-emotionnelle.md", texte, pb)
    if "### Niveau 3" not in texte:
        pb.append("precision-emotionnelle.md : « ### Niveau 3 » absent")
    biblio = texte.split("## Bibliothèque de micro-moments", 1)
    moments = [l for l in biblio[1].splitlines() if l.startswith("- ")] if len(biblio) == 2 else []
    if len(moments) < mini:
        pb.append(f"precision-emotionnelle.md : {len(moments)} micro-moment(s) sur {mini}")
    pb += [f"precision-emotionnelle.md : micro-moment sans source : {l[:60]}" for l in moments if "(" not in l]

    fichiers = [f for f in sorted(pensees.glob("*.md")) if not f.name.startswith("_")] if pensees.exists() else []
    if not fichiers:
        pb.append("pensees-client/ : aucun fichier de situation")
    for f in fichiers:
        texte = lire(f)
        controles_communs(f"pensees-client/{f.name}", texte, pb)
        secs = sections(texte)
        for n in range(1, 7):
            lignes = secs.get(str(n), [])
            if not lignes or (n <= 5 and not any("«" in l for l in lignes)):
                pb.append(f"pensees-client/{f.name} : section {n} vide ou sans citation")
    return pb


def auto_test() -> int:
    def entree(n: int, k: int) -> str:
        vrai = " Vrai : selon l'expert (carnet expert)" if n in (6, 7) else ""
        return f"- « phrase {n}.{k} » (raw/source-{k}.md).{vrai}"

    fiche = "# Dossier\n## Les situations\n1. Situation : [[pensees-client/situation-a]]\n" + "".join(
        f"## {n}. Section\n" + "\n".join(entree(n, k) for k in range(3)) + "\n" for n in range(1, 13))
    precision = "# P\n### Niveau 3\n- « scène » (raw/a.md)\n## Bibliothèque de micro-moments\n" + "".join(
        f"- moment {k} (raw/b.md)\n" for k in range(3))
    pensee = "".join(f"## {n}. T\n1. « pensée {n} » (raw/c.md)\n" for n in range(1, 6)) + "## 6. Trous\n- aucun\n"
    with tempfile.TemporaryDirectory() as tmp:
        biz = Path(tmp) / "wiki" / "business"
        (biz / "pensees-client").mkdir(parents=True)
        (biz / "client-ideal.md").write_text(fiche, encoding="utf-8")
        (biz / "precision-emotionnelle.md").write_text(precision, encoding="utf-8")
        (biz / "pensees-client" / "situation-a.md").write_text(pensee, encoding="utf-8")
        assert verifier(Path(tmp)) == [], verifier(Path(tmp))
        (biz / "client-ideal.md").write_text(
            fiche.replace("« phrase 2.1 » (raw/source-1.md)", "« phrase 2.1 »").replace(" Vrai : selon", " selon", 1)
            + "- <phrase exacte> \u2014 \n", encoding="utf-8")
        (biz / "pensees-client" / "situation-a.md").unlink()
        pb = verifier(Path(tmp))
        for attendu in ("sans source", "Vrai :", "gabarit non rempli", "tiret long", "situation sans fichier", "aucun fichier"):
            assert any(attendu in p for p in pb), f"non détecté : {attendu}\n{pb}"
    print("AUTO-TEST OK")
    return 0


def main(args: list[str]) -> int:
    if args[:1] == ["--test"]:
        return auto_test()
    if not args:
        print(__doc__)
        return 2
    mini = int(args[args.index("--min") + 1]) if "--min" in args else 3
    vault = Path(args[0])
    pb = verifier(vault, mini)
    for p in pb:
        print("  ", p)
    print("DOSSIER OK" if not pb else f"À COMPLÉTER : {len(pb)} point(s)")
    return 0 if not pb else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
