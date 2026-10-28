#!/usr/bin/env python3
"""cerveau-check.py : test d'or du moteur de recherche par le sens.

Lit scripts/cerveau-tests.txt, une ligne par test :
    question formulée autrement que la note => wiki/chemin/attendu.md
Lance scripts/cerveau.py sur chaque question et vérifie que la note attendue sort dans
les 5 premiers résultats, et que le mode est bien « sens » (pas le repli mots-clés).

Usage :
    python scripts/cerveau-check.py            sort 0 si tout passe, sinon le nombre d'échecs
    python scripts/cerveau-check.py --top 8
Aucune dépendance en plus de cerveau.py.
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ICI = Path(__file__).resolve().parent


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--top", type=int, default=5)
    a = ap.parse_args()
    tests_f = ICI / "cerveau-tests.txt"
    if not tests_f.exists():
        print(f"{tests_f} absent : écris 3 à 5 lignes « question => chemin attendu ».")
        return 1
    tests = [l.split("=>") for l in tests_f.read_text(encoding="utf-8").splitlines() if "=>" in l and not l.startswith("#")]
    echecs = 0
    for question, attendu in tests:
        question, attendu = question.strip(), attendu.strip()
        r = subprocess.run([sys.executable, str(ICI / "cerveau.py"), question, "--top", str(a.top)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=600)
        chemins = re.findall(r"^\[[-\d.]+\] (\S+)", r.stdout, re.M)
        sens = "(mode : sens)" in r.stdout
        ok = sens and attendu in chemins
        echecs += not ok
        etat = "OK " if ok else "ÉCHEC"
        detail = "" if sens else " (mode mots-clés : pip install fastembed numpy)"
        print(f"{etat} {question!r} -> {attendu}{detail}")
        if not ok and r.returncode != 0:
            print("   ", (r.stderr or r.stdout).strip()[-300:])
    print(f"{len(tests) - echecs}/{len(tests)} tests passés")
    return echecs


if __name__ == "__main__":
    sys.exit(main())
