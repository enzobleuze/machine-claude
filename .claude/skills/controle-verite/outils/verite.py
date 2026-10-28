"""verite.py : contrôles de vérité déterministes (skill controle-verite). Python 3.8+, bibliothèque standard seule.

  python verite.py chiffres <texte> --sources <fichier|dossier> [...] [--permis permis.txt]
      Chaque chiffre du texte (nombre, pourcentage, durée en chiffres) doit apparaître dans une des sources,
      ou dans la liste des chiffres permis (un par ligne : années de la marque, prix publics, etc.). Sinon : inventé.
  python verite.py attributions <texte> --auteurs auteurs.json
      Toute personne citée (« selon X », « X dit », ou un nom de auteurs.json) doit avoir une fiche source non vide.
      Les attributions vagues (« des études montrent », « les experts disent ») sont refusées.
  python verite.py noms <texte> --liste noms-prives.txt
      Aucun nom de la liste privée (vrais clients, proches) dans un texte public. Casse et accents ignorés.
  python verite.py pseudonymiser <entree> <sortie> --liste noms-prives.txt --table table.json [--prefixe Client]
      Remplace chaque nom privé par « Client 001 » (stable d'une fois sur l'autre grâce à table.json),
      masque emails et téléphones. Sert à fabriquer les sources du client idéal.
  python verite.py selftest

Sortie : 0 = propre, 1 = problème trouvé (liste imprimée), 2 = usage ou fichier illisible.
Les fichiers privés (noms-prives.txt, table.json) ne quittent jamais la machine : à mettre dans .gitignore.
"""
import argparse
import json
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

CHIFFRE = re.compile(r"(?<![\w.,])\d+(?:[.,]\d+)?(?:\s?%)?")
URL = re.compile(r"https?://\S+|www\.\S+")
VAGUE = re.compile(r"\b(des|les|plusieurs|de nombreuses) (études|recherches|scientifiques|chercheurs|experts|psychologues)"
                   r"\b[^.\n]{0,40}\b(montrent|prouvent|disent|affirment|ont montré|ont prouvé)\b", re.I)
SELON = re.compile(r"\b(?i:selon|d'après|comme le dit|comme l'écrit)\s+((?:[A-ZÉÈÀ][\w'’\-]+\s?){1,3})")
EMAIL = re.compile(r"[\w.+-]+@[\w-]+\.[\w.]+")
TEL = re.compile(r"(?:\+\d{1,3}[\s.]?)?(?:\(?\d{2,4}\)?[\s.\-]?){3,5}\d{2,4}")
TEXTE_SOURCE = {".md", ".txt", ".json", ".csv", ".html", ".srt", ".vtt"}


def _n(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def _lire(p):
    return Path(p).read_text(encoding="utf-8-sig", errors="replace")


def _norm_chiffre(c):
    return re.sub(r"\s", "", c).replace(",", ".")


def chiffres_de(texte):
    return [m.group(0) for m in CHIFFRE.finditer(URL.sub(" ", texte))]


def controle_chiffres(texte, sources, permis=()):
    pool = set(_norm_chiffre(p) for p in permis)
    for s in sources:
        p = Path(s)
        fichiers = [f for f in p.rglob("*") if f.suffix.lower() in TEXTE_SOURCE] if p.is_dir() else [p]
        for f in fichiers:
            pool |= {_norm_chiffre(c) for c in chiffres_de(_lire(f))}
            pool |= {_norm_chiffre(c).rstrip("%") for c in chiffres_de(_lire(f))}
    manque = []
    for c in chiffres_de(texte):
        k = _norm_chiffre(c)
        if k not in pool and k.rstrip("%") not in pool | {"1"}:  # « 1 » sert d'article (« 1 seule fois »)
            manque.append(c)
    return [f"chiffre sans source : « {c} »" for c in dict.fromkeys(manque)]


def controle_attributions(texte, auteurs, base=Path(".")):
    """auteurs : {"Nom affiché": "chemin/vers/fiche-source.md"}."""
    out = [f"attribution vague : « {m.group(0)} »" for m in VAGUE.finditer(texte)]
    connus = {_n(nom): fiche for nom, fiche in auteurs.items()}
    cites = {_n(m.group(1).strip()) for m in SELON.finditer(texte)}
    cites |= {k for k in connus if re.search(rf"(?<!\w){re.escape(k)}(?!\w)", _n(texte))}
    for c in sorted(cites):
        fiche = connus.get(c) or next((f for k, f in connus.items() if k.split()[-1] == c.split()[-1]), None)
        if not fiche:
            out.append(f"personne citée sans fiche source : « {c} » (l'ajouter à auteurs.json avec sa fiche, ou retirer la citation)")
        elif not (base / fiche).is_file() or not _lire(base / fiche).strip():
            out.append(f"fiche source absente ou vide pour « {c} » : {fiche}")
    return out


def _noms(liste):
    return [l.strip() for l in _lire(liste).splitlines() if l.strip() and not l.lstrip().startswith("#")]


def _rx_nom(nom):
    return re.compile(rf"(?<!\w){re.escape(_n(nom))}(?!\w)")


def controle_noms(texte, noms):
    t = _n(texte)
    return [f"nom privé dans le texte : « {nom} »" for nom in noms if _rx_nom(nom).search(t)]


def pseudonymiser(texte, noms, table, prefixe="Client"):
    """Remplace les noms (les plus longs d'abord, pour « Prénom Nom » avant « Prénom »). Modifie table sur place."""
    texte = EMAIL.sub("[email]", texte)
    texte = TEL.sub(lambda m: "[téléphone]" if len(re.sub(r"\D", "", m.group(0))) >= 8 else m.group(0), texte)
    for nom in sorted(noms, key=len, reverse=True):
        if nom not in table:
            table[nom] = f"{prefixe} {len(table) + 1:03d}"
        # recherche sans accents ni casse, remplacement dans le texte d'origine (la normalisation garde la longueur
        # pour les lettres accentuées composées ; sinon on retombe sur une recherche exacte)
        plat = _n(texte)
        if len(plat) != len(texte):
            texte = re.sub(rf"(?<!\w){re.escape(nom)}(?!\w)", table[nom], texte, flags=re.I)
            continue
        morceaux, pos = [], 0
        for m in _rx_nom(nom).finditer(plat):
            morceaux += [texte[pos:m.start()], table[nom]]
            pos = m.end()
        texte = "".join(morceaux) + texte[pos:]
    return texte


def _rapport(problemes):
    for p in problemes:
        print("REFUS : " + p)
    print("PROPRE" if not problemes else f"{len(problemes)} problème(s)")
    return 1 if problemes else 0


def selftest():
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        src = t / "source.md"
        src.write_text("Après 30 jours, 3 étapes. Voir 2019.", encoding="utf-8")
        assert controle_chiffres("Fais les 3 étapes pendant 30 jours.", [src]) == []
        assert controle_chiffres("73 % des hommes échouent.", [src]) == ["chiffre sans source : « 73 % »"]
        assert controle_chiffres("En 2024 j'ai lancé.", [src], permis=["2024"]) == []
        assert controle_chiffres("Va sur https://site.fr/page-42", [src]) == [], "URL ignorée"
        assert controle_chiffres("Fais-le 1 fois.", [src]) == []
        fiche = t / "auteur-x.md"
        fiche.write_text("Notes sur l'auteur.", encoding="utf-8")
        auteurs = {"Marie Durand": "auteur-x.md", "Paul Vide": "vide.md"}
        assert controle_attributions("Selon Marie Durand, il faut écouter.", auteurs, t) == []
        assert controle_attributions("Comme le dit Durand, écoute.", auteurs, t) == [], "nom de famille seul"
        assert len(controle_attributions("Selon Jean Inconnu, ça marche.", auteurs, t)) == 1
        assert len(controle_attributions("Paul Vide le répète.", auteurs, t)) == 1, "fiche absente"
        assert len(controle_attributions("Des études montrent que c'est vrai.", auteurs, t)) == 1
        assert controle_noms("Merci à Hélène pour son retour.", ["Helene"]) == ["nom privé dans le texte : « Helene »"]
        assert controle_noms("Merci à Hélènette.", ["Helene"]) == [], "mot entier seulement"
        table = {}
        out = pseudonymiser("Marc Petit a écrit à marc@example.com. Marc rappelle au 06 12 34 56 78.", ["Marc", "Marc Petit"], table)
        assert "Marc" not in out and "[email]" in out and "[téléphone]" in out, out
        assert table["Marc Petit"] != table["Marc"], table
        assert pseudonymiser("Marc revient.", ["Marc"], table) == f"{table['Marc']} revient.", "stable"
    print("selftest OK")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Contrôles de vérité")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("chiffres")
    c.add_argument("texte")
    c.add_argument("--sources", nargs="+", default=[])
    c.add_argument("--permis")
    a_ = sub.add_parser("attributions")
    a_.add_argument("texte")
    a_.add_argument("--auteurs", required=True)
    n = sub.add_parser("noms")
    n.add_argument("texte")
    n.add_argument("--liste", required=True)
    p = sub.add_parser("pseudonymiser")
    p.add_argument("entree")
    p.add_argument("sortie")
    p.add_argument("--liste", required=True)
    p.add_argument("--table", required=True)
    p.add_argument("--prefixe", default="Client")
    sub.add_parser("selftest")
    a = ap.parse_args()
    try:
        if a.cmd == "selftest":
            return selftest()
        if a.cmd == "chiffres":
            permis = _lire(a.permis).split() if a.permis else []
            return _rapport(controle_chiffres(_lire(a.texte), a.sources, permis))
        if a.cmd == "attributions":
            return _rapport(controle_attributions(_lire(a.texte), json.loads(_lire(a.auteurs)), Path(a.auteurs).parent))
        if a.cmd == "noms":
            return _rapport(controle_noms(_lire(a.texte), _noms(a.liste)))
        tf = Path(a.table)
        table = json.loads(_lire(tf)) if tf.is_file() else {}
        Path(a.sortie).write_text(pseudonymiser(_lire(a.entree), _noms(a.liste), table, a.prefixe), encoding="utf-8")
        tf.write_text(json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
        reste = controle_noms(_lire(a.sortie), _noms(a.liste))
        print(f"{a.sortie} écrit, {len(table)} pseudonymes dans {tf}")
        return _rapport(reste)
    except (OSError, json.JSONDecodeError) as e:
        print(f"lecture impossible : {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
