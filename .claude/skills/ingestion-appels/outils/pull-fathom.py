#!/usr/bin/env python3
"""pull-fathom.py : rapatrie les appels enregistrés par Fathom (avec transcription) dans raw/appels/.

La clé vient de ~/.claude/secrets/fathom.env (ligne FATHOM_API_KEY=...), jamais du vault.
Un fichier par appel : raw/appels/AAAA-MM-JJ-<titre>-<id>.md. Un appel déjà présent est sauté.

Usage :
    python scripts/pull-fathom.py                        tout l'historique
    python scripts/pull-fathom.py --depuis 2025-01-01    seulement après cette date
Codes : 0 succès, 1 clé absente ou refusée, 2 autre erreur. Aucune dépendance.

Autre enregistreur que Fathom ? Garde la même sortie (un .md par appel, frontmatter
date, titre, participants, puis la transcription) : le reste de la chaîne ne change pas.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
SORTIE = VAULT / "raw" / "appels"
SECRET = Path.home() / ".claude" / "secrets" / "fathom.env"
API = "https://api.fathom.ai/external/v1/meetings"
PAGES_MAX = 500


def cle() -> str | None:
    if not SECRET.exists():
        return None
    for l in SECRET.read_text(encoding="utf-8").splitlines():
        if l.startswith("FATHOM_API_KEY="):
            return l.split("=", 1)[1].strip().strip('"') or None
    return None


def slug(t: str) -> str:
    t = unicodedata.normalize("NFKD", t or "").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:60] or "appel"


def page(k: str, curseur: str | None, depuis: str | None) -> dict:
    p = {"include_transcript": "true", "limit": "10"}
    if curseur:
        p["cursor"] = curseur
    if depuis:
        p["created_after"] = depuis
    req = urllib.request.Request(f"{API}?{urllib.parse.urlencode(p)}", headers={"X-Api-Key": k})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read().decode("utf-8"))


def date_de(m: dict) -> datetime | None:
    s = m.get("recording_start_time") or m.get("created_at") or ""
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def en_md(m: dict) -> str:
    d = date_de(m)
    titre = (m.get("title") or m.get("meeting_title") or "Sans titre").replace('"', "'")
    gens = [f"  - {i.get('name') or 'inconnu'}{' (externe)' if i.get('is_external') else ''}"
            for i in m.get("calendar_invitees") or []]
    md = ["---", f'title: "{titre}"', "type: appel", f"date: {d.date().isoformat() if d else 'inconnue'}",
          f"enregistrement: {m.get('recording_id')}", "participants:", *(gens or ["  []"]),
          "source: fathom", "---", f"# {titre}", ""]
    if m.get("default_summary"):
        resume = m["default_summary"]
        md += ["## Résumé de l'outil", resume if isinstance(resume, str) else json.dumps(resume, ensure_ascii=False), ""]
    md.append("## Transcription")
    for e in m.get("transcript") or []:
        qui = (e.get("speaker") or {}).get("display_name") or "?"
        md.append(f"**[{e.get('timestamp', '')}] {qui} :** {e.get('text', '')}")
    if not m.get("transcript"):
        md.append("*(transcription non disponible)*")
    return "\n".join(md) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--depuis")
    a = ap.parse_args()
    k = cle()
    if not k:
        print(f"Clé Fathom absente : range FATHOM_API_KEY=... dans {SECRET}", file=sys.stderr)
        return 1
    SORTIE.mkdir(parents=True, exist_ok=True)
    curseur, neufs, sautes, n = None, 0, 0, 0
    while n < PAGES_MAX:
        n += 1
        try:
            data = page(k, curseur, a.depuis)
        except urllib.error.HTTPError as e:
            if e.code in (401, 403):
                print("Clé Fathom refusée : recrée-la dans les réglages de Fathom (API).", file=sys.stderr)
                return 1
            if e.code == 429:
                time.sleep(5)
                n -= 1
                continue
            print(f"Erreur Fathom {e.code}", file=sys.stderr)
            return 2
        except Exception as e:
            print(f"Erreur réseau : {e}", file=sys.stderr)
            return 2
        for m in data.get("items", []):
            d = date_de(m)
            f = SORTIE / f"{d.date().isoformat() if d else 'inconnue'}-{slug(m.get('title'))}-{m.get('recording_id')}.md"
            if f.exists():
                sautes += 1
                continue
            f.write_text(en_md(m), encoding="utf-8")
            neufs += 1
        curseur = data.get("next_cursor")
        if not curseur:
            break
        time.sleep(0.25)
    print(f"Fini : {neufs} nouvel(s) appel(s), {sautes} déjà présent(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
