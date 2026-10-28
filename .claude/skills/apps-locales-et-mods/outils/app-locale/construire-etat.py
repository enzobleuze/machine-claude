#!/usr/bin/env python3
"""Moteur d'une app locale : construit outputs/<app>/state.json à partir de sections indépendantes.

Chaque section est une fonction qui rend un dict. Une section qui plante est notée en erreur
et n'empêche pas les autres. L'écriture est atomique (fichier temporaire puis remplacement).

  python scripts/<app>/construire-etat.py              construit l'état
  python scripts/<app>/construire-etat.py --test       auto-test

Pour ajouter une section : écris une fonction, ajoute-la dans SECTIONS. Aucune dépendance.
"""
import datetime
import json
import os
import sys
import tempfile

RACINE = os.environ.get("VAULT", os.getcwd())
SORTIE = os.path.join(RACINE, "outputs", os.environ.get("APP_NOM", "mon-app"), "state.json")


# ---- Sections (à adapter) -------------------------------------------------

def section_log():
    """Les 5 dernières entrées de log.md."""
    chemin = os.path.join(RACINE, "log.md")
    if not os.path.exists(chemin):
        return {"entrees": [], "note": "log.md absent"}
    titres = [l.strip()[3:] for l in open(chemin, encoding="utf-8") if l.startswith("## ")]
    return {"entrees": titres[-5:][::-1]}


def section_parking():
    """Nombre d'idées à trier dans le parking."""
    chemin = os.path.join(RACINE, "wiki", "maps", "parking.md")
    if not os.path.exists(chemin):
        return {"a_trier": 0}
    return {"a_trier": sum(1 for l in open(chemin, encoding="utf-8") if l.startswith("- "))}


SECTIONS = {"log": section_log, "parking": section_parking}


# ---- Mécanique (ne change pas) --------------------------------------------

def construire(sections):
    etat = {"construit_le": datetime.datetime.now().isoformat(timespec="seconds"), "sections": {}, "erreurs": {}}
    for nom, fonction in sections.items():
        try:
            etat["sections"][nom] = fonction()
        except Exception as e:  # une section cassée ne casse pas l'app
            etat["erreurs"][nom] = f"{type(e).__name__}: {e}"
    return etat


def ecrire_atomique(chemin, donnees):
    os.makedirs(os.path.dirname(chemin), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(chemin), suffix=".tmp")
    with os.fdopen(fd, "w", encoding="utf-8") as h:
        json.dump(donnees, h, ensure_ascii=False, indent=1)
    os.replace(tmp, chemin)


def auto_test():
    def casse():
        raise RuntimeError("boum")
    e = construire({"bonne": lambda: {"x": 1}, "casse": casse})
    assert e["sections"]["bonne"] == {"x": 1} and "boum" in e["erreurs"]["casse"]
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "a", "state.json")
        ecrire_atomique(p, e)
        assert json.load(open(p, encoding="utf-8"))["sections"]["bonne"]["x"] == 1
    print("ok")


if __name__ == "__main__":
    if "--test" in sys.argv:
        auto_test()
        sys.exit(0)
    etat = construire(SECTIONS)
    ecrire_atomique(SORTIE, etat)
    print(f"{SORTIE} : {len(etat['sections'])} section(s), {len(etat['erreurs'])} erreur(s)")
    sys.exit(1 if etat["erreurs"] else 0)
