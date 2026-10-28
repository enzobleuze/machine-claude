#!/usr/bin/env python3
"""notify.py : notifications de la machine pour les scripts Python (même règle que notify.sh).

Usage dans un script :
    from notify import notifier
    notifier("urgent", "Compte déconnecté", "Reconnecte le compte X : réglages, connexions.")
Usage direct :
    python notify.py <urgent|hebdo|warn|info|ok|silent> "<titre>" "<message>"

Niveaux : urgent part sur Telegram avec son ; hebdo part sans son (messages demandés par l'humain) ;
warn, info et ok vont seulement au résumé du jour outputs/cron-logs/resume-AAAA-MM-JJ.log ;
silent ne fait rien.
Secret : ~/.claude/secrets/telegram.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
Test sans envoi : NOTIFY_SIMULER=1. Bibliothèque standard seulement. Ne lève jamais d'erreur.
"""
from __future__ import annotations

import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

SECRET = Path(os.environ.get("NOTIFY_SECRET", Path.home() / ".claude" / "secrets" / "telegram.env"))
VAULT = Path(os.environ.get("VAULT", Path(__file__).resolve().parents[1]))
JOURNAUX = Path(os.environ.get("JOURNAUX", VAULT / "outputs" / "cron-logs"))


def _resume(niveau: str, titre: str, message: str) -> None:
    try:
        JOURNAUX.mkdir(parents=True, exist_ok=True)
        ligne = f"{dt.datetime.now():%H:%M:%S} [{niveau}] {titre} | {message.replace(chr(10), ' / ')}\n"
        with open(JOURNAUX / f"resume-{dt.date.today():%Y-%m-%d}.log", "a", encoding="utf-8") as f:
            f.write(ligne)
    except OSError:
        pass


def _lire_secret() -> dict:
    valeurs = {}
    try:
        for ligne in SECRET.read_text(encoding="utf-8").splitlines():
            if "=" in ligne and not ligne.lstrip().startswith("#"):
                cle, val = ligne.split("=", 1)
                valeurs[cle.strip()] = val.strip().strip('"')
    except OSError:
        pass
    return valeurs


def _telegram(texte: str, silencieux: bool, niveau: str, titre: str) -> None:
    if os.environ.get("NOTIFY_SIMULER") == "1":
        print(f"[SIMULATION {niveau}, silencieux={silencieux}]\n{texte}")
        return
    s = _lire_secret()
    token, chat = s.get("TELEGRAM_BOT_TOKEN"), s.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        _resume("SENDFAIL", f"{niveau} {titre}", "secret Telegram absent ou incomplet")
        return
    data = urllib.parse.urlencode({
        "chat_id": chat, "text": texte,
        "disable_notification": "true" if silencieux else "false",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    erreur = ""
    for essai in (1, 2):
        try:
            with urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=15) as r:
                if json.loads(r.read().decode("utf-8")).get("ok"):
                    return
        except Exception as e:  # réseau, HTTP, JSON : on réessaie une fois puis on trace
            erreur = type(e).__name__
        if essai == 1:
            time.sleep(3)
    _resume("SENDFAIL", f"{niveau} {titre}", erreur or "réponse sans ok")


def notifier(niveau: str, titre: str, message: str = "") -> None:
    if niveau == "silent":
        return
    _resume(niveau, titre, message)
    if niveau not in ("urgent", "hebdo"):
        return
    texte = (f"URGENT : {titre}" if niveau == "urgent" else titre) + (f"\n{message}" if message else "")
    _telegram(texte, silencieux=(niveau != "urgent"), niveau=niveau, titre=titre)


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(64)
    notifier(sys.argv[1], sys.argv[2], sys.argv[3] if len(sys.argv) > 3 else "")
