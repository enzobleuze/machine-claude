"""roast.py : comité « roast » ancré sur des carnets (skill comite-roast-ancre). Python 3.8+, bibliothèque standard seule.

  python roast.py tour <dossier> <n>
      Lance en parallèle chaque siège du tour n : un fichier <dossier>/prompts/r<n>-<siege>.txt = un siège.
      Chaque siège tourne en `claude -p` Sonnet SANS outil, SANS serveur MCP, dans un dossier neutre (il ne voit ni le vault
      ni la mémoire : seulement son prompt). Écrit <dossier>/tour<n>-<siege>.json (la carte) et les jetons dans couts.json.
  python roast.py scores <dossier>
      Lit session.json (sièges et poids) et la dernière carte de chaque siège, calcule la note pondérée par option,
      la bande de verdict et les plafonds. Écrit scores.json et imprime le tableau.
  python roast.py selftest

session.json minimal : {"options": [{"id": "A", "label": "..."}], "sieges": [{"id": "expert1", "poids": 3}]}
Carte d'un siège (JSON) : {"option": "A", "notes": {"A": 8, "B": 4}, "ruine": "aucun|possible|probable",
                           "porte": "aller simple|aller-retour", ...}
Bandes : 7,5 et plus FONCE ; 6 à 7,4 FONCE AVEC CONDITIONS ; 4,5 à 5,9 À REMODELER ; moins de 4,5 N'Y VA PAS.
Plafonds : une ruine « probable » plafonne à À REMODELER ; « aller simple » avec un écart de 4 points ou plus entre
sièges sur l'option en tête plafonne à FONCE AVEC CONDITIONS.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
BANDES = [(7.5, "FONCE"), (6.0, "FONCE AVEC CONDITIONS"), (4.5, "À REMODELER"), (-1, "N'Y VA PAS")]


def siege(prompt_f, systeme_f, modele="sonnet"):
    """Une carte JSON, ou (None, erreur). Un JSON invalide est redemandé une fois."""
    cmd = ["claude", "-p", "--model", modele, "--system-prompt-file", str(systeme_f), "--tools", "", "--strict-mcp-config",
           "--setting-sources", "", "--output-format", "json"]
    err = ""
    for _ in range(2):
        try:
            r = subprocess.run(cmd, input=prompt_f.read_text(encoding="utf-8"), capture_output=True, text=True,
                               encoding="utf-8", cwd=tempfile.gettempdir(), timeout=300,
                               env={**os.environ, "PYTHONUTF8": "1", "ENABLE_CLAUDEAI_MCP_SERVERS": "false"})
            out = json.loads(r.stdout)
            carte = json.loads(re.search(r"\{.*\}", out["result"], re.S).group(0))
        except Exception as e:  # délai, JSON invalide, commande refusée : on retente une fois
            err = f"{type(e).__name__}: {e}"[:200]
            continue
        u = out.get("usage", {})
        entree = sum(u.get(k, 0) for k in ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens"))
        return carte, {"entree": entree, "sortie": u.get("output_tokens", 0)}
    return None, {"erreur": err}


def tour(d, n):
    if not shutil.which("claude"):
        sys.exit("commande `claude` introuvable sur le PATH")
    d = Path(d).resolve()
    systeme = HERE / "siege-systeme.md"
    prompts = sorted((d / "prompts").glob(f"r{n}-*.txt"))
    if not prompts:
        sys.exit(f"aucun prompt {d / 'prompts'}/r{n}-<siege>.txt")
    with ThreadPoolExecutor(len(prompts)) as ex:
        res = dict(zip([p.stem.split("-", 1)[1] for p in prompts], ex.map(lambda p: siege(p, systeme), prompts)))
    couts_f = d / "couts.json"
    couts = json.loads(couts_f.read_text(encoding="utf-8")) if couts_f.exists() else {}
    echecs = 0
    for s, (carte, cout) in res.items():
        couts.setdefault(f"tour{n}", {})[s] = cout
        if carte:
            (d / f"tour{n}-{s}.json").write_text(json.dumps(carte, ensure_ascii=False, indent=1), encoding="utf-8")
        else:
            echecs += 1
        print(f"tour {n} {s}: {'OK' if carte else 'ECHEC'} {cout}", flush=True)
    couts_f.write_text(json.dumps(couts, ensure_ascii=False, indent=1), encoding="utf-8")
    return 1 if echecs else 0


def derniere_carte(d, s):
    for n in (3, 2, 1):
        f = d / f"tour{n}-{s}.json"
        if f.exists():
            return json.loads(f.read_text(encoding="utf-8"))
    return None


def calc_scores(session, cartes):
    """cartes : {siege: carte}. Renvoie {option: {"note", "bande", "ecart"}} et l'option en tête."""
    poids = {s["id"]: s.get("poids", 1) for s in session["sieges"]}
    res = {}
    for o in (x["id"] for x in session["options"]):
        notes = [(poids[s], c["notes"][o]) for s, c in cartes.items() if c and o in c.get("notes", {}) and s in poids]
        if not notes:
            continue
        note = sum(p * v for p, v in notes) / sum(p for p, _ in notes)
        vals = [v for _, v in notes]
        res[o] = {"note": round(note, 2), "ecart": max(vals) - min(vals)}
    if not res:
        return res, None
    tete = max(res, key=lambda o: res[o]["note"])
    for o, r in res.items():
        r["bande"] = next(b for seuil, b in BANDES if r["note"] >= seuil)
    rang = [b for _, b in BANDES]
    if any(c.get("ruine") == "probable" for c in cartes.values() if c):
        if rang.index(res[tete]["bande"]) < rang.index("À REMODELER"):
            res[tete]["bande"], res[tete]["plafond"] = "À REMODELER", "ruine probable vue par un siège"
    if res[tete]["ecart"] >= 4 and any(c.get("porte") == "aller simple" for c in cartes.values() if c):
        if res[tete]["bande"] == "FONCE":
            res[tete]["bande"], res[tete]["plafond"] = "FONCE AVEC CONDITIONS", "porte aller simple et sièges divisés"
    return res, tete


def scores(d):
    d = Path(d)
    session = json.loads((d / "session.json").read_text(encoding="utf-8"))
    cartes = {s["id"]: derniere_carte(d, s["id"]) for s in session["sieges"]}
    manquants = [s for s, c in cartes.items() if c is None]
    res, tete = calc_scores(session, cartes)
    (d / "scores.json").write_text(json.dumps({"options": res, "en_tete": tete, "sieges_sans_carte": manquants},
                                              ensure_ascii=False, indent=1), encoding="utf-8")
    for o, r in sorted(res.items(), key=lambda x: -x[1]["note"]):
        print(f"{o} : {r['note']:.2f} ({r['bande']}) écart {r['ecart']}" + (f" | plafond : {r['plafond']}" if "plafond" in r else ""))
    if manquants:
        print("sièges sans carte : " + ", ".join(manquants))
    return 0


def selftest():
    session = {"options": [{"id": "A"}, {"id": "B"}], "sieges": [{"id": "x", "poids": 3}, {"id": "y", "poids": 1}]}
    r, tete = calc_scores(session, {"x": {"notes": {"A": 8, "B": 3}}, "y": {"notes": {"A": 8, "B": 9}}})
    assert tete == "A" and r["A"]["bande"] == "FONCE" and r["B"]["note"] == 4.5, r
    r, _ = calc_scores(session, {"x": {"notes": {"A": 9}, "ruine": "probable"}, "y": {"notes": {"A": 8}}})
    assert r["A"]["bande"] == "À REMODELER", r
    r, _ = calc_scores(session, {"x": {"notes": {"A": 10}, "porte": "aller simple"}, "y": {"notes": {"A": 4}}})
    assert r["A"]["note"] == 8.5 and r["A"]["bande"] == "FONCE AVEC CONDITIONS", r
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "session.json").write_text(json.dumps(session), encoding="utf-8")
        (t / "tour1-x.json").write_text(json.dumps({"notes": {"A": 2}}), encoding="utf-8")
        (t / "tour2-x.json").write_text(json.dumps({"notes": {"A": 7}}), encoding="utf-8")
        assert derniere_carte(t, "x")["notes"]["A"] == 7, "la dernière carte compte"
        import contextlib, io
        with contextlib.redirect_stdout(io.StringIO()):
            scores(t)
        s = json.loads((t / "scores.json").read_text(encoding="utf-8"))
        assert s["sieges_sans_carte"] == ["y"], s
    print("selftest OK")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    a = sys.argv[1:]
    if a[:1] == ["selftest"]:
        return selftest()
    if len(a) == 3 and a[0] == "tour":
        return tour(a[1], a[2])
    if len(a) == 2 and a[0] == "scores":
        return scores(a[1])
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
