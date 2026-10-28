#!/usr/bin/env python3
"""sauvegarde-git.py : commit + push du vault vers un dépôt GitHub PRIVÉ, robuste aux tâches qui écrivent en même temps.

Ce qu'il fait, dans l'ordre :
  1. refuse de tourner si un fichier de secret est suivi par git (garde-fou)
  2. retire un verrou index.lock orphelin (plus de 10 minutes)
  3. git add -A puis commit « Sauvegarde auto AAAA-MM-JJ HH:MM » s'il y a du changement
  4. pull --rebase --autostash puis push, 3 essais
  5. écrit outputs/.derniere-sauvegarde-git-ok (un gardien peut vérifier sa date)
Jamais de --force, jamais de réécriture de l'historique.

Usage :
    python scripts/sauvegarde-git.py           sauvegarde
    python scripts/sauvegarde-git.py --verif   seulement le garde-fou secrets
Le jeton GitHub n'est jamais écrit dans .git/config : utilise « gh auth login »
(gestionnaire d'identifiants) ou SSH. Codes : 0 ok, 1 échec, 3 secret suivi par git.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import subprocess
import sys
import time
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
SECRET = re.compile(r"(^|/)(secrets/|[^/]*\.env(\.[^/]*)?$|[^/]*\.pem$|[^/]*\.key$|credentials[^/]*\.json$|service-account[^/]*\.json$)", re.I)


def git(*args: str, ok: bool = False) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", *args], cwd=VAULT, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if r.returncode != 0 and not ok:
        raise RuntimeError(f"git {' '.join(args)} : {(r.stderr or r.stdout).strip()[-400:]}")
    return r


def secrets_suivis() -> list[str]:
    """Fichiers de secrets déjà suivis, ou qui le seraient au prochain « git add -A »."""
    # -z : chemins bruts séparés par NUL (sans -z, git met entre guillemets les chemins accentués et le motif rate)
    suivis = git("ls-files", "-z").stdout.split("\0")
    entrants = git("ls-files", "-z", "--others", "--exclude-standard").stdout.split("\0")
    return sorted({f for f in suivis + entrants if SECRET.search(f)})


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--verif", action="store_true")
    a = ap.parse_args()
    if not (VAULT / ".git").exists():
        print("Pas de dépôt git ici : lance d'abord « git init ».", file=sys.stderr)
        return 1
    lock = VAULT / ".git" / "index.lock"
    if lock.exists() and time.time() - lock.stat().st_mtime > 600:
        lock.unlink()  # verrou laissé par un git planté : sans ça, plus aucune sauvegarde ne passe
        print("Verrou git orphelin retiré.")
    fuite = secrets_suivis()
    if fuite:
        print("STOP : des fichiers de secrets seraient envoyés sur GitHub :\n  " + "\n  ".join(fuite), file=sys.stderr)
        print("Ajoute-les au .gitignore puis « git rm --cached <fichier> ». Ne pousse rien avant.", file=sys.stderr)
        return 3
    if a.verif:
        print("Aucun secret suivi par git.")
        return 0
    git("add", "-A")
    if git("diff", "--cached", "--quiet", ok=True).returncode != 0:
        git("commit", "-q", "-m", f"Sauvegarde auto {dt.datetime.now():%Y-%m-%d %H:%M}")
        print("Commit fait.")
    else:
        print("Rien de neuf à commiter.")
    if not git("remote", ok=True).stdout.strip():
        print("Aucun dépôt distant : commit local seulement. Branche GitHub avec « gh repo create --private ».", file=sys.stderr)
        return 1
    for essai in range(1, 4):
        git("pull", "--rebase", "--autostash", "-q", ok=True)
        r = git("push", "-q", ok=True)
        if r.returncode == 0:
            marque = VAULT / "outputs" / ".derniere-sauvegarde-git-ok"
            marque.parent.mkdir(parents=True, exist_ok=True)
            marque.write_text(dt.datetime.now().isoformat(timespec="seconds"), encoding="utf-8")
            print("Poussé sur GitHub.")
            return 0
        print(f"Push refusé (essai {essai}) : {r.stderr.strip()[-200:]}", file=sys.stderr)
        time.sleep(10 * essai)
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
