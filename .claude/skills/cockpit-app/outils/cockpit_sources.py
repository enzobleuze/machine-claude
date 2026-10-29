#!/usr/bin/env python3
"""Cockpit : les sources branchables. Bibliothèque standard seulement.

Chaque source rend un dictionnaire avec au moins :
  etat      "ok" | "vide" | "non-branche" | "erreur"
  consigne  la phrase qui dit quoi brancher quand rien n'est branché (None sinon)
Une source en panne ne casse jamais le build : elle rend son état et une erreur lisible, sans aucun secret.

  secrets   ~/.claude/secrets/<service>.env (lignes NOM=valeur), jamais dans le vault
  taches    Linear (linear.env : LINEAR_API_KEY, clé personnelle) ou, à défaut, wiki/maps/taches.md
  agenda    adresse iCal secrète de ton agenda (agenda.env : AGENDA_ICAL_URL, AGENDA_ICAL_URL_2...)
  echelle   wiki/business/echelle-offres.md (le tableau des marches)
  reseaux   outputs/cockpit/reseaux/releves.jsonl, publications.jsonl, commentaires.jsonl, traites.json
  tournage  outputs/youtube/<slug>/script.md et outputs/courts/scripts/*.md, verdict du board à côté
  appel     wiki/scripts/script-appel.md et wiki/scripts/objections-reponses.md
"""
import datetime as dt
import hashlib
import json
import re
import time
import unicodedata
import urllib.error
import urllib.request
from pathlib import Path

LINEAR_URL = "https://api.linear.app/graphql"
CACHE_TACHES_S = 300      # Linear relu au plus toutes les 5 minutes (vidé après chaque écriture)
CACHE_AGENDA_S = 1800     # agenda relu au plus toutes les 30 minutes ; réseau coupé : on garde la copie
NOMS_RESEAUX = {"instagram": "Instagram", "youtube": "YouTube", "tiktok": "TikTok", "facebook": "Facebook",
                "linkedin": "LinkedIn", "threads": "Threads", "x": "X", "pinterest": "Pinterest", "bluesky": "Bluesky"}


class SourceErreur(Exception):
    """Une panne lisible, sans secret, à montrer telle quelle."""


# ---------- petites aides partagées ----------

def slug(texte):
    t = unicodedata.normalize("NFKD", str(texte or "")).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-")


def lire_json(path, defaut):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return defaut


def lire_jsonl(path, erreurs=None):
    out = []
    p = Path(path)
    if not p.exists():
        return out
    for n, ligne in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
        if ligne.strip():
            try:
                out.append(json.loads(ligne))
            except ValueError:
                if erreurs is not None:
                    erreurs.append("Ligne {} illisible dans {}.".format(n, p.name))
    return out


def sans_frontmatter(texte):
    texte = texte.replace("\r\n", "\n")
    m = re.match(r"^---\n.*?\n---\s*\n", texte, re.S)
    return texte[m.end():] if m else texte


def sections(texte, niveau=2):
    """[(titre, corps)] pour chaque titre de ce niveau, dans l'ordre."""
    marque = "#" * niveau + " "
    out, titre, corps = [], None, []
    for ligne in texte.replace("\r\n", "\n").split("\n"):
        if ligne.startswith(marque):
            if titre is not None:
                out.append((titre, "\n".join(corps).strip()))
            titre, corps = ligne[len(marque):].strip(), []
        elif titre is not None:
            if niveau > 1 and re.match(r"^#{1,%d} " % (niveau - 1), ligne):   # un titre plus haut ferme la section
                out.append((titre, "\n".join(corps).strip()))
                titre, corps = None, []
            else:
                corps.append(ligne)
    if titre is not None:
        out.append((titre, "\n".join(corps).strip()))
    return out


def lire_secrets(dossier, service):
    p = Path(dossier) / (service + ".env")
    out = {}
    try:
        lignes = p.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return out
    for ligne in lignes:
        k, sep, v = ligne.strip().partition("=")
        if sep and k and not k.startswith("#"):
            out[k.strip()] = v.strip().strip('"').strip("'")
    return out


def _cache_frais(path, duree):
    return path.exists() and time.time() - path.stat().st_mtime < duree


def _ecrire(path, texte):
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(texte, encoding="utf-8")
    tmp.replace(path)


# ---------- tâches : Linear ou fichier ----------

class Linear:
    """Lecture et écritures Linear par la clé personnelle. `envoi` se remplace dans les tests (aucun réseau)."""

    def __init__(self, cle, envoi=None):
        self.cle = cle
        self.envoi = envoi or self._http

    def _http(self, requete, variables):
        corps = json.dumps({"query": requete, "variables": variables}).encode("utf-8")
        req = urllib.request.Request(LINEAR_URL, data=corps, headers={
            "Authorization": self.cle, "Content-Type": "application/json", "User-Agent": "cockpit-local"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read().decode("utf-8"))

    def gql(self, requete, variables=None):
        try:
            rep = self.envoi(requete, variables or {})
        except urllib.error.HTTPError as e:
            e.close()
            if e.code in (400, 401, 403):
                raise SourceErreur("Linear refuse la clé. Crée une nouvelle clé personnelle et range-la dans linear.env.")
            raise SourceErreur("Linear répond une erreur {}. Réessaie plus tard.".format(e.code))
        except (urllib.error.URLError, OSError, ValueError) as e:
            raise SourceErreur("Linear est injoignable ({}).".format(type(e).__name__))
        if rep.get("errors"):
            raise SourceErreur("Linear a refusé la demande : {}".format(str(rep["errors"][0].get("message", ""))[:120]))
        return rep.get("data") or {}

    def lister(self):
        d = self.gql('query { issues(first: 150, filter: {state: {type: {in: ["started", "unstarted", "backlog"]}}}) '
                     '{ nodes { identifier title url dueDate startedAt state { type } } } }')
        return [{"id": n["identifier"], "titre": n.get("title") or "", "url": n.get("url"), "echeance": n.get("dueDate"),
                 "depuis": (n.get("startedAt") or "")[:10] or None, "enCours": (n.get("state") or {}).get("type") == "started",
                 "modifiable": True} for n in (d.get("issues") or {}).get("nodes") or []]

    def _issue(self, ident):
        d = self.gql("query($id: String!) { issue(id: $id) { id team { states { nodes { id type } } } } }", {"id": ident})
        if not d.get("issue"):
            raise SourceErreur("Linear ne connaît pas la tâche {}.".format(ident))
        return d["issue"]

    def _maj(self, iid, entree):
        d = self.gql("mutation($id: String!, $e: IssueUpdateInput!) { issueUpdate(id: $id, input: $e) { success } }",
                     {"id": iid, "e": entree})
        if not (d.get("issueUpdate") or {}).get("success"):
            raise SourceErreur("Linear n'a pas enregistré le changement.")

    def changer_etat(self, ident, type_etat):
        issue = self._issue(ident)
        for s in ((issue.get("team") or {}).get("states") or {}).get("nodes") or []:
            if s.get("type") == type_etat:
                return self._maj(issue["id"], {"stateId": s["id"]})
        raise SourceErreur("Cette équipe Linear n'a pas d'état « {} ».".format(type_etat))

    def deplacer(self, ident, date):
        self._maj(self._issue(ident)["id"], {"dueDate": date})

    def creer(self, titre, date, equipe=None):
        if not equipe:
            equipes = (self.gql("query { teams(first: 1) { nodes { id } } }").get("teams") or {}).get("nodes") or []
            if not equipes:
                raise SourceErreur("Ton espace Linear n'a aucune équipe.")
            equipe = equipes[0]["id"]
        d = self.gql("mutation($e: IssueCreateInput!) { issueCreate(input: $e) { success issue { identifier } } }",
                     {"e": {"teamId": equipe, "title": titre, "dueDate": date}})
        r = d.get("issueCreate") or {}
        if not r.get("success"):
            raise SourceErreur("Linear n'a pas créé la tâche.")
        return (r.get("issue") or {}).get("identifier")


def lire_fichier_taches(path):
    """wiki/maps/taches.md : sections En cours, À faire, Plus tard ; une case par tâche, échéance AAAA-MM-JJ dans le texte."""
    items = []
    for n, (titre, corps) in enumerate(sections(path.read_text(encoding="utf-8"))):
        t = slug(titre)
        if t.startswith("fait"):
            continue
        for ligne in corps.splitlines():
            m = re.match(r"\s*- \[ \] (.+)", ligne)
            if m:
                d = re.search(r"\b(\d{4}-\d{2}-\d{2})\b", m.group(1))
                items.append({"id": "T{}".format(len(items) + 1), "titre": re.sub(r"\s*\(?\b\d{4}-\d{2}-\d{2}\b\)?", "", m.group(1)).strip(),
                              "url": None, "echeance": d.group(1) if d else None, "depuis": None,
                              "enCours": t.startswith("en-cours"), "modifiable": False})
    return items


def taches(vault, secrets_dir, today, cache_dir, envoi=None, reseau=True):
    base = {"source": "aucune", "etat": "non-branche", "erreur": None, "enCours": [], "enRetard": [], "datees": [],
            "consigne": "Branche tes tâches : une clé personnelle Linear dans linear.env, ou le fichier wiki/maps/taches.md. "
                        "Dis à Claude « branche mes tâches au cockpit »."}
    cle = lire_secrets(secrets_dir, "linear").get("LINEAR_API_KEY")
    if cle:
        base.update(source="linear", consigne=None)
        cache = Path(cache_dir) / "taches.json"
        items = lire_json(cache, None) if _cache_frais(cache, CACHE_TACHES_S) or not reseau else None
        if items is None and not reseau:
            items = []
        if items is None:
            try:
                items = Linear(cle, envoi).lister()
                _ecrire(cache, json.dumps(items, ensure_ascii=False))
            except SourceErreur as e:
                base.update(etat="erreur", erreur=str(e))
                items = lire_json(cache, [])   # la dernière copie, même vieille, plutôt que rien
    else:
        f = Path(vault) / "wiki/maps/taches.md"
        if not f.exists():
            return base
        base.update(source="fichier", consigne=None)
        items = lire_fichier_taches(f)
    jour = today.isoformat()
    if base["etat"] != "erreur":
        base["etat"] = "ok" if items else "vide"
    base["enCours"] = [t for t in items if t["enCours"]]
    base["enRetard"] = sorted([t for t in items if t["echeance"] and t["echeance"] < jour], key=lambda t: t["echeance"])
    base["datees"] = [t for t in items if t["echeance"]]
    return base


# ---------- agenda : adresse iCal secrète ----------

def _deplier(texte):
    lignes = []
    for ligne in texte.replace("\r\n", "\n").split("\n"):
        if ligne[:1] in (" ", "\t") and lignes:
            lignes[-1] += ligne[1:]
        else:
            lignes.append(ligne)
    return lignes


def _date_ics(valeur, params):
    v = valeur.strip()
    if "VALUE=DATE" in params or len(v) == 8:
        return dt.datetime(int(v[:4]), int(v[4:6]), int(v[6:8])), True
    d = dt.datetime.strptime(v[:15], "%Y%m%dT%H%M%S")
    if v.endswith("Z"):
        d = d.replace(tzinfo=dt.timezone.utc).astimezone().replace(tzinfo=None)
    # shortcut: une heure avec TZID est lue comme l'heure de l'ordinateur ; à revoir si l'agenda vit dans un autre fuseau
    return d, False


def _texte_ics(v):
    return v.replace("\\n", " ").replace("\\,", ",").replace("\\;", ";").replace("\\\\", "\\").strip()


def _occurrences(ev, debut, fin):
    """Les dates de début d'un événement dans [debut, fin], règles simples de répétition comprises."""
    regle = dict(p.split("=", 1) for p in ev.get("RRULE", "").split(";") if "=" in p)
    d0 = ev["debut"]
    if not regle:
        return [d0] if debut <= d0.date() <= fin else []
    freq, pas = regle.get("FREQ", ""), max(1, int(regle.get("INTERVAL", "1") or 1))
    compte = int(regle["COUNT"]) if regle.get("COUNT", "").isdigit() else None
    jusqua = None
    if regle.get("UNTIL"):
        jusqua = _date_ics(regle["UNTIL"], "")[0].date()
    jours = {"MO": 0, "TU": 1, "WE": 2, "TH": 3, "FR": 4, "SA": 5, "SU": 6}
    par_jour = [jours[j[-2:]] for j in regle.get("BYDAY", "").split(",") if j[-2:] in jours] or [d0.weekday()]
    lundi0 = d0.date() - dt.timedelta(days=d0.weekday())
    # chaque test se calcule depuis le premier jour : sans COUNT, on peut partir directement du début de la fenêtre
    out, n, jour = [], 0, d0.date() if compte is not None else max(d0.date(), debut)
    for _ in range(30000):   # borne de sécurité : une règle cassée ne bloque jamais le build
        if jour > fin or (jusqua and jour > jusqua) or (compte is not None and n >= compte):
            break
        if freq == "DAILY":
            ok = (jour - d0.date()).days % pas == 0
        elif freq == "WEEKLY":
            ok = jour.weekday() in par_jour and ((jour - lundi0).days // 7) % pas == 0
        elif freq == "MONTHLY":
            ok = jour.day == d0.day and ((jour.year - d0.year) * 12 + jour.month - d0.month) % pas == 0
        elif freq == "YEARLY":
            ok = (jour.month, jour.day) == (d0.month, d0.day) and (jour.year - d0.year) % pas == 0
        else:
            return [d0] if debut <= d0.date() <= fin else []
        if ok:
            n += 1
            if jour >= debut and jour.isoformat() not in ev["exdates"]:
                out.append(dt.datetime.combine(jour, d0.time()))
        jour += dt.timedelta(days=1)
    return out


def lire_ics(texte, debut, fin):
    bruts, cur = [], None
    for ligne in _deplier(texte):
        if ligne == "BEGIN:VEVENT":
            cur = {"exdates": set()}
        elif ligne == "END:VEVENT" and cur is not None:
            bruts.append(cur)
            cur = None
        elif cur is not None and ":" in ligne:
            nom, _, val = ligne.partition(":")
            cle, _, params = nom.partition(";")
            cle, params = cle.upper(), params.upper()
            try:
                if cle in ("DTSTART", "DTEND"):
                    cur[cle], cur[cle + "_jour"] = _date_ics(val, params)
                elif cle == "EXDATE":
                    cur["exdates"].update(_date_ics(x, params)[0].date().isoformat() for x in val.split(","))
                elif cle == "RECURRENCE-ID":
                    cur["recid"] = _date_ics(val, params)[0].date().isoformat()
                elif cle in ("SUMMARY", "UID", "RRULE", "STATUS"):
                    cur[cle] = val
            except ValueError:
                cur["casse"] = True
    remplaces = {(b.get("UID"), b["recid"]) for b in bruts if b.get("recid")}
    out = []
    for b in bruts:
        if b.get("casse") or "DTSTART" not in b or b.get("STATUS", "").upper() == "CANCELLED":
            continue
        duree = (b["DTEND"] - b["DTSTART"]) if "DTEND" in b else dt.timedelta(0)
        ev = {"debut": b["DTSTART"], "RRULE": "" if b.get("recid") else b.get("RRULE", ""), "exdates": b["exdates"]}
        for d in _occurrences(ev, debut, fin):
            if not b.get("recid") and (b.get("UID"), d.date().isoformat()) in remplaces:
                continue
            journee = b.get("DTSTART_jour", False)
            f = d + duree
            out.append({"id": "agenda:" + hashlib.sha1("{}{}".format(b.get("UID"), d).encode()).hexdigest()[:12],
                        "type": "evenement", "titre": _texte_ics(b.get("SUMMARY", "Sans titre")),
                        "debut": d.date().isoformat() if journee else d.strftime("%Y-%m-%dT%H:%M"),
                        "fin": None if journee else f.strftime("%Y-%m-%dT%H:%M"), "journee": journee,
                        "source": "agenda", "modifiable": False})
    return sorted(out, key=lambda e: e["debut"])


def agenda(secrets_dir, today, cache_dir, reseau=True):
    s = lire_secrets(secrets_dir, "agenda")
    urls = [v for k, v in sorted(s.items()) if k.startswith("AGENDA_ICAL_URL") and v]
    if not urls:
        return {"etat": "non-branche", "erreur": None, "evenements": [],
                "consigne": "Pour voir ton agenda ici, range l'adresse secrète iCal de ton agenda dans agenda.env. "
                            "Dis à Claude « branche mon agenda au cockpit »."}
    evts, erreurs = [], []
    for i, url in enumerate(urls):
        cache = Path(cache_dir) / "agenda-{}.ics".format(i + 1)
        texte = None
        if _cache_frais(cache, CACHE_AGENDA_S) or (not reseau and cache.exists()):
            texte = cache.read_text(encoding="utf-8")
        elif not reseau:
            continue
        if texte is None:
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "cockpit-local"})
                with urllib.request.urlopen(req, timeout=15) as r:
                    texte = r.read().decode("utf-8", "replace")
                _ecrire(cache, texte)
            except (urllib.error.URLError, OSError, ValueError):
                # jamais l'adresse dans le message : elle donne accès à tout l'agenda
                erreurs.append("Agenda {} injoignable, la dernière copie est gardée.".format(i + 1))
                texte = cache.read_text(encoding="utf-8") if cache.exists() else ""
        evts += lire_ics(texte, today - dt.timedelta(days=31), today + dt.timedelta(days=400))
    return {"etat": "erreur" if erreurs and not evts else "ok", "erreur": " ".join(erreurs) or None, "consigne": None,
            "evenements": evts}


# ---------- échelle d'offres ----------

def premier_tableau(texte):
    lignes = [l.strip() for l in texte.splitlines()]
    for i, l in enumerate(lignes):
        if l.startswith("|") and i + 1 < len(lignes) and re.match(r"^\|[\s:|-]+\|?$", lignes[i + 1]):
            tete = [c.strip() for c in l.strip("|").split("|")]
            rangs = []
            for r in lignes[i + 2:]:
                if not r.startswith("|"):
                    break
                rangs.append([c.strip() for c in r.strip("|").split("|")])
            return tete, rangs
    return None, []


def _num_prix(texte):
    m = re.search(r"\d[\d\s]*(?:[.,]\d+)?", texte or "")
    if not m:
        return None
    try:
        return float(m.group(0).replace(" ", "").replace(" ", "").replace(",", "."))
    except ValueError:
        return None


def echelle(vault):
    f = Path(vault) / "wiki/business/echelle-offres.md"
    vide = {"etat": "non-branche", "marches": [],
            "consigne": "Ton échelle d'offres n'est pas encore écrite. Dis à Claude « construis mon échelle d'offres »."}
    if not f.exists():
        return vide
    tete, rangs = premier_tableau(sans_frontmatter(f.read_text(encoding="utf-8")))
    if not tete:
        return dict(vide, etat="erreur", consigne="Le fichier echelle-offres.md n'a pas de tableau des marches. Demande à Claude de le remettre au format.")
    cols = [slug(c) for c in tete]

    def col(*mots, sauf=None):
        for i, c in enumerate(cols):
            if i != sauf and any(c.startswith(m) or m in c for m in mots):
                return i
        return None
    i_suiv = col("suivante")
    i_nom = col("marche", "offre", "nom", sauf=i_suiv)
    i_nom = 0 if i_nom is None else i_nom
    i_prix, i_texte = col("prix"), col("contenu", "contient", "ce-qu")
    i_quand, i_ou, i_qui = col("quand"), col("ou-on", "montre", "visible"), col("a-qui", "pour-qui")
    get = lambda r, i: (r[i] if i is not None and i < len(r) else "").replace("**", "").strip()
    marches = []
    for r in rangs:
        nom = get(r, i_nom)
        if nom:
            marches.append({"id": slug(nom), "nom": nom, "prix": _num_prix(get(r, i_prix)), "prixTexte": get(r, i_prix) or None,
                            "texte": get(r, i_texte) or None, "suivante": slug(get(r, i_suiv)) or None,
                            "quand": get(r, i_quand) or None, "ou": get(r, i_ou) or None, "pourQui": get(r, i_qui) or None})
    return {"etat": "ok" if marches else "vide", "consigne": None, "marches": marches}


# ---------- réseaux : fichiers de relevés ----------

def _mediane(v):
    v = sorted(v)
    n = len(v)
    return None if not n else (v[n // 2] if n % 2 else (v[n // 2 - 1] + v[n // 2]) / 2)


def reseaux(vault, today, voulus=()):
    d = Path(vault) / "outputs/cockpit/reseaux"
    erreurs = []
    releves = [r for r in lire_jsonl(d / "releves.jsonl", erreurs) if isinstance(r.get("abonnes"), (int, float)) and r.get("reseau") and r.get("date")]
    pubs = lire_jsonl(d / "publications.jsonl", erreurs)
    comms = lire_jsonl(d / "commentaires.jsonl", erreurs)
    traites = lire_json(d / "traites.json", {})
    jour = today.isoformat()
    ids = list(dict.fromkeys([slug(x) for x in voulus] + [slug(r["reseau"]) for r in releves]))

    def valeur_au(rid, date):
        vals = [r for r in releves if slug(r["reseau"]) == rid and str(r["date"])[:10] <= date]
        return max(vals, key=lambda r: str(r["date"]))["abonnes"] if vals else None

    liste = []
    for rid in ids:
        rs = sorted([r for r in releves if slug(r["reseau"]) == rid], key=lambda r: str(r["date"]))
        der = rs[-1] if rs else None
        v7 = valeur_au(rid, (today - dt.timedelta(days=7)).isoformat())
        v30 = valeur_au(rid, (today - dt.timedelta(days=30)).isoformat())
        age = (today - dt.date.fromisoformat(str(der["date"])[:10])).days if der else None
        liste.append({"id": rid, "nom": NOMS_RESEAUX.get(rid, rid.capitalize()), "abonnes": der["abonnes"] if der else None,
                      "releveLe": str(der["date"])[:10] if der else None, "source": (der or {}).get("source") or None,
                      "delta7": der["abonnes"] - v7 if der and v7 is not None else None,
                      "delta30": der["abonnes"] - v30 if der and v30 is not None else None,
                      "etat": "non-branche" if not der else ("ancien" if age > 7 else "ok"),
                      "historique": [{"date": str(r["date"])[:10], "valeur": r["abonnes"]} for r in rs][-120:]})
    # total : la dernière valeur connue de chaque réseau, reportée entre deux relevés (rien n'est deviné avant le premier)
    dates = sorted({str(r["date"])[:10] for r in releves if str(r["date"])[:10] >= (today - dt.timedelta(days=365)).isoformat()})
    serie = []
    for date in dates:
        vals = [valeur_au(r["id"], date) for r in liste]
        vals = [v for v in vals if v is not None]
        serie.append({"date": date, "valeur": sum(vals)})
    connus = [r for r in liste if r["abonnes"] is not None]
    # ce qui marche : les vues d'une publication contre la médiane de son réseau sur 30 jours
    debut = (today - dt.timedelta(days=30)).isoformat()
    recentes = [p for p in pubs if str(p.get("date", ""))[:10] >= debut and isinstance(p.get("vues"), (int, float))]
    classees = []
    for rid in {slug(p.get("reseau")) for p in recentes}:
        lot = [p for p in recentes if slug(p.get("reseau")) == rid]
        med = _mediane([p["vues"] for p in lot])
        for p in lot:
            classees.append(dict(p, reseau=rid, nomReseau=NOMS_RESEAUX.get(rid, rid.capitalize()),
                                 facteur=round(p["vues"] / med, 1) if med else None, mediane=med))
    classees = [p for p in classees if p["facteur"] is not None]
    classees.sort(key=lambda p: p["facteur"], reverse=True)
    assez = len(classees) >= 4
    a_repondre = [dict(c, id=str(c.get("id") or slug("{}{}{}".format(c.get("reseau"), c.get("auteur"), c.get("date")))),
                       nomReseau=NOMS_RESEAUX.get(slug(c.get("reseau")), str(c.get("reseau") or "").capitalize()))
                  for c in comms if str(c.get("id")) not in traites and not c.get("repondu")]
    a_repondre.sort(key=lambda c: str(c.get("date") or ""), reverse=True)
    etat = "ok" if connus else ("vide" if ids else "non-branche")
    return {"etat": etat, "erreur": " ".join(erreurs) or None,
            "consigne": None if connus else "Aucun relevé de tes réseaux pour l'instant. Note tes abonnés ici, ou dis à Claude « relève mes réseaux ».",
            "reseaux": liste, "total": sum(r["abonnes"] for r in connus) if connus else None,
            "delta30Total": sum(r["delta30"] for r in connus if r["delta30"] is not None) if any(r["delta30"] is not None for r in connus) else None,
            "serie": serie, "meilleurs": classees[:3] if assez else [], "faibles": classees[-3:][::-1] if assez else [],
            "publicationsMesurees": len(classees), "commentaires": a_repondre[:60], "aRepondre": len(a_repondre)}


# ---------- tournage : scripts prêts, board, état ----------

VERDICT = re.compile(r"^##\s*Verdict\s*:\s*(.+?)\s*$", re.M | re.I)
ETATS_TOURNAGE = ("a_tourner", "tournee", "publiee")


def _element(type_, slug_, script, board, etat):
    texte = sans_frontmatter(script.read_text(encoding="utf-8"))
    titre = next((l[2:].strip() for l in texte.splitlines() if l.startswith("# ")), slug_)
    v = VERDICT.search(board.read_text(encoding="utf-8")) if board.exists() else None
    verdict = v.group(1) if v else None
    return {"type": type_, "slug": slug_, "titre": titre, "mots": len(re.findall(r"\w+", texte)),
            "verdict": verdict, "vert": bool(verdict and verdict.upper().startswith("VERT")),
            "etat": etat.get("etat") if etat.get("etat") in ETATS_TOURNAGE else "a_tourner", "le": etat.get("le")}


def chemins_tournage(vault, type_, slug_):
    v = Path(vault)
    if type_ == "youtube":
        dossier = v / "outputs/youtube" / slug_
        return dossier / "script.md", dossier / "board.md", dossier / "tournage.json"
    dossier = v / "outputs/courts/scripts"
    return dossier / (slug_ + ".md"), dossier / (slug_ + ".board.md"), v / "outputs/courts/tournage.json"


def tournage(vault):
    v = Path(vault)
    out = []
    for s in sorted((v / "outputs/youtube").glob("*/script.md")):
        if not s.parent.name.startswith("_"):
            _, b, e = chemins_tournage(v, "youtube", s.parent.name)
            out.append(_element("youtube", s.parent.name, s, b, lire_json(e, {})))
    etats = lire_json(v / "outputs/courts/tournage.json", {})
    for s in sorted((v / "outputs/courts/scripts").glob("*.md")):
        if not s.name.endswith(".board.md"):
            _, b, _ = chemins_tournage(v, "court", s.stem)
            out.append(_element("court", s.stem, s, b, etats.get(s.stem) or {}))
    rep = {"prets": sum(1 for e in out if e["vert"] and e["etat"] == "a_tourner"),
           "attente": sum(1 for e in out if not e["vert"] and e["etat"] == "a_tourner"),
           "tournes": sum(1 for e in out if e["etat"] == "tournee"), "publiees": sum(1 for e in out if e["etat"] == "publiee")}
    return {"etat": "ok" if out else "vide", "elements": out, "repartition": rep,
            "consigne": None if out else "Aucun script pour l'instant. Les scripts vidéo arrivent avec « script-video » et « reels-et-shorts »."}


# ---------- script d'appel ----------

def _blocs(corps):
    out = []
    for p in re.split(r"\n\s*\n", corps.strip()):
        p = p.strip()
        if not p:
            continue
        dit = all(l.startswith(">") for l in p.splitlines())
        texte = "\n".join(re.sub(r"^>\s?", "", l) for l in p.splitlines()) if dit else p
        out.append({"texte": texte.replace("**", ""), "dit": dit})
    return out


def appel(vault):
    v = Path(vault)
    f = v / "wiki/scripts/script-appel.md"
    if not f.exists():
        return {"etat": "non-branche", "phases": [], "objections": [], "securite": None,
                "consigne": "Ton script d'appel n'est pas encore écrit. Dis à Claude « écris mon script d'appel »."}
    phases, securite = [], None
    for titre, corps in sections(sans_frontmatter(f.read_text(encoding="utf-8"))):
        if slug(titre).startswith("securite"):
            securite = " ".join(b["texte"] for b in _blocs(corps))
        elif corps.strip():
            phases.append({"titre": titre, "blocs": _blocs(corps)})
    objections = []
    o = v / "wiki/scripts/objections-reponses.md"
    if o.exists():
        texte = sans_frontmatter(o.read_text(encoding="utf-8"))
        niveau = 3 if re.search(r"^### ", texte, re.M) else 2
        objections = [{"titre": t, "blocs": _blocs(c)} for t, c in sections(texte, niveau) if c.strip()]
    return {"etat": "ok" if phases else "vide", "consigne": None, "phases": phases, "objections": objections, "securite": securite}
