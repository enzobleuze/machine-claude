"""garder-connexion.pyw : garde NotebookLM connecté (tâche planifiée toutes les 20 minutes).

Pourquoi : le cookie de session Google tourne vite et meurt si rien ne le rafraîchit, et Google
a révoqué en une heure environ les connexions ouvertes par le navigateur de l'outil. Ce script
rafraîchit la session ; s'il échoue, il relit la connexion du navigateur du quotidien (Firefox
par défaut). Trois échecs de suite : il écrit ~/.notebooklm/ALERTE-connexion.txt, que Claude
lit en début de séance. Un succès efface l'alerte. Bibliothèque standard seulement.

Usage : pythonw garder-connexion.pyw [--navigateur firefox]   (tâche planifiée, sans fenêtre)
        python garder-connexion.pyw --une-fois                (à la main : affiche le résultat)
        python garder-connexion.pyw --test                    (auto-test, sans réseau)
"""
from __future__ import annotations

import datetime
import os
import subprocess
import sys
import tempfile
from pathlib import Path

DOSSIER = Path.home() / ".notebooklm"
SEUIL = 3


def lancer(*args: str) -> tuple[int, str]:
    # pythonw n'a pas de console : on appelle python.exe à côté, sans fenêtre
    py = Path(sys.executable).with_name("python.exe")
    py = py if py.exists() else Path(sys.executable)
    try:
        r = subprocess.run([str(py), "-m", "notebooklm", "auth", "refresh", *args],
                           capture_output=True, text=True, timeout=120,
                           env={**os.environ, "PYTHONUTF8": "1"},
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
        return r.returncode, (r.stderr or r.stdout).strip()
    except Exception as e:  # délai dépassé, Python absent : un échec, rejoué au passage suivant
        return -1, f"{type(e).__name__}: {e}"


def rafraichir(navigateur: str, lancer=lancer) -> tuple[int, str]:
    rc, sortie = lancer()
    if rc == 0:
        return rc, sortie
    return lancer("--browser-cookies", navigateur, "--verify")


def noter(rc: int, sortie: str, dossier: Path, maintenant: datetime.datetime) -> int:
    """Tient le compte des échecs de suite ; renvoie ce compte (0 après un succès)."""
    dossier.mkdir(parents=True, exist_ok=True)
    compteur, alerte = dossier / "echecs-connexion.txt", dossier / "ALERTE-connexion.txt"
    if rc == 0:
        compteur.write_text("0", encoding="utf-8")
        alerte.unlink(missing_ok=True)
        return 0
    echecs = (int(compteur.read_text(encoding="utf-8").strip() or 0) if compteur.exists() else 0) + 1
    compteur.write_text(str(echecs), encoding="utf-8")
    with (dossier / "garder-connexion.log").open("a", encoding="utf-8") as f:
        f.write(f"{maintenant:%Y-%m-%d %H:%M} échec {echecs} rc={rc} {sortie[:300]}\n")
    if echecs >= SEUIL and not alerte.exists():
        alerte.write_text(
            f"NotebookLM est déconnecté depuis le {maintenant:%d/%m à %H:%M} ({echecs} échecs de suite).\n"
            "1. Ouvre Firefox depuis le menu Démarrer, va sur https://notebooklm.google.com\n"
            "   et vérifie que ta session Google est ouverte (reconnecte-toi si besoin).\n"
            "2. Dis à Claude : « Répare la connexion NotebookLM. »\n", encoding="utf-8")
    return echecs


def auto_test() -> int:
    appels: list[tuple[str, ...]] = []

    def faux(*codes: int):
        it = iter(codes)

        def f(*args: str) -> tuple[int, str]:
            appels.append(args)
            return next(it), "sortie"
        return f

    assert rafraichir("firefox", faux(0)) == (0, "sortie") and len(appels) == 1
    appels.clear()
    assert rafraichir("firefox", faux(1, 0))[0] == 0
    assert appels[1] == ("--browser-cookies", "firefox", "--verify"), appels
    t = datetime.datetime(2026, 1, 2, 3, 4)
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        assert [noter(1, "x", d, t) for _ in range(SEUIL)] == [1, 2, 3]
        assert (d / "ALERTE-connexion.txt").exists()
        assert noter(0, "", d, t) == 0 and not (d / "ALERTE-connexion.txt").exists()
    print("AUTO-TEST OK")
    return 0


def main(args: list[str]) -> int:
    if "--test" in args:
        return auto_test()
    navigateur = args[args.index("--navigateur") + 1] if "--navigateur" in args else "firefox"
    rc, sortie = rafraichir(navigateur)
    echecs = noter(rc, sortie, DOSSIER, datetime.datetime.now())
    if "--une-fois" in args:
        print("CONNEXION OK" if rc == 0 else f"ÉCHEC ({echecs} de suite) : {sortie[:300]}")
    return 0 if rc == 0 else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
