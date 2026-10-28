"""nlm_ask.py : poser UNE question à UN carnet NotebookLM, proprement (skill notebooklm-brancher). Python 3.8+, stdlib.

Il s'appuie sur la commande `notebooklm` (paquet notebooklm-py, non officiel) et ajoute les garde-fous appris à la dure :
conversation neuve à chaque fois, carnet toujours explicite, taille de question limitée, réponse vérifiée.

  python nlm_ask.py auth
      Sortie 0 si la connexion à NotebookLM marche, 2 sinon (relancer `notebooklm login`).
  python nlm_ask.py ask <carnet> <question.txt> [--sortie dossier] [--registre carnets.json] [--auteur "Nom"]
      <carnet> = un identifiant NotebookLM, ou une clé du registre carnets.json (qui donne l'identifiant et l'auteur).
      Écrit <sortie>/<question>.answer.md (la réponse) et <sortie>/<question>.status.json (le verdict du garde-fou).
      Sortie : 0 réponse acceptée ; 1 garde-fou refusé (mauvais carnet, aucune source, sources hors du carnet) ;
               2 panne (auth, délai, commande absente) ; 4 question trop longue (découper).
  python nlm_ask.py selftest

Garde-fou (une réponse n'est acceptée que si les trois passent) :
  1. elle ne nie pas l'auteur attendu (« the sources do not contain ... <auteur> » = la question est partie ailleurs,
     ou elle était trop large) ;
  2. elle cite au moins une source ;
  3. chaque source citée appartient à la liste des sources de CE carnet (cache dans <sortie>/.cache/, rafraîchi une fois).
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_SIGNES = 3800  # NotebookLM rejette une question au-delà d'environ 4 000 signes (« status 3 »)
DENI = r"(do not contain|don't contain|does not contain|doesn't contain|no information|ne contiennent (pas|aucun)|ne contient (pas|aucun)).{0,60}"
ENV = {**os.environ, "PYTHONUTF8": "1"}  # sans cela, les accents cassent sous Windows


def nlm(*args, timeout=420):
    """Lance `notebooklm <args>` et renvoie son JSON. Lève RuntimeError avec un message lisible."""
    if not shutil.which("notebooklm"):
        raise RuntimeError("commande `notebooklm` introuvable : installer notebooklm-py (skill notebooklm-brancher, étape 1)")
    try:
        r = subprocess.run(["notebooklm", *args], capture_output=True, text=True, encoding="utf-8", env=ENV, timeout=timeout)
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"délai dépassé ({timeout} s)")
    if r.returncode:
        raise RuntimeError((r.stderr or r.stdout).strip()[:400])
    try:
        return json.loads(r.stdout)
    except json.JSONDecodeError:
        raise RuntimeError("réponse non JSON : " + r.stdout.strip()[:200])


def ref_ids(obj):
    """Tous les identifiants de source cités, quelle que soit la forme exacte du JSON (elle change selon les versions)."""
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("source_id", "sourceId") and isinstance(v, str):
                out.add(v)
            else:
                out |= ref_ids(v)
    elif isinstance(obj, list):
        for v in obj:
            out |= ref_ids(v)
    return out


def sources_du_carnet(carnet, cache_dir, rafraichir=False):
    cache = Path(cache_dir) / f"{carnet}.json"
    if rafraichir or not cache.exists():
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(json.dumps(nlm("source", "list", "-n", carnet, "--json", timeout=120), ensure_ascii=False), encoding="utf-8")
    d = json.loads(cache.read_text(encoding="utf-8"))
    return {s.get("id") for s in d.get("sources", [])}, d.get("notebook_title", "")


def garde_fou(reponse, refs, carnet, auteur, cache_dir):
    """(ok, raison, titre du carnet)."""
    if auteur and re.search(DENI + re.escape(auteur), reponse, re.I):
        return False, f"la réponse nie {auteur} : mauvais carnet ou question trop large", ""
    if not refs:
        return False, "aucune source citée (question trop large, ou amorce « réponds seulement depuis tes sources » absente)", ""
    ids, titre = sources_du_carnet(carnet, cache_dir)
    if not refs <= ids:
        ids, titre = sources_du_carnet(carnet, cache_dir, rafraichir=True)
    if not refs <= ids:
        return False, f"{len(refs - ids)} source(s) citée(s) hors du carnet demandé", titre
    return True, f"{len(refs)} source(s) citée(s), toutes dans « {titre} »", titre


def resoudre(carnet, registre):
    """Identifiant et auteur attendu, depuis le registre si <carnet> en est une clé."""
    if registre and Path(registre).is_file():
        reg = json.loads(Path(registre).read_text(encoding="utf-8-sig"))
        if carnet in reg:
            return reg[carnet]["id"], reg[carnet].get("auteur")
    return carnet, None


def demander(carnet, question, sortie, auteur=None):
    q = Path(question)
    n = len(q.read_text(encoding="utf-8-sig"))
    sortie = Path(sortie)
    sortie.mkdir(parents=True, exist_ok=True)
    statut_f = sortie / f"{q.stem}.status.json"
    if n > MAX_SIGNES:
        statut = {"ok": False, "raison": f"question de {n} signes (plafond {MAX_SIGNES}) : découper en lots de 4 à 6 points"}
        statut_f.write_text(json.dumps(statut, ensure_ascii=False, indent=1), encoding="utf-8")
        print("TROP LONGUE : " + statut["raison"])
        return 4
    t0 = time.time()
    try:
        # -n explicite et --new : sans eux, `ask` continue la DERNIÈRE conversation, parfois sur un autre carnet
        brut = nlm("ask", "-n", carnet, "--new", "--yes", "--json", "--prompt-file", str(q))
    except RuntimeError as e:
        statut = {"ok": False, "raison": f"échec de la question : {e}"}
        statut_f.write_text(json.dumps(statut, ensure_ascii=False, indent=1), encoding="utf-8")
        print("PANNE : " + statut["raison"])
        return 2
    (sortie / f"{q.stem}.raw.json").write_text(json.dumps(brut, ensure_ascii=False, indent=1), encoding="utf-8")
    reponse = (brut.get("answer") or brut.get("text") or "") if isinstance(brut, dict) else ""
    (sortie / f"{q.stem}.answer.md").write_text(reponse, encoding="utf-8")
    try:
        ok, raison, titre = garde_fou(reponse, ref_ids(brut), carnet, auteur, sortie / ".cache")
    except RuntimeError as e:
        ok, raison, titre = False, f"liste des sources illisible : {e}", ""
    statut = {"ok": ok, "raison": raison, "carnet": carnet, "carnet_titre": titre, "mots": len(reponse.split()),
              "secondes": round(time.time() - t0)}
    statut_f.write_text(json.dumps(statut, ensure_ascii=False, indent=1), encoding="utf-8")
    print(("OK : " if ok else "REFUSÉ : ") + raison)
    return 0 if ok else 1


def selftest():
    global nlm
    vrai = nlm
    faux = {"ask": {"answer": "Point 1 AGREE [1].", "references": [{"source_id": "s1"}]},
            "list": {"notebook_title": "Carnet test", "sources": [{"id": "s1"}, {"id": "s2"}]}}

    def nlm_faux(*args, timeout=0):
        return faux["ask"] if args[0] == "ask" else faux["list"]
    nlm = nlm_faux
    try:
        with tempfile.TemporaryDirectory() as t:
            t = Path(t)
            q = t / "q.txt"
            q.write_text("Answer ONLY from the sources. 1. point", encoding="utf-8")
            assert demander("abc", q, t / "out", auteur="Durand") == 0
            assert (t / "out" / "q.answer.md").read_text(encoding="utf-8").startswith("Point 1")
            faux["ask"] = {"answer": "The sources do not contain anything from Durand.", "references": [{"source_id": "s1"}]}
            assert demander("abc", q, t / "out", auteur="Durand") == 1, "auteur nié"
            faux["ask"] = {"answer": "Une réponse sans source."}
            assert demander("abc", q, t / "out") == 1, "aucune source"
            faux["ask"] = {"answer": "Réponse [1].", "citations": [{"sourceId": "zz"}]}
            assert demander("abc", q, t / "out") == 1, "source hors du carnet"
            q.write_text("x" * (MAX_SIGNES + 1), encoding="utf-8")
            assert demander("abc", q, t / "out") == 4, "trop longue"
            reg = t / "carnets.json"
            reg.write_text(json.dumps({"expert": {"id": "abc", "auteur": "Durand"}}), encoding="utf-8")
            assert resoudre("expert", reg) == ("abc", "Durand") and resoudre("xyz", reg) == ("xyz", None)
    finally:
        nlm = vrai
    print("selftest OK")
    return 0


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description="Une question à un carnet NotebookLM, avec garde-fou")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("auth")
    a_ = sub.add_parser("ask")
    a_.add_argument("carnet")
    a_.add_argument("question")
    a_.add_argument("--sortie", default="outputs/carnets")
    a_.add_argument("--registre", default="carnets.json")
    a_.add_argument("--auteur")
    sub.add_parser("selftest")
    a = ap.parse_args()
    if a.cmd == "selftest":
        return selftest()
    if a.cmd == "auth":
        try:
            ok = nlm("auth", "check", "--test", "--json", timeout=60).get("status") == "ok"
        except RuntimeError as e:
            print(f"AUTH KO : {e}")
            return 2
        print("AUTH OK" if ok else "AUTH KO : lancer `notebooklm login` dans un terminal")
        return 0 if ok else 2
    try:
        carnet, auteur = resoudre(a.carnet, a.registre)
        return demander(carnet, a.question, a.sortie, a.auteur or auteur)
    except (OSError, json.JSONDecodeError, KeyError) as e:
        print(f"lecture impossible : {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
