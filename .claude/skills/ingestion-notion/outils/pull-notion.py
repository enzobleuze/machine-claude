#!/usr/bin/env python3
"""pull-notion.py : copie incrémentale des bases Notion vers raw/notion-sync/<base>/<page>.md

Le jeton vient de ~/.claude/secrets/notion.env (ligne NOTION_TOKEN=...), jamais du vault.
Seules les bases PARTAGÉES avec l'intégration sont visibles (bouton « Connexions » de la page).
Incrémental : une page dont last_edited_time n'a pas bougé n'est pas retéléchargée
(état dans raw/notion-sync/_etat.json). raw/notion-sync/ est un miroir tenu par ce script seul.

Usage :
    python scripts/pull-notion.py                 toutes les bases partagées
    python scripts/pull-notion.py --base Clients  seulement les bases dont le nom contient « Clients »
    python scripts/pull-notion.py --essai         liste les bases sans rien écrire
Codes de sortie : 0 succès (même 0 page), 1 jeton absent ou refusé, 2 autre erreur.
Aucune dépendance (urllib).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

VAULT = Path(__file__).resolve().parent.parent
SORTIE = VAULT / "raw" / "notion-sync"
ETAT = SORTIE / "_etat.json"
SECRET = Path.home() / ".claude" / "secrets" / "notion.env"
API = "https://api.notion.com/v1"
VERSION = "2022-06-28"  # version stable qui expose encore /databases/{id}/query
PAUSE = 0.35  # Notion limite à environ 3 requêtes par seconde
PROFONDEUR_MAX = 3


class JetonRefuse(Exception):
    pass


def jeton() -> str:
    if not SECRET.exists():
        raise JetonRefuse(f"{SECRET} absent")
    for l in SECRET.read_text(encoding="utf-8").splitlines():
        if l.startswith("NOTION_TOKEN="):
            v = l.split("=", 1)[1].strip().strip('"')
            if v:
                return v
    raise JetonRefuse("NOTION_TOKEN vide")


def appel(tok: str, methode: str, chemin: str, corps: dict | None = None) -> dict:
    for essai in range(5):
        req = urllib.request.Request(API + chemin, method=methode,
                                     data=json.dumps(corps).encode() if corps is not None else None,
                                     headers={"Authorization": f"Bearer {tok}", "Notion-Version": VERSION,
                                              "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                time.sleep(PAUSE)
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise JetonRefuse("jeton refusé (401)")
            if e.code in (429, 502, 503) and essai < 4:
                time.sleep(float(e.headers.get("Retry-After", 2 ** essai)))
                continue
            raise
    raise RuntimeError("trop d'essais")


def paginer(tok: str, methode: str, chemin: str, corps: dict | None = None):
    curseur = None
    while True:
        if methode == "POST":
            c = dict(corps or {}, page_size=100, **({"start_cursor": curseur} if curseur else {}))
            r = appel(tok, "POST", chemin, c)
        else:
            sep = "&" if "?" in chemin else "?"
            r = appel(tok, "GET", f"{chemin}{sep}page_size=100" + (f"&start_cursor={curseur}" if curseur else ""))
        yield from r.get("results", [])
        if not r.get("has_more"):
            return
        curseur = r.get("next_cursor")


def texte(rt: list) -> str:
    return "".join(x.get("plain_text", "") for x in rt or [])


def slug(t: str) -> str:
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", t).strip("-").lower()[:60] or "sans-titre"


PREFIXES = {"heading_1": "# ", "heading_2": "## ", "heading_3": "### ", "bulleted_list_item": "- ",
            "numbered_list_item": "1. ", "quote": "> ", "callout": "> ", "toggle": "- "}


def blocs_md(tok: str, bloc_id: str, niveau: int = 0) -> list[str]:
    out = []
    for b in paginer(tok, "GET", f"/blocks/{bloc_id}/children"):
        t = b.get("type", "")
        contenu = b.get(t, {}) if isinstance(b.get(t), dict) else {}
        ligne = texte(contenu.get("rich_text", []))
        if t == "to_do":
            ligne = ("- [x] " if contenu.get("checked") else "- [ ] ") + ligne
        elif t == "code":
            ligne = f"```\n{ligne}\n```"
        elif t == "divider":
            ligne = "---"
        elif t == "child_page":
            ligne = f"(sous-page : {contenu.get('title', '')})"
        elif t in ("image", "file", "pdf", "video"):
            ligne = f"({t} : {texte(contenu.get('caption', [])) or 'sans légende'})"
        else:
            ligne = PREFIXES.get(t, "") + ligne
        if ligne.strip():
            out.append("  " * niveau + ligne)
        if b.get("has_children") and niveau < PROFONDEUR_MAX and t != "child_page":
            out += blocs_md(tok, b["id"], niveau + 1)
    return out


def valeur(p: dict) -> str:
    t = p.get("type")
    v = p.get(t)
    if t in ("title", "rich_text"):
        return texte(v)
    if t in ("select", "status"):
        return (v or {}).get("name", "")
    if t == "multi_select":
        return ", ".join(x.get("name", "") for x in v or [])
    if t == "date":
        return (v or {}).get("start", "") or ""
    if t in ("number", "checkbox", "url", "email", "phone_number"):
        return "" if v is None else str(v)
    if t == "people":
        return ", ".join(x.get("name", "") for x in v or [])
    if t == "relation":
        return f"{len(v or [])} lien(s)"
    return ""


def page_md(tok: str, page: dict, base: str) -> tuple[str, str]:
    props = page.get("properties", {})
    titre = next((texte(p["title"]) for p in props.values() if p.get("type") == "title"), "") or "Sans titre"
    lignes = ["---", f'title: "{titre.replace(chr(34), chr(39))}"', "type: notion", f'base: "{base}"',
              f"notion_id: {page['id']}", f"modifie: {page.get('last_edited_time', '')}", "---", f"# {titre}", ""]
    for nom, p in props.items():
        v = valeur(p)
        if v and p.get("type") != "title":
            lignes.append(f"- **{nom}** : {v}")
    lignes += ["", *blocs_md(tok, page["id"])]
    return titre, "\n".join(lignes) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base", default="")
    ap.add_argument("--essai", action="store_true")
    a = ap.parse_args()
    try:
        tok = jeton()
        bases = list(paginer(tok, "POST", "/search", {"filter": {"property": "object", "value": "database"}}))
    except JetonRefuse as e:
        print(f"Jeton Notion : {e}. Recrée-le et range-le dans {SECRET}.", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Erreur Notion : {e}", file=sys.stderr)
        return 2
    etat = json.loads(ETAT.read_text(encoding="utf-8")) if ETAT.exists() else {}
    neufs = sautes = erreurs = 0
    for db in bases:
        nom = texte(db.get("title", [])) or "base-sans-nom"
        if a.base.lower() not in nom.lower():
            continue
        print(f"Base : {nom}")
        if a.essai:
            continue
        dossier = SORTIE / slug(nom)
        dossier.mkdir(parents=True, exist_ok=True)
        try:
            pages = list(paginer(tok, "POST", f"/databases/{db['id']}/query", {}))
        except Exception as e:
            print(f"  base ignorée ({e})", file=sys.stderr)
            erreurs += 1
            continue
        for page in pages:
            if etat.get(page["id"]) == page.get("last_edited_time"):
                sautes += 1
                continue
            try:
                titre, md = page_md(tok, page, nom)
                (dossier / f"{slug(titre)}-{page['id'][:8]}.md").write_text(md, encoding="utf-8")
                etat[page["id"]] = page.get("last_edited_time")
                neufs += 1
            except Exception as e:  # une page en échec ne bloque pas les autres, elle sera retentée
                print(f"  page {page['id'][:8]} en échec : {e}", file=sys.stderr)
                erreurs += 1
        ETAT.write_text(json.dumps(etat, indent=1), encoding="utf-8")
    print(f"Fini : {neufs} page(s) écrites, {sautes} inchangées, {erreurs} erreur(s), {len(bases)} base(s) visibles.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
