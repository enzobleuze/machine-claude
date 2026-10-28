#!/usr/bin/env python3
"""sauvegarde-drive.py : copie de nuit du vault vers un stockage en ligne avec rclone, plus un coffre chiffré.

Deux envois :
  A. miroir lisible du vault -> <distant>:Sauvegardes/01-vault        (sans .git ni secrets, voir filtre)
     tout fichier modifié ou supprimé part d'abord dans 04-versions/AAAA-MM-JJ_HHMM/ (rien ne se perd)
  B. coffre chiffré       -> <coffre>:                                (~/.claude : mémoire, skills, secrets)
Puis purge les dossiers de versions (miroir et coffre) plus vieux que --garde jours (par leur NOM, jamais autre chose)
et écrit outputs/.derniere-sauvegarde-drive-ok.

Prérequis (une fois, guidé par le skill) : rclone installé, un distant OAuth (ex. « gdrive »),
un distant chiffré « crypt » posé dessus (ex. « coffre »). Voir le SKILL.md.

Usage :
    python scripts/sauvegarde-drive.py --distant gdrive --coffre coffre
    python scripts/sauvegarde-drive.py --distant gdrive --essai      (rclone --dry-run, rien n'est envoyé)
Options : --garde 730  --filtre scripts/filtre-sauvegarde.txt
Codes : 0 ok, 1 échec d'un envoi, 2 rclone absent.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
RACINE = "Sauvegardes"


def rclone(rc: str, *args: str, essai: bool) -> int:
    cmd = [rc, *args, "--transfers", "4", "--retries", "3", "--log-level", "NOTICE"] + (["--dry-run"] if essai else [])
    print("$", " ".join(cmd))
    return subprocess.run(cmd).returncode


def purger(rc: str, base: str, garde: int, essai: bool) -> None:
    r = subprocess.run([rc, "lsf", "--dirs-only", base], capture_output=True, text=True)
    limite = dt.date.today() - dt.timedelta(days=garde)
    for nom in r.stdout.split():
        try:
            jour = dt.date.fromisoformat(nom.strip("/")[:10])
        except ValueError:
            continue  # un dossier au nom inattendu n'est jamais purgé
        if jour < limite:
            rclone(rc, "purge", f"{base}/{nom.strip('/')}", essai=essai)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--distant", required=True)
    ap.add_argument("--coffre")
    ap.add_argument("--garde", type=int, default=730)
    ap.add_argument("--filtre", type=Path, default=VAULT / "scripts" / "filtre-sauvegarde.txt")
    ap.add_argument("--essai", action="store_true")
    a = ap.parse_args()
    rc = shutil.which("rclone")
    if not rc:
        print("rclone introuvable. Windows : winget install Rclone.Rclone ; Mac : brew install rclone", file=sys.stderr)
        return 2
    if not a.filtre.exists():
        print(f"Filtre absent : {a.filtre} (sans lui les secrets partiraient en clair). Arrêt.", file=sys.stderr)
        return 1
    horo = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    echecs = 0
    echecs += rclone(rc, "sync", str(VAULT), f"{a.distant}:{RACINE}/01-vault", "--exclude-from", str(a.filtre),
                     "--backup-dir", f"{a.distant}:{RACINE}/04-versions/{horo}", essai=a.essai) != 0
    if a.coffre:
        claude = Path.home() / ".claude"
        echecs += rclone(rc, "sync", str(claude), f"{a.coffre}:claude",
                         "--exclude", "projects/**/*.jsonl", "--exclude", "cache/**", "--exclude", "logs/**",
                         "--backup-dir", f"{a.coffre}:versions/{horo}", essai=a.essai) != 0
    purger(rc, f"{a.distant}:{RACINE}/04-versions", a.garde, a.essai)
    if a.coffre:
        purger(rc, f"{a.coffre}:versions", a.garde, a.essai)
    if not echecs and not a.essai:
        m = VAULT / "outputs" / ".derniere-sauvegarde-drive-ok"
        m.parent.mkdir(parents=True, exist_ok=True)
        m.write_text(dt.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
    print("Sauvegarde OK." if not echecs else f"{echecs} envoi(s) en échec.")
    return 1 if echecs else 0


if __name__ == "__main__":
    sys.exit(main())
