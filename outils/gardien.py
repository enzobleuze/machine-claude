#!/usr/bin/env python3
"""gardien.py : vérifie que chaque tâche planifiée a vraiment tourné et que ses sorties existent.

Une tâche peut afficher « réussi » dans le planificateur sans avoir rien produit. Le gardien
regarde donc les PREUVES : l'état écrit par run-tache.sh et les fichiers que la tâche doit laisser.

Liste attendue : scripts/taches-attendues.json (voir taches-attendues.exemple.json)
  {"taches": [
     {"nom": "sauvegarde", "toutes_les_heures": 26, "sorties": ["outputs/sauvegarde/derniere-ok.txt"]},
     {"nom": "jardinier",  "toutes_les_heures": 26, "sorties": ["outputs/jardinier/{date}/resume.md"]},
     {"nom": "scoreboard", "toutes_les_heures": 170}
  ]}
  {date} = date de la dernière exécution (AAAA-MM-JJ). Les jokers * sont permis.
  "active": false met une tâche de côté sans la retirer de la liste.

Problèmes détectés : jamais tournée, dernière exécution trop vieille, code de sortie en échec,
sortie absente ou plus vieille que la fréquence. Une tâche en cours (verrou récent) n'est pas un problème.

Usage :
  python scripts/gardien.py                 rapport à l'écran + outputs/gardien/AAAA-MM-JJ.json
  python scripts/gardien.py --notifier      en plus : une ligne au résumé ; urgent si une panne dure
  python scripts/gardien.py --selftest      test sur un faux vault temporaire (rien n'est envoyé)
Sortie : 0 tout va bien, 1 au moins un problème, 64 liste attendue illisible.
"""
from __future__ import annotations

import argparse
import datetime as dt
import glob
import json
import os
import sys
import tempfile
from pathlib import Path

CODES_OK = (0, 3)  # 3 = arrêt propre qui reprendra seul (convention run-tache.sh)


def lire_json(chemin: Path, defaut):
    try:
        return json.loads(chemin.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def verifier_tache(vault: Path, t: dict, maintenant: dt.datetime) -> dict:
    nom = t["nom"]
    heures = float(t.get("toutes_les_heures", 26))
    limite = maintenant - dt.timedelta(hours=heures)
    journaux = vault / "outputs" / "cron-logs"
    res = {"nom": nom, "statut": "ok", "detail": ""}

    verrou = journaux / ".verrous" / f"{nom}.lock"
    if verrou.exists() and dt.datetime.fromtimestamp(verrou.stat().st_mtime) > maintenant - dt.timedelta(hours=4):
        res.update(statut="en_cours", detail="verrou présent, la tâche tourne")
        return res

    etat = lire_json(journaux / ".etat" / f"{nom}.json", None)
    if etat:
        fin = dt.datetime.strptime(etat["fin"], "%Y-%m-%d %H:%M:%S")
        code = int(etat.get("code", 1))
    else:  # tâche lancée sans run-tache.sh : on se rabat sur le journal le plus récent
        logs = sorted(journaux.glob(f"{nom}-*.log"), key=lambda p: p.stat().st_mtime)
        if not logs:
            res.update(statut="jamais", detail="aucun état ni journal : la tâche n'a jamais tourné")
            return res
        fin = dt.datetime.fromtimestamp(logs[-1].stat().st_mtime)
        code = 0
    res["derniere"] = fin.strftime("%Y-%m-%d %H:%M")

    if fin < limite:
        res.update(statut="trop_vieux", detail=f"dernière exécution {res['derniere']}, attendue toutes les {heures:g} h")
        return res
    if code not in CODES_OK:
        res.update(statut="echec", detail=f"code de sortie {code}, voir {etat.get('journal', 'le journal')}")
        return res

    for motif in t.get("sorties", []):
        chemin = motif.replace("{date}", fin.strftime("%Y-%m-%d"))
        trouves = glob.glob(str(vault / chemin))
        if not trouves:
            res.update(statut="sortie_absente", detail=f"{chemin} introuvable")
            return res
        recent = max(os.path.getmtime(p) for p in trouves)
        if dt.datetime.fromtimestamp(recent) < limite:
            res.update(statut="sortie_vieille", detail=f"{chemin} n'a pas bougé depuis {heures:g} h")
            return res
    return res


def verifier(vault: Path, config: dict, maintenant: dt.datetime | None = None) -> list[dict]:
    maintenant = maintenant or dt.datetime.now()
    return [verifier_tache(vault, t, maintenant) for t in config.get("taches", []) if t.get("active", True)]


def mettre_a_jour_serie(vault: Path, resultats: list[dict], aujourd_hui: str) -> dict:
    """Compte les jours de suite où chaque tâche est en panne (un passage du gardien par jour)."""
    chemin = vault / "outputs" / "gardien" / "serie.json"
    serie = lire_json(chemin, {})
    for r in resultats:
        ancien = serie.get(r["nom"], {"jours": 0, "dernier": ""})
        if r["statut"] in ("ok", "en_cours"):
            serie.pop(r["nom"], None)
        elif ancien["dernier"] != aujourd_hui:
            serie[r["nom"]] = {"jours": ancien["jours"] + 1, "dernier": aujourd_hui}
    chemin.parent.mkdir(parents=True, exist_ok=True)
    chemin.write_text(json.dumps(serie, ensure_ascii=False, indent=1), encoding="utf-8")
    return serie


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Gardien des tâches planifiées")
    ap.add_argument("--vault", default=os.environ.get("VAULT", str(Path(__file__).resolve().parents[1])))
    ap.add_argument("--liste", default=None, help="chemin de taches-attendues.json")
    ap.add_argument("--notifier", action="store_true")
    ap.add_argument("--escalade-jours", type=int, default=3, help="jours de panne avant un urgent")
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return selftest()

    vault = Path(a.vault)
    liste = Path(a.liste) if a.liste else vault / "scripts" / "taches-attendues.json"
    config = lire_json(liste, None)
    if not config or "taches" not in config:
        print(f"Liste attendue illisible : {liste}", file=sys.stderr)
        return 64

    resultats = verifier(vault, config)
    jour = dt.date.today().isoformat()
    sortie = vault / "outputs" / "gardien" / f"{jour}.json"
    sortie.parent.mkdir(parents=True, exist_ok=True)
    sortie.write_text(json.dumps(resultats, ensure_ascii=False, indent=1), encoding="utf-8")

    problemes = [r for r in resultats if r["statut"] not in ("ok", "en_cours")]
    for r in resultats:
        print(f"{'OK ' if r not in problemes else 'KO '} {r['nom']:<24} {r['statut']:<15} {r['detail']}")
    serie = mettre_a_jour_serie(vault, resultats, jour)

    if a.notifier:
        sys.path.insert(0, str(Path(__file__).resolve().parent))
        from notify import notifier
        if problemes:
            notifier("warn", f"Gardien : {len(problemes)} tâche(s) à réparer",
                     "; ".join(f"{r['nom']} ({r['detail']})" for r in problemes))
            longues = [n for n, s in serie.items() if s["jours"] >= a.escalade_jours]
            if longues:
                notifier("urgent", "Machine en panne depuis plusieurs jours",
                         f"{', '.join(longues)} ne tourne plus depuis {a.escalade_jours} jours ou plus. "
                         "Ouvre une session Claude et dis : répare la machine.")
        else:
            notifier("ok", "Gardien", f"{len(resultats)} tâches vérifiées, tout a tourné")
    return 1 if problemes else 0


def selftest() -> int:
    maintenant = dt.datetime(2030, 1, 10, 11, 0, 0)
    with tempfile.TemporaryDirectory() as d:
        v = Path(d)
        j = v / "outputs" / "cron-logs"
        (j / ".etat").mkdir(parents=True)
        (j / ".verrous").mkdir()

        def etat(nom, fin, code=0):
            (j / ".etat" / f"{nom}.json").write_text(json.dumps({"nom": nom, "fin": fin, "code": code, "debut": fin}))

        etat("bonne", "2030-01-10 03:00:00")
        sortie = v / "outputs" / "bonne" / "2030-01-10"
        sortie.mkdir(parents=True)
        (sortie / "resume.md").write_text("ok")
        os.utime(sortie / "resume.md", (maintenant.timestamp(), maintenant.timestamp()))
        etat("vieille", "2030-01-07 03:00:00")
        etat("cassee", "2030-01-10 03:00:00", code=1)
        etat("quota", "2030-01-10 03:00:00", code=3)
        etat("sans-sortie", "2030-01-10 03:00:00")
        (j / ".verrous" / "longue.lock").mkdir()
        os.utime(j / ".verrous" / "longue.lock", (maintenant.timestamp(), maintenant.timestamp()))

        config = {"taches": [
            {"nom": "bonne", "toutes_les_heures": 26, "sorties": ["outputs/bonne/{date}/resume.md"]},
            {"nom": "vieille", "toutes_les_heures": 26},
            {"nom": "cassee", "toutes_les_heures": 26},
            {"nom": "quota", "toutes_les_heures": 26},
            {"nom": "sans-sortie", "toutes_les_heures": 26, "sorties": ["outputs/rien/*.md"]},
            {"nom": "longue", "toutes_les_heures": 26},
            {"nom": "jamais", "toutes_les_heures": 26},
            {"nom": "rangee", "active": False},
        ]}
        got = {r["nom"]: r["statut"] for r in verifier(v, config, maintenant)}
        attendu = {"bonne": "ok", "vieille": "trop_vieux", "cassee": "echec", "quota": "ok",
                   "sans-sortie": "sortie_absente", "longue": "en_cours", "jamais": "jamais"}
        assert got == attendu, f"selftest : {got} au lieu de {attendu}"

        res = [{"nom": "cassee", "statut": "echec"}, {"nom": "bonne", "statut": "ok"}]
        mettre_a_jour_serie(v, res, "2030-01-10")
        mettre_a_jour_serie(v, res, "2030-01-10")  # même jour : pas de double compte
        s = mettre_a_jour_serie(v, res, "2030-01-11")
        assert s == {"cassee": {"jours": 2, "dernier": "2030-01-11"}}, s
    print("selftest gardien : OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
