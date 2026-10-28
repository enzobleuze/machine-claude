"""lint_voix.py : contrôle de voix par règles dures mesurables (skill controle-voix). Python 3.8+, bibliothèque standard seule.

  python lint_voix.py <texte> [--regles regles-voix.json] [--fix] [--json]
      Sortie 0 = propre (ou tout corrigé par --fix), 1 = au moins une violation « dur » restante, 2 = usage ou règles illisibles.
      Les violations « alerte » s'impriment sans bloquer.
  python lint_voix.py selftest

Règles : --regles, sinon la variable VOIX_REGLES, sinon regles-voix.json dans le dossier courant, sinon à côté du script.
Format (toutes les clés sont facultatives) :
  {
    "tirets_longs": true,                        tiret long, demi-tiret et double tiret hors URL et hors code
    "remplacement_tiret": ", ",
    "ignorer_citations": true,                   lignes « > » (verbatims) signalées sans correction
    "mots_interdits": [{"mot": "focus", "remplacer_par": "attention", "niveau": "dur"}],
    "motifs_interdits": [{"motif": "regex", "message": "pourquoi", "niveau": "dur|alerte", "remplacer_par": "texte"}],
    "anaphore": {"actif": true, "min": 3, "mots_exclus": ["le", "la", "les"]}
  }
Un mot interdit se cherche entier, sans tenir compte de la casse. Un motif est une expression régulière Python,
insensible à la casse sauf si "casse": true.
"""
import argparse
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

URL_OU_CODE = re.compile(r"https?://\S+|`[^`]*`|\]\([^)]*\)")
TIRETS = re.compile(r"\s*[\u2014\u2013]\s*|(?<![-<!])--(?![->])")
PHRASES = re.compile(r"(?<=[.!?])\s+")
MOTS_EXCLUS_DEFAUT = {"le", "la", "les", "un", "une", "des", "de", "du", "et", "a", "à", "en"}  # jamais les pronoms : « Tu... Tu... Tu... » est une anaphore


def charger_regles(chemin=None):
    for c in (chemin, os.environ.get("VOIX_REGLES"), "regles-voix.json", Path(__file__).with_name("regles-voix.json")):
        if c and Path(c).is_file():
            try:
                return json.loads(Path(c).read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as e:
                raise SystemExit(f"règles illisibles ({c}) : {e}")
    return {"tirets_longs": True, "anaphore": {"actif": True}}


def _sans_accent(s):
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def _compiler(regles):
    """[(regex, message, niveau, remplacement)]"""
    out = []
    for m in regles.get("mots_interdits", []):
        mot = m if isinstance(m, str) else m["mot"]
        d = {} if isinstance(m, str) else m
        out.append((re.compile(rf"(?<!\w){re.escape(mot)}(?!\w)", re.I), f"mot interdit « {mot} »",
                    d.get("niveau", "dur"), d.get("remplacer_par")))
    for m in regles.get("motifs_interdits", []):
        try:
            rx = re.compile(m["motif"], 0 if m.get("casse") else re.I)
        except (re.error, KeyError) as e:
            raise SystemExit(f"motif invalide {m!r} : {e}")
        out.append((rx, m.get("message", m["motif"]), m.get("niveau", "dur"), m.get("remplacer_par")))
    return out


def _masque(ligne):
    """Les zones URL et code, remplacées par des espaces de même longueur (positions conservées)."""
    return URL_OU_CODE.sub(lambda m: " " * len(m.group(0)), ligne)


def _premier_mot(s, exclus):
    m = re.match(r"\W*([\w'’]+)", s)
    if not m:
        return None
    w = _sans_accent(m.group(1)).replace("’", "'")
    return None if w in exclus else w


def _anaphores(lignes, cfg):
    """Séries d'au moins `min` phrases ou lignes consécutives (dans un même paragraphe) au même premier mot."""
    if not cfg.get("actif", True):
        return []
    n_min = int(cfg.get("min", 3))
    exclus = {_sans_accent(w) for w in cfg.get("mots_exclus", MOTS_EXCLUS_DEFAUT)}
    out, unites = [], []

    def fin_de_paragraphe():
        serie = []
        for no, u in unites + [(0, "")]:
            w = _premier_mot(u, exclus)
            if w and serie and serie[-1][1] == w:
                serie.append((no, w))
                continue
            if len(serie) >= n_min:
                out.append({"ligne": serie[0][0], "niveau": "dur", "message": f"anaphore : {len(serie)} phrases ou lignes de suite "
                            f"commencent par « {serie[0][1]} »", "extrait": serie[0][1]})
            serie = [(no, w)] if w else []
        unites.clear()
    for no, l in enumerate(lignes, 1):
        if not l.strip():
            fin_de_paragraphe()
            continue
        for p in PHRASES.split(l.strip().lstrip(">#-* ").strip()):
            if p:
                unites.append((no, p))
    fin_de_paragraphe()
    return out


def lint(text, regles, corriger=False):
    """Renvoie (violations, texte corrigé)."""
    lignes = text.replace("\r\n", "\n").split("\n")
    motifs, viol, sortie = _compiler(regles), [], []
    for no, l in enumerate(lignes, 1):
        citation = regles.get("ignorer_citations", True) and l.lstrip().startswith(">")
        vue = _masque(l)
        if regles.get("tirets_longs", True):
            for m in TIRETS.finditer(vue):
                viol.append({"ligne": no, "niveau": "dur", "message": "tiret long, demi-tiret ou double tiret",
                             "extrait": l[max(0, m.start() - 15):m.end() + 15], "corrige": corriger and not citation})
        for rx, msg, niveau, rempl in motifs:
            for m in rx.finditer(vue):
                viol.append({"ligne": no, "niveau": niveau, "message": msg, "extrait": m.group(0),
                             "corrige": bool(corriger and rempl is not None and not citation)})
        if corriger and not citation:
            if regles.get("tirets_longs", True):
                l = _remplacer(l, TIRETS, regles.get("remplacement_tiret", ", "))
            for rx, _, _, rempl in motifs:
                if rempl is not None:
                    l = _remplacer(l, rx, rempl)
        sortie.append(l)
    viol += _anaphores(lignes, regles.get("anaphore", {}))
    return sorted(viol, key=lambda v: v["ligne"]), "\n".join(sortie)


def _remplacer(ligne, rx, rempl):
    """Remplace hors des zones URL et code."""
    vue, morceaux, pos = _masque(ligne), [], 0
    for m in rx.finditer(vue):
        morceaux += [ligne[pos:m.start()], rempl]
        pos = m.end()
    return "".join(morceaux) + ligne[pos:]


def restantes(viol):
    return [v for v in viol if v["niveau"] == "dur" and not v.get("corrige")]


def selftest():
    regles = {"tirets_longs": True,
              "mots_interdits": [{"mot": "focus", "remplacer_par": "attention"}, "challenge"],
              "motifs_interdits": [{"motif": r"\bn'(?:est|es)\s+pas\b[^.!?\n]{1,80}?,\s*(?:c'est|tu es)\b",
                                    "message": "antithèse « pas X, c'est Y »", "niveau": "dur"},
                                   {"motif": r"\bau final\b", "message": "tic oral", "niveau": "alerte"}],
              "anaphore": {"actif": True, "min": 3, "mots_exclus": ["le", "la"]}}
    v, _ = lint("Une phrase propre.\nVoir https://site.fr/a--b et `x--y`.\n", regles)
    assert restantes(v) == [], v
    v, _ = lint("Il vient \u2014 puis part.", regles)
    assert len(restantes(v)) == 1, v
    v, fixe = lint("Garde le focus.", regles, corriger=True)
    assert restantes(v) == [] and fixe == "Garde le attention.", (v, fixe)
    v, _ = lint("Un vrai challenge.", regles, corriger=True)
    assert len(restantes(v)) == 1, "sans remplacement : reste dur"
    v, _ = lint("Ce n'est pas de la faiblesse, c'est de la peur.", regles)
    assert len(restantes(v)) == 1, v
    v, _ = lint("Au final on verra.", regles)
    assert restantes(v) == [] and v[0]["niveau"] == "alerte", v
    v, _ = lint("Tu ouvres. Tu écoutes. Tu attends.", regles)
    assert any("anaphore" in x["message"] for x in v), v
    v, _ = lint("Tu ouvres.\nTu écoutes.\n\nTu attends.", regles)
    assert not any("anaphore" in x["message"] for x in v), "un paragraphe coupe la série"
    v, _ = lint("La porte. La table. La chaise.", regles)
    assert not any("anaphore" in x["message"] for x in v), "mot exclu"
    v, fixe = lint("> Il a dit \u2014 non.", regles, corriger=True)
    assert len(restantes(v)) == 1 and "\u2014" in fixe, "citation signalée, jamais corrigée"
    with tempfile.TemporaryDirectory() as t:
        f = Path(t) / "r.json"
        f.write_text(json.dumps(regles), encoding="utf-8")
        assert charger_regles(str(f)) == regles
    print("selftest OK")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Lint de voix par règles dures")
    ap.add_argument("fichier", help="texte à contrôler, ou « selftest »")
    ap.add_argument("--regles")
    ap.add_argument("--fix", action="store_true", help="applique les remplacements prévus et réécrit le fichier")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    if a.fichier == "selftest":
        return selftest()
    try:
        regles = charger_regles(a.regles)
        p = Path(a.fichier)
        viol, fixe = lint(p.read_text(encoding="utf-8-sig"), regles, a.fix)
    except SystemExit as e:
        print(e)
        return 2
    except (OSError, UnicodeDecodeError) as e:
        print(f"lecture impossible : {e}")
        return 2
    if a.fix:
        p.write_text(fixe, encoding="utf-8", newline="\n")
    reste = restantes(viol)
    if a.json:
        print(json.dumps({"violations": viol, "dures_restantes": len(reste)}, ensure_ascii=False, indent=1))
    else:
        for x in viol:
            etat = "corrigé" if x.get("corrige") else x["niveau"].upper()
            print(f"ligne {x['ligne']} [{etat}] {x['message']} : {x['extrait']!r}")
        print("PROPRE" if not reste else f"{len(reste)} violation(s) dure(s) restante(s)")
    return 1 if reste else 0


if __name__ == "__main__":
    sys.exit(main())
