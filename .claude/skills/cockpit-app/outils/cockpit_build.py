#!/usr/bin/env python3
"""Cockpit : construit outputs/cockpit/state.json à partir du vault. Python 3.8+, bibliothèque standard seulement.

Sources lues (rien d'autre) :
  wiki/strategie/plan.md        frontmatter (cap, jalons, trimestre, mois, semaine) + section « Semaine » + ligne **PROCHAINE**
  wiki/clients/*.md             fiches (type: client ou lead ; attend_reponse ; statut ; prochain_pas)
  outputs/cockpit/ventes.jsonl  une ligne par paiement reçu (écrite par la sous-commande « vente »)

Usage :
  python cockpit_build.py [--vault DOSSIER]                 reconstruit state.json
  python cockpit_build.py vente MONTANT QUI [--vault ...]   note un paiement reçu aujourd'hui
  python cockpit_build.py ligne [--vault ...]               affiche la ligne de situation (début de conversation)
  python cockpit_build.py --check                           contrôles intégrés

Règle : un chiffre absent s'affiche « inconnu », jamais 0. Rien ne sort du disque.
"""
import datetime as dt
import json
import os
import re
import sys
import tempfile
from pathlib import Path

PLAN_REL = "wiki/strategie/plan.md"
CLIENTS_REL = "wiki/clients"
SALES_REL = "outputs/cockpit/ventes.jsonl"
STATE_REL = "outputs/cockpit/state.json"
WAIT_ALERT_DAYS = 2   # un homme qui attend ta réponse depuis plus de 2 jours devient une alerte
WEEK_STALE_DAYS = 7   # la semaine du plan n'a pas été réécrite depuis 7 jours : revue du lundi oubliée
JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


# ---------- mini lecteur de frontmatter (sous-ensemble de YAML : clés, dictionnaires imbriqués, listes de { } ) ----------

def _strip_comment(s):
    out, q = [], None
    for ch in s:
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch == "#":
            break
        out.append(ch)
    return "".join(out).rstrip()


def _split_top(s, sep=","):
    parts, cur, q, depth = [], [], None, 0
    for ch in s:
        if q:
            if ch == q:
                q = None
        elif ch in "\"'":
            q = ch
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
        elif ch == sep and depth == 0:
            parts.append("".join(cur))
            cur = []
            continue
        cur.append(ch)
    if "".join(cur).strip():
        parts.append("".join(cur))
    return parts


def scalar(v):
    v = v.strip()
    if v == "" or v in ("null", "~"):
        return None
    if len(v) >= 2 and v[0] == v[-1] and v[0] in "\"'":
        return v[1:-1]
    if v.startswith("{") and v.endswith("}"):
        d = {}
        for part in _split_top(v[1:-1]):
            k, _, val = part.partition(":")
            d[k.strip()] = scalar(val)
        return d
    if v.startswith("[") and v.endswith("]"):
        return [scalar(x) for x in _split_top(v[1:-1])]
    if v in ("true", "false"):
        return v == "true"
    if re.fullmatch(r"-?\d+", v):
        return int(v)
    if re.fullmatch(r"-?\d+\.\d+", v):
        return float(v)
    return v


def parse_frontmatter(text):
    """Le frontmatter entre deux lignes « --- » en dictionnaire. {} s'il manque. ValueError si la forme est cassée."""
    text = text.replace("\r\n", "\n")
    m = re.match(r"^---\n(.*?)\n---\s*(\n|$)", text, re.S)
    if not m:
        return {}
    root = {}
    stack = [(-1, root)]          # (indentation, conteneur)
    pending = None                # (indentation, dict parent, clé) : clé sans valeur, attend son contenu
    for n, raw in enumerate(m.group(1).split("\n"), 2):
        line = _strip_comment(raw)
        if not line.strip():
            continue
        ind = len(line) - len(line.lstrip(" "))
        body = line.strip()
        if pending and ind > pending[0]:
            _, parent, key = pending
            parent[key] = [] if body.startswith("- ") else {}
            stack.append((ind, parent[key]))
        pending = None
        while stack and ind < stack[-1][0]:
            stack.pop()
        if not stack:
            raise ValueError("ligne {} : indentation incohérente".format(n))
        cont = stack[-1][1]
        if body.startswith("- "):
            if not isinstance(cont, list):
                raise ValueError("ligne {} : élément de liste hors d'une liste".format(n))
            cont.append(scalar(body[2:]))
            continue
        key, sep, val = body.partition(":")
        if not sep or not isinstance(cont, dict):
            raise ValueError("ligne {} : « clé: valeur » attendu".format(n))
        key = key.strip()
        if val.strip() == "":
            cont[key] = None
            pending = (ind, cont, key)
        else:
            cont[key] = scalar(val)
    return root


# ---------- petites aides ----------

def as_date(v):
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v)[:10])
    except (TypeError, ValueError):
        return None


def eur(n):
    return "inconnu" if n is None else "{:,.0f} €".format(n).replace(",", " ")


def num(v):
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def section(text, title_re):
    """Le corps d'une section « ## … » dont le titre matche title_re (jusqu'au « ## » suivant)."""
    m = re.search(r"^## ((?:" + title_re + r")[^\n]*)\n(.*?)(?=^## |\Z)", text, re.M | re.S | re.I)
    return (m.group(1), m.group(2)) if m else (None, "")


def checkboxes(body):
    out = []
    for line in body.splitlines():
        b = re.match(r"\s*- \[([ xX])\] (.*)", line)
        if b:
            out.append({"fait": b.group(1) != " ", "texte": re.sub(r"\*\*|\[\[|\]\]|`", "", b.group(2)).strip()})
    return out


DATE_IN_TEXT = re.compile(r"\b(?:" + "|".join(JOURS) + r")\s+(\d{1,2})/(\d{1,2})\b", re.I)


def date_passee(texte, today):
    """« jj/mm » si la case annonce « lundi 12/01 » et que ce jour est passé, sinon None."""
    for m in DATE_IN_TEXT.finditer(texte):
        try:
            d = dt.date(today.year, int(m.group(2)), int(m.group(1)))
        except ValueError:
            continue
        if (d - today).days > 200:   # « lundi 28/12 » lu en janvier : c'était l'an dernier
            d = d.replace(year=d.year - 1)
        if d < today:
            return "{:02d}/{:02d}".format(d.day, d.month)
    return None


# ---------- lecture des sources ----------

def read_plan(path, today, errors):
    if not path.exists():
        errors.append("Plan absent : {} (lance le skill plan-unique).".format(path.name))
        return None
    text = path.read_text(encoding="utf-8")
    try:
        fm = parse_frontmatter(text)
    except ValueError as e:
        errors.append("Plan illisible ({}).".format(e))
        return None
    titre_sem, corps = section(text, r"Semaine")
    semaine_cases = checkboxes(corps)
    prochaine = None
    for c in checkboxes(text):
        if not c["fait"] and "PROCHAINE" in c["texte"]:
            prochaine = c["texte"].replace("PROCHAINE", "", 1).strip(" :")
            break
    return {"fm": fm, "semaineTitre": (titre_sem or "").strip() or None, "semaineCases": semaine_cases, "prochaine": prochaine}


def read_clients(folder, today, errors):
    people = []
    if not folder.exists():
        return people
    for f in sorted(folder.glob("*.md")):
        if f.name.startswith("_"):
            continue
        try:
            fm = parse_frontmatter(f.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as e:
            errors.append("Fiche illisible : {} ({}).".format(f.name, e))
            continue
        if fm.get("type") not in ("client", "lead"):
            continue
        attend = as_date(fm.get("attend_reponse"))
        dernier = as_date(fm.get("dernier_echange"))
        people.append({
            "id": f.stem,
            "nom": str(fm.get("title") or f.stem),   # le prénom reste local : la page ne sort jamais de l'ordinateur
            "type": fm["type"],
            "statut": str(fm.get("statut") or "inconnu"),
            "attendDepuis": attend.isoformat() if attend else None,
            "joursAttente": max(0, (today - attend).days) if attend else None,
            "prochainPas": fm.get("prochain_pas") or None,
            "dernierEchange": dernier.isoformat() if dernier else None,
        })
    return people


def read_sales(path, today, errors):
    """Ventes du mois en cours. None si le fichier n'existe pas (= inconnu, jamais 0)."""
    if not path.exists():
        return None
    out = []
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            s = json.loads(line)
            if str(s["date"])[:7] == today.strftime("%Y-%m"):
                out.append({"date": s["date"], "montant": float(s["montant"]), "qui": s.get("qui", "")})
        except (ValueError, KeyError, TypeError):
            errors.append("Vente illisible ligne {} de {}.".format(n, path.name))
    return out


# ---------- calcul de l'état ----------

def build_state(vault, today=None):
    vault = Path(vault)
    today = today or dt.date.today()
    errors = []
    plan = read_plan(vault / PLAN_REL, today, errors)
    people = read_clients(vault / CLIENTS_REL, today, errors)
    sales = read_sales(vault / SALES_REL, today, errors)
    fm = (plan or {}).get("fm") or {}

    attente = sorted([p for p in people if p["attendDepuis"]], key=lambda p: p["attendDepuis"])
    encaisse = None if sales is None else sum(s["montant"] for s in sales)
    cible = num((fm.get("mois") or {}).get("cible"))
    cap = fm.get("cap") or {}
    tri = fm.get("trimestre") or {}
    objectifs = []
    for o in tri.get("objectifs") or []:
        if isinstance(o, dict):
            objectifs.append({"titre": o.get("titre"), "cible": num(o.get("cible")), "actuel": num(o.get("actuel")), "unite": o.get("unite") or ""})
    sem = fm.get("semaine") or {}
    prochaine = (plan or {}).get("prochaine")

    alertes = []
    if plan is not None and not prochaine:
        alertes.append("Ton plan n'a pas de ligne PROCHAINE. Dis à Claude quelle est ta prochaine tâche.")
    if prochaine and date_passee(prochaine, today):
        alertes.append("La prochaine tâche parle du {}, déjà passé. Dis à Claude ce qui a eu lieu.".format(date_passee(prochaine, today)))
    debut = as_date(sem.get("debut"))
    if plan is not None and (not debut or (today - debut).days >= WEEK_STALE_DAYS):
        alertes.append("La semaine du plan n'a pas été réécrite depuis lundi. Demande « plan du lundi » à Claude.")
    for c in (plan or {}).get("semaineCases", []):
        if not c["fait"] and date_passee(c["texte"], today):
            alertes.append("Case datée d'avant aujourd'hui : « {} ». À cocher ou à replanifier.".format(c["texte"][:80]))
    for p in attente:
        if p["joursAttente"] is not None and p["joursAttente"] > WAIT_ALERT_DAYS:
            alertes.append("{} attend ta réponse depuis {} jours.".format(p["nom"], p["joursAttente"]))
    for o in objectifs:
        if o["actuel"] is None:
            alertes.append("Objectif du trimestre sans chiffre actuel : « {} ».".format(o["titre"]))
    alertes += errors

    parts = []
    if prochaine:
        parts.append("Prochaine tâche : " + prochaine)
    parts.append("{} personne{} attend{} ta réponse".format(len(attente), "s" if len(attente) > 1 else "", "ent" if len(attente) > 1 else ""))
    parts.append("encaissé ce mois : {}{}".format(eur(encaisse), " sur " + eur(cible) if cible else ""))
    if alertes:
        parts.append("{} alerte{}".format(len(alertes), "s" if len(alertes) > 1 else ""))
    return {
        "genereLe": dt.datetime.now().isoformat(timespec="seconds"),
        "aujourdhui": today.isoformat(),
        "situation": ". ".join(parts) + ".",
        "attente": attente,
        "prochaine": prochaine,
        "argent": {"encaisse": encaisse, "cible": cible, "ventes": None if sales is None else len(sales), "lignes": sales or []},
        "semaine": {"titre": (plan or {}).get("semaineTitre"), "chose": sem.get("chose"), "cases": (plan or {}).get("semaineCases", [])},
        "trimestre": {"nom": tri.get("nom"), "fin": str(tri.get("fin")) if tri.get("fin") else None, "objectifs": objectifs},
        "cap": {"libelle": cap.get("libelle"), "mensuel": num(cap.get("mensuel")), "echeance": str(cap.get("echeance")) if cap.get("echeance") else None},
        "clients": {"actifs": sum(1 for p in people if p["type"] == "client" and p["statut"] == "actif"),
                    "leads": sum(1 for p in people if p["type"] == "lead"), "total": len(people)},
        "alertes": alertes,
    }


def atomic_write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=1)
        os.replace(tmp, str(path))
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)


def add_sale(vault, montant, qui, today=None):
    value = float(str(montant).replace(" ", "").replace("€", "").replace(",", "."))
    if not 0 < value <= 1000000:
        raise ValueError("montant hors limites : {}".format(montant))
    path = Path(vault) / SALES_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    row = json.dumps({"date": (today or dt.date.today()).isoformat(), "montant": value, "qui": qui.strip()}, ensure_ascii=False)
    with open(path, "a", encoding="utf-8") as f:   # ajout seul : on ne réécrit jamais l'historique des ventes
        f.write(row + "\n")
    return value


def check():
    fm = parse_frontmatter('---\na: 1\nb:\n  c: "x # pas un commentaire"\n  d:\n    - {t: "un, deux", n: 3}\n# note\ne: 2027-01-31\n---\n')
    assert fm == {"a": 1, "b": {"c": "x # pas un commentaire", "d": [{"t": "un, deux", "n": 3}]}, "e": "2027-01-31"}, fm
    assert date_passee("lundi 05/01 : appel", dt.date(2027, 1, 7)) == "05/01"
    assert date_passee("lundi 28/12 : appel", dt.date(2027, 1, 3)) == "28/12"
    assert date_passee("lundi 12/01 : appel", dt.date(2027, 1, 7)) is None
    assert eur(None) == "inconnu" and eur(1500) == "1 500 €"
    print("contrôles OK")


def main(argv):
    vault = Path(os.environ.get("COCKPIT_VAULT") or Path.cwd())
    if "--vault" in argv:
        i = argv.index("--vault")
        vault = Path(argv[i + 1])
        argv = argv[:i] + argv[i + 2:]
    if argv[:1] == ["--check"]:
        check()
        return 0
    if argv[:1] == ["vente"]:
        if len(argv) < 3:
            print("Usage : cockpit_build.py vente MONTANT QUI", file=sys.stderr)
            return 2
        try:
            v = add_sale(vault, argv[1], " ".join(argv[2:]))
        except ValueError as e:
            print("Vente refusée : {}".format(e), file=sys.stderr)
            return 2
        print("Vente notée : {} ({}).".format(eur(v), " ".join(argv[2:])))
    state = build_state(vault)
    if argv[:1] == ["ligne"]:
        print(state["situation"])
        return 0
    atomic_write(vault / STATE_REL, state)
    print("state.json écrit. " + state["situation"])
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
