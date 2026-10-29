"""verif.py : la garde du tournage. Vérifie une prise test de 10 secondes AVANT la séance, et dit ce que la caméra
sait vraiment filmer. Une caméra branchée au mauvais endroit enregistre en petite résolution sans prévenir.

  python verif.py prise-test.mp4 [--attendu 3840x2160] [--fps 30]   résolution, images par seconde, son, niveau, écrêtage
  python verif.py cameras [--camera "Nom de la caméra"]             Windows et Mac : caméras vues, et leurs résolutions
  python verif.py --test
Sortie 0 = prête à tourner, 1 = à corriger (la raison est écrite en clair).
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path[:0] = [str(ICI), str(ICI.parents[1] / "montage-video-code" / "outils")]
import commun as C  # noqa: E402


def niveaux(f) -> tuple[float, float]:
    r = C.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-vn", "-af", "volumedetect", "-f", "null", "-"])
    moy = re.search(r"mean_volume: (-?[\d.]+|-inf) dB", r.stderr)
    pic = re.search(r"max_volume: (-?[\d.]+|-inf) dB", r.stderr)
    return float(moy.group(1)) if moy else -91.0, float(pic.group(1)) if pic else -91.0


def verifier(f, attendu=None, fps=None) -> tuple[list[str], list[str]]:
    """-> (problèmes bloquants, remarques)."""
    i, pb, rq = C.infos(f), [], []
    rq.append(f"{i['w']}x{i['h']} à {i['fps']} images/s, {i['duree']:.1f} s, son : {'oui' if i['son'] else 'non'}")
    if attendu:
        w, h = (int(x) for x in attendu.lower().split("x"))
        if max(i["w"], i["h"]) < max(w, h) or min(i["w"], i["h"]) < min(w, h):
            pb.append(f"résolution {i['w']}x{i['h']} au lieu de {attendu} : vérifie le câble (port USB 3 direct, sans "
                      "concentrateur) et le réglage du logiciel (résolution de base et de sortie)")
    if fps and abs(i["fps"] - fps) > .6:
        rq.append(f"{i['fps']} images/s au lieu de {fps} : vérifie le réglage vidéo du logiciel")
    if i["duree"] < 3:
        pb.append("prise trop courte pour juger : filme 10 secondes en parlant normalement")
    if not i["son"]:
        pb.append("pas de son : le micro n'est pas dans la scène enregistrée")
    else:
        moy, pic = niveaux(f)
        if pic >= -0.5:
            pb.append(f"le son sature (pic à {pic} dB) : baisse le gain du micro")
        elif moy < -42:
            pb.append(f"son trop faible (moyenne {moy} dB) : rapproche le micro ou monte le gain")
        else:
            rq.append(f"son : moyenne {moy} dB, pic {pic} dB")
    if i["h"] > i["w"]:
        rq.append("prise verticale : parfaite pour un Reel, trop étroite pour une vidéo longue")
    elif min(i["w"], i["h"]) < 2160:
        rq.append("sous la 4K : un recadrage vertical plein cadre sera flou (garde le mode buste ou flou pour les Shorts)")
    return pb, rq


def resolutions(texte: str) -> list[tuple[int, int]]:
    """Les tailles listées par ffmpeg pour une caméra (s=3840x2160, 1920x1080...), de la plus grande à la plus petite."""
    t = {(int(a), int(b)) for a, b in re.findall(r"(?:s=|\b)(\d{3,4})x(\d{3,4})\b", texte)}
    return sorted(t, key=lambda x: x[0] * x[1], reverse=True)


def cameras(nom=None) -> None:
    if sys.platform == "darwin":
        r = subprocess.run(["ffmpeg", "-hide_banner", "-f", "avfoundation", "-list_devices", "true", "-i", ""], capture_output=True, text=True)
        print(r.stderr)
        return
    if nom:
        r = subprocess.run(["ffmpeg", "-hide_banner", "-list_options", "true", "-f", "dshow", "-i", f"video={nom}"], capture_output=True, text=True)
        res = resolutions(r.stderr)
        if not res:
            print(r.stderr[-1500:])
            return
        print(f"{nom} : jusqu'à {res[0][0]}x{res[0][1]}")
        if res[0][0] < 3840:
            print("Pas de 4K proposée. Si la caméra filme en 4K : branche l'adaptateur sur un port USB 3 (souvent bleu, à "
                  "l'arrière du PC), sans concentrateur, puis relance.")
        return
    r = subprocess.run(["ffmpeg", "-hide_banner", "-list_devices", "true", "-f", "dshow", "-i", "dummy"], capture_output=True, text=True)
    for n in re.findall(r'"([^"]+)" \(video\)', r.stderr):
        print(f"caméra : {n}   (détail : python verif.py cameras --camera \"{n}\")")
    for n in re.findall(r'"([^"]+)" \(audio\)', r.stderr):
        print(f"micro  : {n}")


def auto_test():
    texte = "  pixel_format=nv12  min s=1280x720 fps=30\n  vcodec=mjpeg min s=3840x2160 fps=30\n s=1920x1080"
    assert resolutions(texte)[0] == (3840, 2160) and len(resolutions(texte)) == 3
    with tempfile.TemporaryDirectory() as tmp:
        v = C.test_video(Path(tmp) / "test.mp4", 5.0, "1280x720")
        pb, rq = verifier(v, "1920x1080", 25)
        assert any("1280x720 au lieu" in p for p in pb), pb
        pb, rq = verifier(v, "1280x720", 25)
        assert pb == [] and any("sous la 4K" in r for r in rq), (pb, rq)
        muet = C.test_video(Path(tmp) / "muet.mp4", 5.0, son=False)
        assert any("pas de son" in p for p in verifier(muet)[0])
        fort = Path(tmp) / "fort.mp4"
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=4:size=320x240:rate=25", "-f", "lavfi", "-i",
               "aevalsrc='sin(2*PI*440*t)':d=4", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "pcm_s16le", fort.with_suffix(".mov")])
        assert any("sature" in p for p in verifier(fort.with_suffix(".mov"))[0])
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Garde du tournage : prise test et caméras.")
    ap.add_argument("prise", nargs="?")
    ap.add_argument("--attendu")
    ap.add_argument("--fps", type=float)
    ap.add_argument("--camera")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.prise == "cameras":
        cameras(a.camera)
    elif a.prise:
        C.verifier_ffmpeg()
        pb, rq = verifier(a.prise, a.attendu, a.fps)
        print("\n".join([f"  {r}" for r in rq] + [f"  À CORRIGER : {p}" for p in pb]))
        print("PRÊTE À TOURNER" if not pb else "À CORRIGER AVANT DE TOURNER")
        sys.exit(1 if pb else 0)
    else:
        ap.print_help()
