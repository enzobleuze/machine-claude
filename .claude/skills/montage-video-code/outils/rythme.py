"""rythme.py : contrôle du rythme d'une vidéo rendue, mesuré sur les pixels (ffmpeg et Python seuls).

Deux contrôles :
  1. pas de trou mort : quelque chose bouge à l'image au moins toutes les N secondes
     (un pas « bouge » quand plus de 0,4 % des pixels changent de plus de 14 niveaux de gris) ;
  2. rien ne clignote : aucun plan plus court que 0,3 s entre deux coupes franches, aucun élément qui apparaît
     et disparaît en moins de 0,3 s.
Profils : reel = trou de 1,0 s au plus ; long = trou de 12 s au plus. Dans les deux, rien sous 0,3 s.
C'est un AVERTISSEMENT : il ne bloque jamais un rendu. Il dit où regarder.

  python rythme.py video.mp4 [--profil reel|long]        écrit video-rythme.json, sortie 0 si OK, 1 sinon
  python rythme.py --test
Repris d'un contrôle de rythme publié sous licence MIT par un créateur de montage par IA, réécrit sans numpy.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import commun as C  # noqa: E402

PROFILS = {  # trou max, tenue min, (pas/s, largeur) pour les trous, (pas/s, largeur) pour les clignotements
    "reel": {"trou": 1.0, "tenue": 0.3, "trous": (10, 160), "flash": (30, 96)},
    "long": {"trou": 12.0, "tenue": 0.3, "trous": (5, 120), "flash": (30, 64)},
}


def images(video, fps, largeur):
    i = C.infos(video)
    h = max(2, int(round(i["h"] * largeur / max(1, i["w"]) / 2)) * 2)
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-vf", f"fps={fps},scale={largeur}:{h},format=gray",
                          "-f", "rawvideo", "-"], capture_output=True, check=True).stdout
    n = largeur * h
    return [raw[k:k + n] for k in range(0, len(raw) - n + 1, n)], i["duree"]


def bouge(a: bytes, b: bytes, seuil: int = 14) -> float:
    """Part des pixels qui changent de plus de seuil niveaux entre deux images."""
    return sum(1 for x, y in zip(a, b) if x - y > seuil or y - x > seuil) / max(1, len(a))


def verifier(video, profil="reel") -> dict:
    P = PROFILS[profil]
    fps, larg = P["trous"]
    im, dur = images(video, fps, larg)
    ev = [round(k / fps, 2) for k in range(1, len(im)) if bouge(im[k - 1], im[k]) > .004]
    pts = [0.0] + ev + [round(dur, 2)]
    trous = [(pts[k], pts[k + 1], round(pts[k + 1] - pts[k], 2)) for k in range(len(pts) - 1)]
    morts = [t for t in trous if t[2] > P["trou"] + .05]
    fps2, larg2 = P["flash"]
    im2, _ = images(video, fps2, larg2)
    kk = max(1, round(P["tenue"] / 2 * fps2))
    coupes, flashs = [], []
    for k in range(1, len(im2)):
        if bouge(im2[k - 1], im2[k], 30) > .35:
            if coupes and k / fps2 - coupes[-1] <= .11:  # une transition de 2 ou 3 images = une seule coupe
                coupes[-1] = k / fps2
            else:
                coupes.append(k / fps2)
    for k in range(kk, len(im2) - kk, 2):
        ac, ab = bouge(im2[k - kk], im2[k], 30), bouge(im2[k - kk], im2[k + kk], 30)
        if ac > .01 and ab < .25 * ac:
            flashs.append(round(k / fps2, 2))
    plans = [0.0] + coupes + [dur]
    courts = [(round(plans[k], 2), round(plans[k + 1], 2)) for k in range(len(plans) - 1)
              if plans[k + 1] - plans[k] < P["tenue"] - .01]
    groupes = []
    for t in flashs:
        if groupes and t - groupes[-1][1] <= .1:
            groupes[-1][1] = t
        else:
            groupes.append([t, t])
    rep = {"video": str(video), "profil": profil, "duree": round(dur, 2), "plus_long_trou_s": max((t[2] for t in trous), default=0),
           "limite_trou_s": P["trou"], "trous_morts": morts, "coupes": [round(c, 2) for c in coupes],
           "plans_trop_courts": courts, "clignotements": groupes, "ok": not morts and not courts and not groupes}
    Path(video).with_name(Path(video).stem + "-rythme.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1),
                                                                         encoding="utf-8")
    return rep


def resume(rep) -> list[str]:
    out = [f"rythme ({rep['profil']}) : plus long moment immobile {rep['plus_long_trou_s']} s (limite {rep['limite_trou_s']}), "
           f"{len(rep['coupes'])} coupes"]
    out += [f"  trou mort de {a} à {b} s ({d} s sans rien qui bouge)" for a, b, d in rep["trous_morts"]]
    out += [f"  plan de {a} à {b} s plus court que 0,3 s" for a, b in rep["plans_trop_courts"]]
    out += [f"  un élément apparaît et disparaît vers {a} à {b} s" for a, b in rep["clignotements"]]
    return out + ["OK" if rep["ok"] else "À REGARDER (avertissement, le rendu est gardé)"]


def avertir(video, profil="reel") -> None:
    """Appel depuis un outil de rendu : imprime le résumé, n'arrête jamais le rendu."""
    try:
        for l in resume(verifier(video, profil)):
            print("[rythme]", l)
    except Exception as e:  # le contrôle ne casse jamais un rendu
        print(f"[rythme] contrôle non fait : {e}")


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        bon, mauvais = Path(tmp) / "bon.mp4", Path(tmp) / "mauvais.mp4"
        C.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=black:s=270x480:r=30:d=3", "-f", "lavfi", "-i",
               "color=white:s=60x60:r=30:d=3", "-filter_complex", "[0][1]overlay=x='mod(t*120,210)':y=200",
               "-pix_fmt", "yuv420p", bon])
        C.run(["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "color=black:s=270x480:r=30:d=4", "-vf",
               "drawbox=x=0:y=0:w=270:h=480:c=white:t=fill:enable='between(n,90,91)'", "-pix_fmt", "yuv420p", mauvais])
        r1, r2 = verifier(bon), verifier(mauvais)
        assert r1["ok"], r1
        assert not r2["ok"] and r2["trous_morts"] and (r2["plans_trop_courts"] or r2["clignotements"]), r2
        assert verifier(mauvais, "long")["trous_morts"] == [], "profil long : 4 s immobiles ne sont pas un trou"
        assert (Path(tmp) / "bon-rythme.json").exists()
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Contrôle du rythme d'une vidéo rendue (avertissement).")
    ap.add_argument("video", nargs="?")
    ap.add_argument("--profil", choices=sorted(PROFILS), default="reel")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.video:
        rep = verifier(a.video, a.profil)
        print("\n".join(resume(rep)))
        sys.exit(0 if rep["ok"] else 1)
    else:
        ap.print_help()
