"""porte_board.py : empreinte d'un texte et porte du board (skill board-textes). Python 3.8+, bibliothèque standard seule.

  python porte_board.py extraire <texte> <sortie.txt>
      Écrit le texte que le public lit (celui que le board juge), une ligne par élément.
  python porte_board.py empreinte <texte>
      12 premiers caractères du sha256 du texte extrait. Même texte, même empreinte (fins de ligne normalisées).
  python porte_board.py verifier <texte> <board.md> [--config board-config.json]
      La porte. Sort 0 seulement si board.md porte un titre « ## Verdict : VERT... », une ligne
      « Empreinte du texte final : <12 caractères> » égale à l'empreinte du texte ACTUEL, et les sièges requis.
      Codes : 0 passe ; 1 texte modifié depuis le verdict, ou verdict autre que VERT ; 2 board.md illisible ;
      3 siège requis manquant. Priorité : 2, puis 1, puis 3.
  python porte_board.py selftest

Formats lus :
  .json  toutes les chaînes, dans l'ordre, sauf les valeurs des clés de « cles_non_publiques » (réglages, chemins, dates).
  .md    le frontmatter YAML de tête est retiré, sauf ses lignes « frontmatter_public » (objet d'un email, titre...).
  autre  le fichier tel quel.

Configuration (facultative) : --config, sinon la variable BOARD_CONFIG, sinon board-config.json dans le dossier courant,
sinon à côté de ce script. Sans configuration, aucun siège n'est exigé (seuls le verdict et l'empreinte comptent).
  {"requis": ["Expert fond", "Méthode", "Bibliothécaire", "Client idéal"],
   "joues_ou_sans_objet": ["Expert couple"],
   "cles_non_publiques": ["style", "image", "date"],
   "frontmatter_public": ["subject", "title", "preview"]}
"""
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from pathlib import Path

CLES_NON_PUBLIQUES = {"style", "color", "couleur", "size", "taille", "position", "font", "police", "type", "mode", "layout",
                      "image", "src", "ratio", "align", "fond", "id", "slug", "date", "note", "statut", "source", "modele",
                      "_info", "maj_le"}
FRONTMATTER_PUBLIC = {"subject", "objet", "preview", "preheader", "title", "titre"}
FRONTMATTER = re.compile(r"\A---[ \t]*\n((?:.*?\n)?)---[ \t]*(?:\n|\Z)", re.S)
YAML_LIGNE = re.compile(r"(?:\s*#.*|[A-Za-z_][\w.\-]*\s*:(?:\s.*)?|\s+\S.*|-(?:\s.*)?)?")
CLE_YAML = re.compile(r"([A-Za-z_][\w.\-]*)\s*:")


def charger_config(chemin=None):
    for c in (chemin, os.environ.get("BOARD_CONFIG"), "board-config.json", Path(__file__).with_name("board-config.json")):
        if c and Path(c).is_file():
            try:
                return json.loads(Path(c).read_text(encoding="utf-8-sig"))
            except json.JSONDecodeError as e:
                sys.exit(f"configuration illisible ({c}) : {e}")
    return {}


def _feuilles(o, exclues):
    if isinstance(o, str):
        if o.strip():
            yield o.strip()
    elif isinstance(o, dict):
        for k, v in o.items():
            if k not in exclues:
                yield from _feuilles(v, exclues)
    elif isinstance(o, list):
        for v in o:
            yield from _feuilles(v, exclues)


def texte(src, config=None):
    """Le texte que le public lit, normalisé (UTF-8, sans BOM, fins de ligne LF, une fin de ligne finale)."""
    config = config or {}
    p = Path(src)
    brut = p.read_text(encoding="utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
    if p.suffix.lower() == ".json":
        exclues = CLES_NON_PUBLIQUES | set(config.get("cles_non_publiques", []))
        return "\n".join(_feuilles(json.loads(brut), exclues)) + "\n"
    if p.suffix.lower() == ".md":
        m = FRONTMATTER.match(brut)
        # deux « --- » en tête ne font un frontmatter que si tout l'entre-deux ressemble à du YAML
        if m and all(YAML_LIGNE.fullmatch(l) for l in m.group(1).splitlines()):
            publiques = FRONTMATTER_PUBLIC | set(config.get("frontmatter_public", []))
            garde, tete = False, []
            for ligne in m.group(1).splitlines():
                k = CLE_YAML.match(ligne)
                if k:
                    garde = k.group(1) in publiques
                if garde and ligne.strip():
                    tete.append(ligne.rstrip())
            corps = brut[m.end():].strip("\n")
            return "\n".join(tete + [corps]).strip("\n") + "\n"
    return brut.strip("\n") + "\n"


def empreinte(src, config=None):
    return hashlib.sha256(texte(src, config).encode("utf-8")).hexdigest()[:12]


def _n(s):
    """Minuscules sans accents."""
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn").lower()


def _ligne(board, etiquette):
    """Contenu normalisé de la ligne « <étiquette> : ... », sans parenthèses ; None si absente."""
    for l in board.splitlines():
        m = re.search(_n(etiquette) + r"[\s*_]*:(.*)$", _n(l))
        if m:
            s = m.group(1)
            while (t := re.sub(r"\([^()]*\)", " ", s)) != s:  # parenthèses imbriquées
                s = t
            return re.split(r"\|", s)[0]
    return None


def _present(siege, ligne):
    return bool(re.search(rf"(?<!\w){re.escape(_n(siege))}(?!\w)", ligne or ""))


def sieges_manquants(board, config):
    joues = _ligne(board, "sieges joues")
    sans_objet = _ligne(board, "sieges sans objet") or ""
    manque = []
    if (config.get("requis") or config.get("joues_ou_sans_objet")) and joues is None:
        print("REFUS : board.md n'a pas de ligne « Sièges joués : ... ».")
    manque += [s for s in config.get("requis", []) if not _present(s, joues)]
    manque += [s for s in config.get("joues_ou_sans_objet", []) if not (_present(s, joues) or _present(s, sans_objet))]
    return manque


def verifier(src, board_md, config=None):
    config = config or {}
    b = Path(board_md).read_text(encoding="utf-8-sig")
    h = re.search(r"Empreinte du texte final\s*:\s*`?([0-9a-f]{12})", b)
    v = re.search(r"(?m)^#+\s*Verdict\s*:\s*(.+?)\s*$", b)
    if not (h and v):
        print("board.md illisible : il faut « Empreinte du texte final : <12 caractères> » et un titre « ## Verdict : ... ».")
        return 2
    actuelle = empreinte(src, config)
    vert = _n(v.group(1)).strip("* ").startswith("vert")
    print(f"empreinte actuelle {actuelle} | board.md {h.group(1)} | verdict : {v.group(1)}")
    if actuelle != h.group(1):
        print("REFUS : le texte a changé depuis le verdict. Nouvelle séance du board sur les phrases changées.")
    if not vert:
        print("REFUS : le verdict n'est pas VERT.")
    manque = sieges_manquants(b, config)
    if manque:
        print("REFUS : siège requis manquant : " + ", ".join(manque))
    if actuelle != h.group(1) or not vert:
        return 1
    if manque:
        return 3
    print("PORTE OUVERTE")
    return 0


def selftest():
    import contextlib
    import io
    cfg = {"requis": ["Expert fond", "Client idéal"], "joues_ou_sans_objet": ["Expert couple"]}
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        a, b = t / "a.txt", t / "b.txt"
        a.write_bytes("Un\r\nDeux".encode("utf-8"))
        b.write_bytes("﻿Un\nDeux\n".encode("utf-8"))
        assert empreinte(a) == empreinte(b), "fins de ligne et BOM"
        m1, m2 = t / "m1.md", t / "m2.md"
        m1.write_text("---\nsubject: Ton bilan\nid_outil: 123\n---\nBonjour.\n", encoding="utf-8")
        m2.write_text("---\nsubject: Ton bilan\nid_outil: 999\n---\nBonjour.\n", encoding="utf-8")
        assert empreinte(m1) == empreinte(m2), "clé technique du frontmatter ignorée"
        assert texte(m1) == "subject: Ton bilan\nBonjour.\n", texte(m1)
        m2.write_text("---\nsubject: URGENT ton bilan\nid_outil: 999\n---\nBonjour.\n", encoding="utf-8")
        assert empreinte(m1) != empreinte(m2), "l'objet compte"
        m2.write_text("---\nUne vraie phrase.\n---\nBonjour.\n", encoding="utf-8")
        assert texte(m2).startswith("---\nUne vraie phrase."), "faux frontmatter gardé"
        j = t / "c.json"
        j.write_text(json.dumps({"slides": [{"titre": "T", "style": "x"}, {"texte": "Fin"}], "date": "1/1"}), encoding="utf-8")
        assert texte(j) == "T\nFin\n", texte(j)
        board = t / "board.md"

        def porte(sieges, verdict="VERT", fichier=a, config=cfg):
            board.write_text(f"# Board\nEmpreinte du texte final : {empreinte(a, config)}\n{sieges}\n## Verdict : {verdict}\n",
                             encoding="utf-8")
            with contextlib.redirect_stdout(io.StringIO()):
                return verifier(fichier, board, config)
        tous = "Sièges joués : Expert fond, Expert couple, Client idéal, Voix"
        assert porte(tous) == 0, "board complet"
        assert porte(tous, config={}) == 0, "sans configuration"
        assert porte("sieges joues : EXPERT FOND, client ideal\nSièges sans objet : Expert couple (rien à conseiller)") == 0
        assert porte("Sièges joués : Expert fond, Client idéal (lu avec Expert couple)") == 3, "parenthèse ne compte pas"
        assert porte("Sièges joués : Expert fond, Expert couple") == 3, "client idéal manquant"
        assert porte(tous, verdict="À TRANCHER") == 1, "verdict pas VERT"
        assert porte(tous, fichier=b) == 0, "même texte, autre fichier"
        a.write_text("Un\nDeux modifié\n", encoding="utf-8")
        board.write_text(f"Empreinte du texte final : {empreinte(b)}\n{tous}\n## Verdict : VERT\n", encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            assert verifier(a, board, cfg) == 1, "texte modifié après le verdict"
            board.write_text("rien\n", encoding="utf-8")
            assert verifier(a, board, cfg) == 2, "illisible"
            board.write_bytes(b"\xef\xbb\xbf" + f"## Verdict : VERT\nEmpreinte du texte final : {empreinte(a)}\n{tous}\n".encode())
            assert verifier(a, board, cfg) == 0, "board.md avec BOM"
    print("selftest OK")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Empreinte et porte du board des textes")
    sub = ap.add_subparsers(dest="cmd", required=True)
    e = sub.add_parser("extraire")
    e.add_argument("source")
    e.add_argument("sortie")
    e.add_argument("--config")
    sub.add_parser("empreinte").add_argument("source")
    v = sub.add_parser("verifier")
    v.add_argument("source")
    v.add_argument("board")
    v.add_argument("--config")
    sub.add_parser("selftest")
    a = ap.parse_args()
    try:
        if a.cmd == "selftest":
            return selftest()
        config = charger_config(getattr(a, "config", None))
        if a.cmd == "extraire":
            Path(a.sortie).parent.mkdir(parents=True, exist_ok=True)
            Path(a.sortie).write_text(texte(a.source, config), encoding="utf-8", newline="\n")
            print(f"{a.sortie} ({empreinte(a.source, config)})")
            return 0
        if a.cmd == "empreinte":
            print(empreinte(a.source, config))
            return 0
        return verifier(a.source, a.board, config)
    except FileNotFoundError as err:
        print(f"fichier introuvable : {err.filename}")
        return 2
    except (UnicodeDecodeError, json.JSONDecodeError) as err:
        print(f"fichier illisible : {err}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
