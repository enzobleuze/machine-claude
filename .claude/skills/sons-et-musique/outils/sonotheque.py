"""sonotheque.py : le catalogue des sons de la marque, chaque son avec sa licence, ses plateformes permises et ses mesures.

  python sonotheque.py ajouter fichier.wav --type bruitage --role whoosh --licence CC0 --source https://... [--attribution "..."]
                       [--plateformes toutes|youtube,instagram] [--humeurs calme,chaud] [--notes "..."]
  python sonotheque.py lister [--type musique] [--role pop]
  python sonotheque.py verifier                      fichiers présents, licence et plateformes notées (sortie 1 sinon)
  python sonotheque.py choisir --type musique [--humeur auto] [--plateforme youtube] [--usage ma-video]
  python sonotheque.py bannir <id> --notes "pourquoi"   bannit CE fichier seulement, jamais toute sa famille
  python sonotheque.py --test

Catalogue : bibliotheque/sons/catalogue-son.json (trouvé depuis le dossier courant, ou --catalogue).
Rôles des bruitages : whoosh, clic, pop, tick, notification, impact, riser, frappe. Une musique a le rôle « musique ».
« --humeur auto » prend les mots d'ambiance de la charte (bibliotheque/marque/charte-jetons.json, champ « mots »).
Une musique déjà prise parmi les 5 dernières n'est pas reprise. Un son sans licence notée n'est jamais choisi.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path[:0] = [str(ICI), str(ICI.parents[1] / "montage-video-code" / "outils")]
import commun as C  # noqa: E402

REL = "bibliotheque/sons/catalogue-son.json"
ROLES = ("whoosh", "clic", "pop", "tick", "notification", "impact", "riser", "frappe", "musique")
ECART_MIN = {"frappe": .025, "tick": .06, "clic": .08, "whoosh": .35, "notification": .6, "pop": 1.5, "impact": 1.5, "riser": 8.0}
RECENTS = 5


def chemin_catalogue(c=None) -> Path:
    return Path(c) if c else (C.trouver(REL) or Path(REL))


def lire(cat: Path) -> dict:
    return json.loads(cat.read_text(encoding="utf-8")) if cat.exists() else {"sons": [], "journal": []}


def ecrire(cat: Path, d: dict) -> None:
    cat.parent.mkdir(parents=True, exist_ok=True)
    cat.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")


def mesurer(f) -> dict:
    """Durée, instant du pic (s) et niveau des parties audibles (dB), pour caler un bruitage sur son pic."""
    env = C.enveloppe(f)
    if not env:
        return {"duree": 0.0, "pic": 0.0, "niveau_db": -90.0}
    haut = max(env)
    audibles = [x for x in env if x > haut - 30]
    return {"duree": round(len(env) / 100, 2), "pic": round(env.index(haut) / 100, 2),
            "niveau_db": round(10 * math.log10(sum(10 ** (x / 10) for x in audibles) / len(audibles)), 1)}


def ajouter(cat: Path, fichier, type_, role, licence, source, attribution="", plateformes="toutes", humeurs="", notes="") -> dict:
    if role not in ROLES:
        raise SystemExit(f"rôle inconnu : {role} (au choix : {', '.join(ROLES)})")
    if not licence.strip():
        raise SystemExit("licence obligatoire (CC0, CC BY, licence du service...) : sans elle, le son ne sert jamais.")
    d, f = lire(cat), Path(fichier)
    dest = cat.parent / ("musiques" if type_ == "musique" else role) / f.name
    if f.resolve() != dest.resolve():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dest)
    ident = re.sub(r"[^a-z0-9]+", "-", f.stem.lower()).strip("-")
    d["sons"] = [s for s in d["sons"] if s["id"] != ident]
    s = {"id": ident, "fichier": dest.relative_to(cat.parent).as_posix(), "type": type_, "role": role,
         "humeurs": [h.strip() for h in humeurs.split(",") if h.strip()], "licence": licence, "attribution": attribution,
         "source": source, "plateformes": [p.strip() for p in plateformes.split(",") if p.strip()], "banni": False,
         "notes": notes, **mesurer(dest)}
    d["sons"].append(s)
    ecrire(cat, d)
    return s


def permis(s: dict, plateforme: str | None) -> bool:
    return not s.get("banni") and bool(s.get("licence")) and (not plateforme or "toutes" in s["plateformes"]
                                                              or plateforme in s["plateformes"])


def verifier(cat: Path) -> list[str]:
    pb, d = [], lire(cat)
    for s in d["sons"]:
        if not (cat.parent / s["fichier"]).exists():
            pb.append(f"{s['id']} : fichier absent")
        if not s.get("licence"):
            pb.append(f"{s['id']} : licence absente")
        if not s.get("plateformes"):
            pb.append(f"{s['id']} : plateformes permises absentes")
        if "BY" in s.get("licence", "").upper() and not s.get("attribution"):
            pb.append(f"{s['id']} : licence avec attribution, texte d'attribution absent")
    return pb


def choisir(cat: Path, type_="musique", role=None, humeur=None, plateforme=None, usage="", exclus=()) -> dict | None:
    """Le son le mieux accordé à l'humeur, permis sur la plateforme, pas parmi les 5 derniers de son rôle."""
    d = lire(cat)
    voulu = set(C.charte().get("mots", [])) if humeur == "auto" else {humeur} if humeur else set()
    cands = [s for s in d["sons"] if s["type"] == type_ and (not role or s["role"] == role) and permis(s, plateforme)
             and s["id"] not in exclus]
    recents = [j["id"] for j in d["journal"] if any(s["id"] == j["id"] for s in cands)][-RECENTS:]
    neufs = [s for s in cands if s["id"] not in recents] or cands
    if not neufs:
        return None
    s = max(neufs, key=lambda s: (len(voulu & set(s["humeurs"])), -recents.count(s["id"]), s["id"]))
    if usage:
        d["journal"].append({"id": s["id"], "date": time.strftime("%Y-%m-%d"), "usage": usage})
        ecrire(cat, d)
    return s


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        cat = Path(tmp) / REL
        for nom, freq in (("calme-un", 330), ("vif-deux", 550), ("calme-trois", 440)):
            C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"sine=frequency={freq}:duration=2", Path(tmp) / f"{nom}.wav"])
            ajouter(cat, Path(tmp) / f"{nom}.wav", "musique", "musique", "CC0", "https://exemple.org", humeurs=nom.split("-")[0],
                    plateformes="toutes" if nom != "vif-deux" else "instagram")
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='0.8*sin(2*PI*900*t)*exp(-30*abs(t-0.12))':d=0.4",
               Path(tmp) / "whoosh-a.wav"])
        w = ajouter(cat, Path(tmp) / "whoosh-a.wav", "bruitage", "whoosh", "CC BY", "https://exemple.org", attribution="Auteur")
        assert 0.08 <= w["pic"] <= 0.16 and abs(w["duree"] - .4) < .05 and w["fichier"] == "whoosh/whoosh-a.wav", w
        assert verifier(cat) == []
        try:
            ajouter(cat, Path(tmp) / "whoosh-a.wav", "bruitage", "whoosh", " ", "x")
            raise AssertionError("son sans licence accepté")
        except SystemExit:
            pass
        assert choisir(cat, humeur="calme", plateforme="youtube")["id"].startswith("calme")
        assert choisir(cat, humeur="vif", plateforme="youtube")["id"] != "vif-deux", "licence Instagram seulement sur YouTube"
        pris = [choisir(cat, plateforme="youtube", usage=f"v{k}")["id"] for k in range(4)]
        assert all(a != b for a, b in zip(pris, pris[1:])), pris
        d = lire(cat)
        d["sons"][0]["banni"] = True
        ecrire(cat, d)
        assert all(choisir(cat, plateforme="instagram", usage="x")["id"] != d["sons"][0]["id"] for _ in range(3))
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Catalogue des sons avec licences.")
    ap.add_argument("action", nargs="?", choices=("ajouter", "lister", "verifier", "choisir", "bannir"))
    ap.add_argument("cible", nargs="?")
    ap.add_argument("--catalogue")
    ap.add_argument("--type", default="bruitage")
    ap.add_argument("--role")
    ap.add_argument("--licence", default="")
    ap.add_argument("--source", default="")
    ap.add_argument("--attribution", default="")
    ap.add_argument("--plateformes", default="toutes")
    ap.add_argument("--humeurs", default="")
    ap.add_argument("--humeur")
    ap.add_argument("--plateforme")
    ap.add_argument("--usage", default="")
    ap.add_argument("--notes", default="")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    cat = chemin_catalogue(a.catalogue)
    if a.test:
        auto_test()
    elif a.action == "ajouter" and a.cible:
        print(json.dumps(ajouter(cat, a.cible, a.type, a.role or ("musique" if a.type == "musique" else ""), a.licence, a.source,
                                 a.attribution, a.plateformes, a.humeurs, a.notes), ensure_ascii=False, indent=1))
    elif a.action == "lister":
        for s in lire(cat)["sons"]:
            if (not a.role or s["role"] == a.role) and ("--type" not in sys.argv or s["type"] == a.type):
                print(f"{s['id']:30} {s['role']:12} {s['licence']:10} {','.join(s['plateformes']):20} {'BANNI' if s.get('banni') else ''}")
    elif a.action == "verifier":
        pb = verifier(cat)
        print("\n".join(pb) or f"Catalogue OK ({len(lire(cat)['sons'])} sons).")
        sys.exit(1 if pb else 0)
    elif a.action == "choisir":
        s = choisir(cat, a.type, a.role, a.humeur, a.plateforme, a.usage)
        print(cat.parent / s["fichier"] if s else "Aucun son permis pour cette demande.")
        sys.exit(0 if s else 1)
    elif a.action == "bannir" and a.cible:
        d = lire(cat)
        for s in d["sons"]:
            if s["id"] == a.cible:
                s["banni"], s["notes"] = True, a.notes or s["notes"]
        ecrire(cat, d)
        print(f"{a.cible} banni (les autres sons de son rôle restent permis).")
    else:
        ap.print_help()
