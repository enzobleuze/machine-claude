#!/usr/bin/env python3
"""rapport-du-matin.py : rassemble les faits de la nuit pour le rapport du matin.

Déterministe d'abord : ce script ne rédige rien. Il compte et range les faits
(tâches qui ont tourné, codes de sortie, alertes du résumé, verdict du gardien), puis
le skill rapport-du-matin demande à Claude d'écrire TL;DR, AUTO, TOI et ALERTE au-dessus.

Il écrit la section entre deux marqueurs dans outputs/brief-matin/AAAA-MM-JJ.md :
le reste du fichier (déjà rédigé par une session ou par Claude) n'est jamais écrasé.

Usage : python scripts/rapport-du-matin.py [--date AAAA-MM-JJ] [--selftest]
Sortie : 0 ; affiche le chemin du rapport.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

DEBUT, FIN = "<!-- FAITS:DEBUT -->", "<!-- FAITS:FIN -->"


def faits(vault: Path, jour: dt.date) -> str:
    journaux = vault / "outputs" / "cron-logs"
    depuis = dt.datetime.combine(jour, dt.time()) - dt.timedelta(hours=12)  # depuis midi la veille
    lignes = ["## Faits de la machine (bruts)", ""]

    taches = []
    for f in sorted((journaux / ".etat").glob("*.json")):
        try:
            e = json.loads(f.read_text(encoding="utf-8"))
            fin = dt.datetime.strptime(e["fin"], "%Y-%m-%d %H:%M:%S")
        except (OSError, ValueError, KeyError):
            continue
        if fin >= depuis:
            taches.append(f"- {e['nom']} : code {e['code']} à {fin:%H:%M}")
    lignes.append(f"**Tâches passées depuis hier midi** : {len(taches)}")
    lignes += taches or ["- aucune"]

    alertes = []
    for d in (jour - dt.timedelta(days=1), jour):
        f = journaux / f"resume-{d:%Y-%m-%d}.log"
        if f.exists():
            for l in f.read_text(encoding="utf-8", errors="replace").splitlines():
                if re.search(r"\[(warn|urgent|SENDFAIL)\]", l):
                    alertes.append(f"- {d:%d/%m} {l.strip()[:240]}")
    lignes += ["", f"**Alertes du résumé (warn, urgent, envois ratés)** : {len(alertes)}"]
    lignes += alertes[-15:] or ["- aucune"]

    g = vault / "outputs" / "gardien" / f"{jour:%Y-%m-%d}.json"
    if not g.exists():
        g = vault / "outputs" / "gardien" / f"{jour - dt.timedelta(days=1):%Y-%m-%d}.json"
    lignes.append("")
    if g.exists():
        try:
            res = json.loads(g.read_text(encoding="utf-8"))
            ko = [r for r in res if r["statut"] not in ("ok", "en_cours")]
            lignes.append(f"**Gardien ({g.stem})** : {len(res) - len(ko)} sur {len(res)} tâches prouvées")
            lignes += [f"- {r['nom']} : {r['detail']}" for r in ko]
        except (OSError, ValueError, KeyError):
            lignes.append("**Gardien** : fichier illisible")
    else:
        lignes.append("**Gardien** : pas encore passé")
    return "\n".join(lignes)


def ecrire(vault: Path, jour: dt.date) -> Path:
    cible = vault / "outputs" / "brief-matin" / f"{jour:%Y-%m-%d}.md"
    cible.parent.mkdir(parents=True, exist_ok=True)
    bloc = f"{DEBUT}\n{faits(vault, jour)}\n{FIN}"
    texte = cible.read_text(encoding="utf-8") if cible.exists() else f"# Rapport du matin : {jour:%d/%m}\n\n"
    if DEBUT in texte and FIN in texte:
        texte = re.sub(re.escape(DEBUT) + r".*?" + re.escape(FIN), lambda _: bloc, texte, flags=re.S)
    else:
        texte = texte.rstrip() + "\n\n" + bloc + "\n"
    cible.write_text(texte, encoding="utf-8")
    return cible


def selftest() -> int:
    with tempfile.TemporaryDirectory() as d:
        v = Path(d)
        j = v / "outputs" / "cron-logs"
        (j / ".etat").mkdir(parents=True)
        (j / ".etat" / "jardinier.json").write_text(json.dumps({"nom": "jardinier", "fin": "2030-01-10 03:00:00", "code": 0}))
        (j / ".etat" / "ancienne.json").write_text(json.dumps({"nom": "ancienne", "fin": "2030-01-01 03:00:00", "code": 0}))
        (j / "resume-2030-01-10.log").write_text("03:00:01 [ok] jardinier | fait\n04:00:00 [warn] sauvegarde en échec | x\n", encoding="utf-8")
        jour = dt.date(2030, 1, 10)
        p = ecrire(v, jour)
        p.write_text("# Rapport\n\n## TL;DR\nécrit par Claude\n\n" + p.read_text(encoding="utf-8").split("\n\n", 1)[1], encoding="utf-8")
        ecrire(v, jour)  # deuxième passage : remplace le bloc, garde le texte rédigé
        t = p.read_text(encoding="utf-8")
        assert "écrit par Claude" in t and t.count(DEBUT) == 1, t
        assert "jardinier : code 0" in t and "ancienne" not in t and "sauvegarde en échec" in t, t
    print("selftest rapport-du-matin : OK")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--vault", default=os.environ.get("VAULT", str(Path(__file__).resolve().parents[1])))
    ap.add_argument("--date", default=dt.date.today().isoformat())
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        sys.exit(selftest())
    print(ecrire(Path(a.vault), dt.date.fromisoformat(a.date)))
