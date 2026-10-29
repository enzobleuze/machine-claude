"""decoupe.py : une vidéo longue + une liste de moments -> des Shorts verticaux 1080x1920, avec ffmpeg seul.
Titre en haut et sous-titres aux couleurs de la charte (bibliotheque/marque/charte-jetons.json, sinon la charte simple).

  python decoupe.py video.mp4 moments.json [-o dossier] [--mode buste|flou|centre] [--mots transcription.json]
                    [--centre 0.5] [--miroir] [--min 15] [--max 90] [--apercu]
  python decoupe.py --test

moments.json : [{"debut": 81.5, "fin": 124.0, "titre": "La phrase qui accroche"}, ...]
  (choisis par Claude dans la transcription : compris seuls, accroche dans les 3 premières secondes, idée complète,
  aucun appel à l'action au milieu)

Modes :
  buste  (défaut) tête et buste en 3:4, calés en bas de l'image, sur la même image agrandie et floutée ; le titre vit
         dans le flou du haut. Le cadrage retenu après essais dans le système d'origine.
  flou   la vidéo 16:9 entière au milieu, sur la même image floutée. Rien n'est coupé.
  centre recadrage 9:16 plein cadre. Net seulement si la source est en 4K : en 1080p, la découpe ne fait
         qu'environ 600 px de large et sort floue.
--mots : la transcription de la vidéo longue (transcrire.py). Avec elle, chaque moment démarre sur un début de mot,
         finit sur une fin de phrase (jusqu'à 1,5 s plus tard), reçoit ses sous-titres, et un moment qui commence par
         un mot de liaison (« donc », « ensuite »...) est refusé : il ne se comprend pas seul.
--centre : où est le visage dans l'image (0 = bord gauche, 1 = bord droit). --miroir : image retournée.
Refus avant rendu : moment trop court ou trop long, chevauchement, moment hors de la vidéo, début sur un mot de liaison.
Sortie : short-01.mp4, short-02.mp4... et shorts.json (titre, début, fin, fichier) pour la distribution.
"""
import argparse
import json
import os
import re
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path[:0] = [str(ICI), str(ICI.parents[1] / "montage-video-code" / "outils")]
import commun as C  # noqa: E402

LIAISON = re.compile(r"^(donc|ensuite|puis|alors|enfin|bref|du coup|deuxièmement|troisièmement|premièrement|"
                     r"et puis|après ça|par contre)\b", re.I)
FLOU = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2"
Y_TITRE = {"buste": 240, "flou": 330, "centre": 330}
Y_ST = {"buste": 1450, "flou": 1400, "centre": 1450}


def filtre(mode, centre, miroir, ass=None, j=None, apercu=False):
    m = "hflip," if miroir else ""
    if mode == "flou":
        g = f"[0:v]{m}split[a][b];[a]{FLOU}[f];[b]scale=1080:-2[v];[f][v]overlay=(W-w)/2:(H-h)/2,setsar=1"
    elif mode == "buste":
        x = f"'min(max({centre}*iw-ih*3/8,0),iw-ih*3/4)'"
        g = f"[0:v]{m}split[a][b];[a]{FLOU}[f];[b]crop=ih*3/4:ih:{x}:0,scale=1080:1440[v];[f][v]overlay=0:480,setsar=1"
    else:
        x = f"'min(max({centre}*iw-ih*9/32,0),iw-ih*9/16)'"
        g = f"[0:v]{m}crop='min(iw,ih*9/16)':'min(ih,iw*16/9)':{x}:0,scale=1080:1920,setsar=1"
    if ass:
        g += "," + C.filtre_ass(ass, j)
    return g + (",scale=540:960" if apercu else "") + "[out]"


def caler(moments, mots, mini, maxi):
    """Début sur un début de mot, fin sur une fin de phrase. -> (moments calés, refus)."""
    out, refus = [], []
    for k, m in enumerate(moments, 1):
        m = dict(m)
        dedans = [w for w in mots if w[1] >= m["debut"] - .3 and w[1] < m["fin"]]
        if dedans:
            m["debut"] = round(max(0.0, dedans[0][1] - .05), 2)
            premiere = " ".join(w[0].strip() for w in dedans[:3])
            if LIAISON.match(premiere):
                refus.append(f"moment {k} commence par un mot de liaison (« {premiere} ») : il ne se comprend pas seul")
            fin = next((w for w in mots if m["fin"] - .3 <= w[2] <= m["fin"] + 1.5 and re.search(r"[.!?…]$", w[0].strip())), None)
            if fin:
                m["fin"] = round(fin[2] + .15, 2)
            else:
                print(f"attention : moment {k} finit au milieu d'une phrase")
        out.append(m)
    return out, refus


def verifier(moments, total, mini, maxi):
    erreurs, prec = [], None
    for i, m in enumerate(sorted(moments, key=lambda m: m["debut"]), 1):
        d = m["fin"] - m["debut"]
        if d < mini or d > maxi:
            erreurs.append(f"moment {i} ({m['debut']}-{m['fin']}) dure {d:.1f} s, hors de {mini}-{maxi} s")
        if m["debut"] < 0 or m["fin"] > total + 0.5:
            erreurs.append(f"moment {i} sort de la vidéo ({total:.1f} s)")
        if prec and m["debut"] < prec["fin"]:
            erreurs.append(f"moment {i} chevauche le précédent")
        prec = m
    return erreurs


def ecrire_ass(m, mots, mode, j, f):
    c = C.couleurs(j)
    st = [C.ass_style("Titre", j["polices"]["titres"], 70, c["texte"], c["surface"], align=5, marges=(90, 90, 0), contour=22, boite=True),
          C.ass_style("ST", j["polices"]["texte"], 64, c["texte"], c["surface"], align=5, marges=(150, 150, 0), contour=16, boite=True)]
    l = []
    d = m["fin"] - m["debut"]
    if m.get("titre"):
        l.append(C.ass_ligne(0, d, "Titre", f"{{\\pos(540,{Y_TITRE[mode]})}}" + C.ass_texte(m["titre"])))
    rel = [(w[0], w[1] - m["debut"], w[2] - m["debut"]) for w in mots if m["debut"] <= w[1] < m["fin"]]
    b = C.blocs(rel, 3, 15, capitales=True)
    for k, (a, e, t) in enumerate(b):
        e = min(e + .3, b[k + 1][0] if k + 1 < len(b) else d)
        l.append(C.ass_ligne(max(0, a - 2 / 30), e, "ST", f"{{\\fad(80,0)}}{{\\pos(540,{Y_ST[mode]})}}" + C.ass_texte(t), 1))
    f.write_text(C.ass_entete(1080, 1920, st) + "".join(l), encoding="utf-8")
    return bool(l)


def decouper(video, moments, sortie, mode="buste", mini=15, maxi=90, mots_json=None, centre=.5, miroir=False, apercu=False,
             charte=None):
    C.verifier_ffmpeg()
    i = C.infos(video)
    mots = C.lire_mots(mots_json) if mots_json else []
    refus = []
    if mots:
        moments, refus = caler(moments, mots, mini, maxi)
    erreurs = refus + verifier(moments, i["duree"], mini, maxi)
    if erreurs:
        raise SystemExit("Refusé :\n- " + "\n- ".join(erreurs))
    os.makedirs(sortie, exist_ok=True)
    j = C.charte(charte)
    faits = []
    with tempfile.TemporaryDirectory() as tmp, C.verrou():
        for k, m in enumerate(moments, 1):
            f = os.path.join(sortie, f"short-{k:02d}.mp4")
            ass = Path(tmp) / f"s{k}.ass"
            a_ass = ecrire_ass(m, mots, mode, j, ass)
            cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(m["debut"]), "-to", str(m["fin"]), "-i", video,
                   "-filter_complex", filtre(mode, centre, miroir, ass if a_ass else None, j, apercu), "-map", "[out]"]
            if i["son"]:
                cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
            C.run(cmd + C.encodeur(apercu) + ["-movflags", "+faststart", f], basse=True)
            faits.append({"fichier": os.path.basename(f), "titre": m.get("titre", ""), "debut": m["debut"], "fin": m["fin"]})
            print(f"{f} ({m['fin'] - m['debut']:.0f} s) {m.get('titre', '')}")
    with open(os.path.join(sortie, "shorts.json"), "w", encoding="utf-8") as fh:
        json.dump(faits, fh, ensure_ascii=False, indent=2)
    return faits


def taille(f):
    i = C.infos(f)
    return f"{i['w']},{i['h']}"


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        v = os.path.join(tmp, "longue.mp4")
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=50:size=1280x720:rate=25",
               "-f", "lavfi", "-i", "sine=frequency=440:duration=50", "-shortest", "-c:v", "libx264", "-c:a", "aac", v])
        faits = decouper(v, [{"debut": 2, "fin": 19, "titre": "un"}, {"debut": 25, "fin": 42, "titre": "deux"}],
                         os.path.join(tmp, "out"), "flou")
        assert len(faits) == 2 and taille(os.path.join(tmp, "out", "short-01.mp4")) == "1080,1920"
        decouper(v, [{"debut": 5, "fin": 21}], os.path.join(tmp, "out2"), "centre")
        assert taille(os.path.join(tmp, "out2", "short-01.mp4")) == "1080,1920"
        try:
            decouper(v, [{"debut": 0, "fin": 5}], os.path.join(tmp, "out3"))
            raise AssertionError("moment trop court accepté")
        except SystemExit as e:
            assert "hors de" in str(e)
        mots = [(f" mot{k}{'.' if k % 6 == 5 else ''}", k * .5 + .1, k * .5 + .4) for k in range(96)]
        mots[42] = (" Donc", 21.1, 21.4)
        tj = Path(tmp) / "t.json"
        C.ecrire_mots(mots, tj)
        cal, refus = caler([{"debut": 3.0, "fin": 20.6}, {"debut": 21.2, "fin": 38.0}], mots, 15, 90)
        assert cal[0]["debut"] == 3.05 and cal[0]["fin"] == 21.05 and len(refus) == 1 and "Donc" in refus[0], (cal, refus)
        faits = decouper(v, [{"debut": 3.0, "fin": 20.6, "titre": "Le titre"}], os.path.join(tmp, "out4"), "buste",
                         mots_json=tj, miroir=True, apercu=True)
        assert faits[0]["fin"] == 21.05 and taille(os.path.join(tmp, "out4", "short-01.mp4")) == "540,960"
        try:
            decouper(v, [{"debut": 21.2, "fin": 38.0}], os.path.join(tmp, "out5"), mots_json=tj)
            raise AssertionError("mot de liaison accepté")
        except SystemExit as e:
            assert "liaison" in str(e)
    print("AUTO-TEST OK")


def main():
    p = argparse.ArgumentParser(description="Vidéo longue + moments -> Shorts 1080x1920 (ffmpeg seul).")
    p.add_argument("video", nargs="?")
    p.add_argument("moments", nargs="?")
    p.add_argument("-o", "--sortie", default="shorts")
    p.add_argument("--mode", choices=("buste", "flou", "centre"), default="buste")
    p.add_argument("--mots")
    p.add_argument("--centre", type=float, default=.5)
    p.add_argument("--miroir", action="store_true")
    p.add_argument("--min", type=float, default=15)
    p.add_argument("--max", type=float, default=90)
    p.add_argument("--apercu", action="store_true")
    p.add_argument("--charte")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        return auto_test()
    if not (a.video and a.moments):
        p.print_help()
        return
    with open(a.moments, encoding="utf-8") as f:
        moments = json.load(f)
    decouper(a.video, moments, a.sortie, a.mode, a.min, a.max, a.mots, a.centre, a.miroir, a.apercu, a.charte)


if __name__ == "__main__":
    main()
