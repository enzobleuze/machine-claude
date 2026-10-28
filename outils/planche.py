"""planche.py : plusieurs images (ou les images clés d'une vidéo) en UNE seule image quadrillée.

Pourquoi : Claude paie cher chaque image lue, et chaque image reste dans le contexte.
Une planche de 16 vignettes coûte à peu près le prix d'une seule image.
Lis la planche d'abord, puis ouvre en grand seulement l'image choisie.

Seul besoin : ffmpeg et ffprobe sur le PATH (Windows : winget install ffmpeg ; Mac : brew install ffmpeg ;
Linux : apt install ffmpeg). Aucune bibliothèque Python à installer.

  python outils/planche.py "dossier/*.png" -o planche.jpg
  python outils/planche.py video.mp4 --n 12 -o planche.jpg
  python outils/planche.py video.mp4 --at 0,3.5,12 -o planche.jpg     (instants exacts, en secondes)
  python outils/planche.py --test                                    (auto-test, crée une vidéo de test)

La légende (numéro de case -> fichier ou instant) s'écrit dans le terminal et dans <sortie>.txt.
Les cases se lisent de gauche à droite, puis de haut en bas.
"""
import argparse, glob, math, os, shutil, subprocess, sys, tempfile

MAX_LARGEUR = 1568  # au-delà, l'image est réduite par l'API : des pixels payés pour rien
VIDEO = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"Erreur ffmpeg : {' '.join(cmd[:4])}...\n{r.stderr[-800:]}")
    return r.stdout


def duree(video):
    return float(run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", video]).strip())


def extraire(video, instants, dossier):
    sorties = []
    for i, t in enumerate(instants):
        f = os.path.join(dossier, f"f{i:02d}.png")
        run(["ffmpeg", "-y", "-v", "error", "-ss", f"{t:.2f}", "-i", video, "-frames:v", "1", f])
        sorties.append(f)
    return sorties


def planche(images, sortie, cols, largeur):
    n = len(images)
    cols = min(cols, n)
    rangs = math.ceil(n / cols)
    w = largeur // cols
    w -= w % 2
    h = int(w * 16 / 9) if rangs > 1 or cols > 2 else w  # case portrait par défaut (Reels, carrousels)
    h -= h % 2
    cmd = ["ffmpeg", "-y", "-v", "error"]
    for im in images:
        cmd += ["-i", im]
    filtres = [f"[{i}:v]scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:color=0x202020,"
               f"drawbox=x=0:y=0:w=iw:h=ih:color=0x808080:t=2[c{i}]" for i in range(n)]
    if n == 1:
        filtres.append("[c0]null[out]")
    else:
        disposition = "|".join(f"{(i % cols) * w}_{(i // cols) * h}" for i in range(n))
        entrees = "".join(f"[c{i}]" for i in range(n))
        filtres.append(f"{entrees}xstack=inputs={n}:layout={disposition}:fill=0x202020[out]")
    cmd += ["-filter_complex", ";".join(filtres), "-map", "[out]", "-frames:v", "1", "-q:v", "3", sortie]
    run(cmd)


def main(argv=None):
    p = argparse.ArgumentParser(description="Planche contact d'images ou d'une vidéo (ffmpeg seul).")
    p.add_argument("entrees", nargs="*", help="images, motifs (*.png) ou UNE vidéo")
    p.add_argument("-o", "--sortie", default="planche.jpg")
    p.add_argument("--n", type=int, default=16, help="nombre d'images tirées d'une vidéo (16 au plus conseillé)")
    p.add_argument("--at", help="instants exacts en secondes, séparés par des virgules")
    p.add_argument("--cols", type=int, default=4)
    p.add_argument("--largeur", type=int, default=MAX_LARGEUR)
    p.add_argument("--test", action="store_true")
    a = p.parse_args(argv)
    if a.test:
        return auto_test()
    for outil in ("ffmpeg", "ffprobe"):
        if not shutil.which(outil):
            raise SystemExit(f"{outil} introuvable. Installe ffmpeg (voir l'en-tête de ce fichier).")
    fichiers = []
    for e in a.entrees:
        fichiers += sorted(glob.glob(e)) or [e]
    fichiers = [f for f in fichiers if os.path.isfile(f)]
    if not fichiers:
        raise SystemExit("Aucun fichier trouvé.")
    with tempfile.TemporaryDirectory() as tmp:
        legende = []
        if len(fichiers) == 1 and fichiers[0].lower().endswith(VIDEO):
            video = fichiers[0]
            if a.at:
                instants = [float(x) for x in a.at.split(",")]
            else:
                d = duree(video)
                instants = [d * (i + 0.5) / a.n for i in range(a.n)]
            images = extraire(video, instants, tmp)
            legende = [f"{i + 1} : {t:.1f} s" for i, t in enumerate(instants)]
        else:
            if len(fichiers) > 25:
                print(f"{len(fichiers)} images : seules les 25 premières entrent. Fais plusieurs planches.")
                fichiers = fichiers[:25]
            images = fichiers
            legende = [f"{i + 1} : {os.path.basename(f)}" for i, f in enumerate(fichiers)]
        planche(images, a.sortie, a.cols, a.largeur)
    with open(os.path.splitext(a.sortie)[0] + ".txt", "w", encoding="utf-8") as f:
        f.write("\n".join(legende) + "\n")
    print(f"Planche écrite : {a.sortie} ({len(images)} cases)")
    print("\n".join(legende))
    return 0


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        v = os.path.join(tmp, "test.mp4")
        run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=6:size=720x1280:rate=10", v])
        out = os.path.join(tmp, "planche.jpg")
        main([v, "--n", "6", "-o", out])
        assert os.path.getsize(out) > 5000, "planche vide"
        legende = open(os.path.splitext(out)[0] + ".txt", encoding="utf-8").read().splitlines()
        assert len(legende) == 6, legende
        out2 = os.path.join(tmp, "planche-images.jpg")
        main([os.path.join(tmp, "*.jpg"), "-o", out2])
        assert os.path.getsize(out2) > 1000
    print("AUTO-TEST OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
