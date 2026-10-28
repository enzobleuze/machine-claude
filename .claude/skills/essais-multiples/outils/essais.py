"""essais.py : registre des essais multiples d'une même vidéo (Trial Reels, Shorts, variantes), lus à 24 h et 72 h.

Une vidéo filmée donne plusieurs essais. Chaque essai change UNE seule chose (l'accroche, le titre à l'écran,
le fond, la musique). On note quand il part, on relève ses chiffres à 24 h puis à 72 h, et le registre dit
qui a gagné et si le gagnant mérite d'être republié en publication normale.

Python seul, aucune bibliothèque à installer. Le registre est un fichier JSON (par défaut essais.json à côté
de ce script, ou la variable ESSAIS_REGISTRE).

  python essais.py ajouter <video> <code> --change "accroche : la scène du dîner" [--publie 2026-01-31T10:00]
  python essais.py a-lire                         ce qui doit être relevé maintenant (24 h ou 72 h passées)
  python essais.py relever <video> <code> --a 24 --vues 410 --saut 38 [--partages 9] [--commentaires 3]
  python essais.py verdict <video>                gagnant, essais limités, republier ou non
  python essais.py etat                           tout le registre en bref
  python essais.py --test                         auto-test sur un registre temporaire

--saut = pourcentage de gens partis avant 3 secondes (lu dans les statistiques de la plateforme).
Règles (réglables en tête de fichier) :
  essai sous LIMITE_VUES_24H vues à 24 h = « limité » par la plateforme, sorti de la comparaison ;
  gagnant = le plus de vues à 72 h (à défaut à 24 h) ; il est « net » s'il bat la médiane des autres
  de ECART_SAUT points de saut ou plus, sinon « à confirmer » ;
  republier = vues du gagnant >= seuil public, seuil = max(PLANCHER_PUBLIC, 80e centile des vues
  à 72 h des 30 derniers essais). Le seuil monte avec le compte.
"""
import argparse, json, os, statistics, sys, tempfile
from datetime import datetime, timedelta

LIMITE_VUES_24H = 20
ECART_SAUT = 5.0
PLANCHER_PUBLIC = 1000
REGISTRE = os.environ.get("ESSAIS_REGISTRE") or os.path.join(os.path.dirname(os.path.abspath(__file__)), "essais.json")


def charger():
    if not os.path.exists(REGISTRE):
        return {"essais": []}
    with open(REGISTRE, encoding="utf-8") as f:
        return json.load(f)


def sauver(reg):
    tmp = REGISTRE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    os.replace(tmp, REGISTRE)  # écriture atomique : un arrêt en plein milieu ne casse pas le registre


def trouver(reg, video, code):
    for e in reg["essais"]:
        if e["video"] == video and e["code"] == code:
            return e
    return None


def ajouter(video, code, change, publie=None):
    reg = charger()
    if trouver(reg, video, code):
        raise SystemExit(f"{video}/{code} existe déjà : un essai ne part jamais deux fois.")
    publie = publie or datetime.now().strftime("%Y-%m-%dT%H:%M")
    datetime.fromisoformat(publie)
    reg["essais"].append({"video": video, "code": code, "change": change, "publie": publie, "r24": None, "r72": None})
    sauver(reg)
    print(f"Ajouté : {video}/{code} ({change}), publié {publie}")


def a_lire(maintenant=None):
    maintenant = maintenant or datetime.now()
    dus = []
    for e in charger()["essais"]:
        t = datetime.fromisoformat(e["publie"])
        for h in (24, 72):
            if e[f"r{h}"] is None and maintenant >= t + timedelta(hours=h):
                dus.append((e["video"], e["code"], h))
                break
    for v, c, h in dus:
        print(f"À relever : {v}/{c} à {h} h")
    if not dus:
        print("Rien à relever pour l'instant.")
    return dus


def relever(video, code, a, vues, saut=None, partages=None, commentaires=None):
    reg = charger()
    e = trouver(reg, video, code)
    if not e:
        raise SystemExit(f"{video}/{code} introuvable.")
    if a not in (24, 72):
        raise SystemExit("--a vaut 24 ou 72.")
    if vues < 0 or (saut is not None and not 0 <= saut <= 100):
        raise SystemExit("Chiffre impossible : vues >= 0, saut entre 0 et 100.")
    e[f"r{a}"] = {"vues": vues, "saut": saut, "partages": partages, "commentaires": commentaires,
                  "le": datetime.now().strftime("%Y-%m-%dT%H:%M")}
    sauver(reg)
    print(f"Relevé {a} h noté pour {video}/{code} : {vues} vues")


def seuil_public(reg):
    vues72 = [e["r72"]["vues"] for e in reg["essais"] if e["r72"]][-30:]
    if len(vues72) < 5:
        return PLANCHER_PUBLIC
    p80 = sorted(vues72)[int(0.8 * (len(vues72) - 1))]
    return max(PLANCHER_PUBLIC, p80)


def verdict(video):
    reg = charger()
    lot = [e for e in reg["essais"] if e["video"] == video]
    if not lot:
        raise SystemExit(f"Aucun essai pour {video}.")
    limites = [e for e in lot if e["r24"] and e["r24"]["vues"] < LIMITE_VUES_24H]
    comparables = [e for e in lot if e not in limites and (e["r72"] or e["r24"])]
    res = {"video": video, "limites": [e["code"] for e in limites], "gagnant": None, "net": False, "republier": False,
           "attente": [e["code"] for e in lot if not e["r24"]]}
    if not comparables:
        print(f"{video} : rien à comparer encore.")
        return res
    lecture = lambda e: e["r72"] or e["r24"]
    comparables.sort(key=lambda e: (-lecture(e)["vues"], lecture(e)["saut"] if lecture(e)["saut"] is not None else 100))
    g = comparables[0]
    res["gagnant"] = g["code"]
    autres = [lecture(e)["saut"] for e in comparables[1:] if lecture(e)["saut"] is not None]
    if autres and lecture(g)["saut"] is not None:
        res["net"] = statistics.median(autres) - lecture(g)["saut"] >= ECART_SAUT
    seuil = seuil_public(reg)
    res["seuil"] = seuil
    res["republier"] = bool(g["r72"]) and g["r72"]["vues"] >= seuil
    print(f"{video} : gagnant {g['code']} ({g['change']}), {lecture(g)['vues']} vues, "
          f"{'net' if res['net'] else 'à confirmer'}.")
    if limites:
        print(f"Limités par la plateforme (hors comparaison) : {', '.join(res['limites'])}")
    if res["attente"]:
        print(f"Encore sans relevé 24 h : {', '.join(res['attente'])}")
    print(f"Seuil public : {seuil} vues. Republier en publication normale : {'oui' if res['republier'] else 'non'}.")
    return res


def etat():
    reg = charger()
    for e in reg["essais"]:
        r = e["r72"] or e["r24"]
        print(f"{e['video']}/{e['code']} | {e['change']} | {e['publie']} | "
              f"{(str(r['vues']) + ' vues') if r else 'pas encore relevé'}")
    print(f"{len(reg['essais'])} essais. Seuil public actuel : {seuil_public(reg)} vues.")


def auto_test():
    global REGISTRE
    with tempfile.TemporaryDirectory() as tmp:
        REGISTRE = os.path.join(tmp, "essais.json")
        t0 = (datetime.now() - timedelta(hours=80)).strftime("%Y-%m-%dT%H:%M")
        ajouter("v1", "A1", "accroche scène", t0)
        ajouter("v1", "A2", "accroche question", t0)
        ajouter("v1", "A3", "titre à l'écran", t0)
        try:
            ajouter("v1", "A1", "doublon", t0)
            raise AssertionError("doublon accepté")
        except SystemExit:
            pass
        assert len(a_lire()) == 3
        relever("v1", "A1", 24, 900, 34)
        relever("v1", "A2", 24, 230, 48)
        relever("v1", "A3", 24, 12, 70)
        assert {d[2] for d in a_lire()} == {72}
        relever("v1", "A1", 72, 1500, 33)
        relever("v1", "A2", 72, 260, 47)
        r = verdict("v1")
        assert r["gagnant"] == "A1" and r["net"] and r["limites"] == ["A3"] and r["republier"], r
    print("AUTO-TEST OK")


def main():
    p = argparse.ArgumentParser(description="Registre des essais multiples, lus à 24 h et 72 h.")
    p.add_argument("commande", nargs="?", choices=["ajouter", "a-lire", "relever", "verdict", "etat"])
    p.add_argument("video", nargs="?")
    p.add_argument("code", nargs="?")
    p.add_argument("--change", default="")
    p.add_argument("--publie")
    p.add_argument("--a", type=int)
    p.add_argument("--vues", type=int)
    p.add_argument("--saut", type=float)
    p.add_argument("--partages", type=int)
    p.add_argument("--commentaires", type=int)
    p.add_argument("--test", action="store_true")
    x = p.parse_args()
    if x.test:
        return auto_test()
    if x.commande == "ajouter" and x.video and x.code:
        ajouter(x.video, x.code, x.change, x.publie)
    elif x.commande == "a-lire":
        a_lire()
    elif x.commande == "relever" and x.video and x.code and x.a and x.vues is not None:
        relever(x.video, x.code, x.a, x.vues, x.saut, x.partages, x.commentaires)
    elif x.commande == "verdict" and x.video:
        verdict(x.video)
    elif x.commande == "etat":
        etat()
    else:
        p.print_help()


if __name__ == "__main__":
    main()
