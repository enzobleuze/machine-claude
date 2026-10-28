"""decoupe.py : une vidéo longue + une liste de moments -> des Shorts verticaux 1080x1920, avec ffmpeg seul.

  python decoupe.py video.mp4 moments.json [-o dossier] [--mode flou|centre] [--min 15] [--max 90]
  python decoupe.py --test

moments.json : [{"debut": 81.5, "fin": 124.0, "titre": "La phrase qui accroche"}, ...]
  (les moments sont choisis par Claude dans la transcription : compris seuls, accroche dans les 3 premières
  secondes, idée complète, aucun appel à l'action au milieu)

Modes :
  flou   (défaut) la vidéo entière au milieu, sur la même image agrandie et floutée. Rien n'est coupé :
         idéal pour une vidéo 16:9 filmée large. Place libre en haut pour un titre ajouté au montage.
  centre recadrage 9:16 au centre. Net seulement si la source est en 4K : en 1080p, une découpe
         verticale ne fait que 608 px de large et sort floue.

Refus avant rendu : moment trop court ou trop long, moments qui se chevauchent, moment hors de la vidéo.
Sortie : short-01.mp4, short-02.mp4... et shorts.json (titre, début, fin, fichier) pour la distribution.
"""
import argparse, json, os, shutil, subprocess, sys, tempfile

FILTRES = {
    "flou": "[0:v]split[a][b];[a]scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,boxblur=30:2[f];"
            "[b]scale=1080:-2[v];[f][v]overlay=(W-w)/2:(H-h)/2,setsar=1[out]",
    "centre": "[0:v]crop='min(iw,ih*9/16)':'min(ih,iw*16/9)',scale=1080:1920,setsar=1[out]",
}


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"Erreur ffmpeg :\n{r.stderr[-800:]}")
    return r.stdout


def duree(f):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", f]).strip())


def a_de_l_audio(f):
    return bool(run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries", "stream=index", "-of", "csv=p=0", f]).strip())


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


def decouper(video, moments, sortie, mode="flou", mini=15, maxi=90):
    for outil in ("ffmpeg", "ffprobe"):
        if not shutil.which(outil):
            raise SystemExit(f"{outil} introuvable : installe ffmpeg.")
    total = duree(video)
    erreurs = verifier(moments, total, mini, maxi)
    if erreurs:
        raise SystemExit("Refusé :\n- " + "\n- ".join(erreurs))
    os.makedirs(sortie, exist_ok=True)
    son = a_de_l_audio(video)
    faits = []
    for i, m in enumerate(moments, 1):
        f = os.path.join(sortie, f"short-{i:02d}.mp4")
        cmd = ["ffmpeg", "-y", "-v", "error", "-ss", str(m["debut"]), "-to", str(m["fin"]), "-i", video,
               "-filter_complex", FILTRES[mode], "-map", "[out]"]
        if son:
            cmd += ["-map", "0:a:0", "-c:a", "aac", "-b:a", "160k", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "20", "-pix_fmt", "yuv420p", "-movflags", "+faststart",
                "-threads", "4", f]  # 4 fils : un rendu ne gèle pas le PC pendant qu'on travaille
        run(cmd)
        faits.append({"fichier": os.path.basename(f), "titre": m.get("titre", ""), "debut": m["debut"], "fin": m["fin"]})
        print(f"{f} ({m['fin'] - m['debut']:.0f} s) {m.get('titre', '')}")
    with open(os.path.join(sortie, "shorts.json"), "w", encoding="utf-8") as fh:
        json.dump(faits, fh, ensure_ascii=False, indent=2)
    return faits


def taille(f):
    return run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height", "-of", "csv=p=0", f]).strip()


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        v = os.path.join(tmp, "longue.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=50:size=1280x720:rate=25",
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
    print("AUTO-TEST OK")


def main():
    p = argparse.ArgumentParser(description="Vidéo longue + moments -> Shorts 1080x1920 (ffmpeg seul).")
    p.add_argument("video", nargs="?")
    p.add_argument("moments", nargs="?")
    p.add_argument("-o", "--sortie", default="shorts")
    p.add_argument("--mode", choices=list(FILTRES), default="flou")
    p.add_argument("--min", type=float, default=15)
    p.add_argument("--max", type=float, default=90)
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        return auto_test()
    if not (a.video and a.moments):
        p.print_help()
        return
    with open(a.moments, encoding="utf-8") as f:
        moments = json.load(f)
    decouper(a.video, moments, a.sortie, a.mode, a.min, a.max)


if __name__ == "__main__":
    main()
