"""commun.py : la boîte partagée des outils vidéo du kit (couper, habiller, gabarit, decoupe, mixage, revue, rythme).

Ce qu'elle fait :
  - lancer ffmpeg et lire une vidéo (durée, taille, images par seconde, son) ;
  - choisir l'encodeur : la carte graphique si elle sait encoder (NVIDIA, AMD, Intel, Mac), sinon libx264 ;
  - poser le verrou « un seul rendu lourd à la fois », en priorité basse ;
  - lire la charte de la marque (bibliotheque/marque/charte-jetons.json), sinon la charte « simple » ;
  - écrire des sous-titres et des cartes en ASS (brûlés par ffmpeg), toujours aux couleurs de la charte ;
  - lire une transcription (format Whisper) et mesurer le volume de la voix toutes les 10 ms.

Rien à installer : Python 3.10 ou plus récent, et ffmpeg 7.1 ou plus récent
(Windows : winget install ffmpeg ; Mac : brew install ffmpeg ; Linux : sudo apt install ffmpeg).
Les outils vont tous dans le même dossier outils/ du vault : ils s'importent entre eux.

  python commun.py --test
"""
from __future__ import annotations

import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from array import array
from contextlib import contextmanager
from pathlib import Path

ICI = Path(__file__).resolve().parent

# Copie exacte de jetons(PROPOSITIONS["simple"]) de charte.py (brique charte-graphique). Le test vérifie l'égalité
# quand charte.py est à portée. Sert tant que la personne n'a pas encore de charte.
SIMPLE = {
    "nom": "Simple", "principal": "clair",
    "clair": {"fond": "#fafaf8", "surface": "#f1f1ef", "surface_2": "#e8e8e6", "ligne": "#d7d7d5", "texte": "#1d1d1b",
              "texte_doux": "#6a6a68", "accent": "#2f5bd3", "accent_texte": "#ffffff", "accent_2": "#284289",
              "ok": "#2e8b57", "alerte": "#c77f1c", "erreur": "#c8374d"},
    "sombre": {"fond": "#141413", "surface": "#1d1d1c", "surface_2": "#262625", "ligne": "#393938", "texte": "#fafaf8",
               "texte_doux": "#aaaaa8", "accent": "#4068d7", "accent_texte": "#ffffff", "accent_2": "#8aa2e4",
               "ok": "#2e8b57", "alerte": "#d98a1f", "erreur": "#c8374d"},
    "polices": {"titres": "Inter", "texte": "Inter"}, "rayon": 10, "logo": "", "mots": ["net", "lisible", "sobre"],
}
CHARTE_REL = "bibliotheque/marque/charte-jetons.json"
VERROU = Path(tempfile.gettempdir()) / "montage-rendu.lock"
GPU = {  # réglages de qualité proches d'un crf 18 de libx264
    "h264_nvenc": ["-preset", "p5", "-rc", "vbr", "-cq", "19", "-b:v", "0"],
    "h264_amf": ["-quality", "quality", "-rc", "cqp", "-qp_i", "18", "-qp_p", "20"],
    "h264_qsv": ["-global_quality", "20"],
    "h264_videotoolbox": ["-q:v", "65"],
}
CPU = ["-c:v", "libx264", "-preset", "medium", "-crf", "18", "-threads", "4"]  # 4 fils : le PC reste utilisable
APERCU = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "28", "-threads", "4"]
_ENC: list[str] | None = None


# ------------------------------------------------------------------------------------------------ ffmpeg
def verifier_ffmpeg() -> None:
    for outil in ("ffmpeg", "ffprobe"):
        if not shutil.which(outil):
            raise SystemExit(f"{outil} introuvable. Windows : winget install ffmpeg ; Mac : brew install ffmpeg.")


def run(cmd: list, basse: bool = False, cwd=None, ok_codes=(0,)) -> subprocess.CompletedProcess:
    """Lance une commande. basse=True : priorité basse (un rendu ne gèle pas le PC). Lève SystemExit si elle échoue."""
    kw = {}
    if basse:
        if os.name == "nt":
            kw["creationflags"] = subprocess.BELOW_NORMAL_PRIORITY_CLASS
        else:
            kw["preexec_fn"] = lambda: os.nice(10)
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, encoding="utf-8", errors="replace",
                       cwd=cwd, **kw)
    if r.returncode not in ok_codes:
        raise SystemExit(f"Échec de {Path(str(cmd[0])).name} :\n{r.stderr[-1200:]}")
    return r


def infos(f) -> dict:
    """{'duree', 'w', 'h', 'fps', 'son'} d'une vidéo (ou d'un son : w = h = 0)."""
    r = run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height,r_frame_rate",
             "-of", "json", f])
    j = json.loads(r.stdout)
    v = next((s for s in j.get("streams", []) if s.get("codec_type") == "video"), {})
    n, _, d = (v.get("r_frame_rate") or "0/1").partition("/")
    return {"duree": float(j.get("format", {}).get("duration") or 0), "w": int(v.get("width") or 0),
            "h": int(v.get("height") or 0), "fps": round(float(n) / float(d or 1), 3) if float(d or 1) else 0.0,
            "son": any(s.get("codec_type") == "audio" for s in j.get("streams", []))}


def encodeur(apercu: bool = False) -> list[str]:
    """Arguments d'encodage vidéo. La carte graphique si elle encode vraiment (testée une fois), sinon libx264.
    MONTAGE_CPU=1 force le processeur. Un aperçu de revue reste en libx264 rapide et léger."""
    global _ENC
    if apercu:
        return APERCU + ["-pix_fmt", "yuv420p"]
    if _ENC is None:
        _ENC = CPU
        if os.environ.get("MONTAGE_CPU") != "1":
            noms = ["h264_videotoolbox"] if sys.platform == "darwin" else ["h264_nvenc", "h264_amf", "h264_qsv"]
            for nom in noms:
                r = subprocess.run(["ffmpeg", "-v", "error", "-f", "lavfi", "-i", "color=s=256x256:d=0.2", "-c:v", nom,
                                    "-f", "null", "-"], capture_output=True)
                if r.returncode == 0:
                    _ENC = ["-c:v", nom] + GPU[nom]
                    break
    return _ENC + ["-pix_fmt", "yuv420p"]


def _vivant(pid: int) -> bool:
    if os.name == "nt":  # os.kill tuerait le processus sous Windows : on demande à tasklist
        r = subprocess.run(["tasklist", "/FI", f"PID eq {pid}", "/NH"], capture_output=True, text=True)
        return str(pid) in r.stdout
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


@contextmanager
def verrou(fichier: Path = VERROU):
    """Un seul rendu lourd à la fois sur le PC (trois rendus en parallèle ont déjà gelé un ordinateur)."""
    if fichier.exists():
        try:
            pid, debut = fichier.read_text(encoding="utf-8").split()
            if _vivant(int(pid)) and time.time() - float(debut) < 6 * 3600:
                raise SystemExit(f"Un rendu tourne déjà (processus {pid}). Attends sa fin. "
                                 f"S'il est mort, supprime {fichier}.")
        except ValueError:
            pass
    fichier.write_text(f"{os.getpid()} {time.time()}", encoding="utf-8")
    try:
        yield
    finally:
        fichier.unlink(missing_ok=True)


def chemin_filtre(p) -> str:
    """Un chemin écrit dans un filtre ffmpeg (subtitles, fontsdir) : barres obliques, deux-points échappés."""
    return "'" + str(Path(p).resolve()).replace("\\", "/").replace(":", "\\:").replace("'", "\\'") + "'"


# ------------------------------------------------------------------------------------------------ charte
def trouver(rel: str, depart=None) -> Path | None:
    """Cherche rel dans le dossier courant puis dans ses parents (le vault)."""
    d = Path(depart or Path.cwd()).resolve()
    for x in [d, *d.parents]:
        if (x / rel).exists():
            return x / rel
    return None


def charte(chemin=None) -> dict:
    """Les jetons de la charte. Ordre : chemin donné, variable CHARTE, bibliotheque/marque/charte-jetons.json
    trouvé depuis le dossier courant. Sinon la charte « simple » (clé _secours à True)."""
    p = Path(chemin) if chemin else Path(os.environ["CHARTE"]) if os.environ.get("CHARTE") else trouver(CHARTE_REL)
    if p and p.exists():
        j = json.loads(p.read_text(encoding="utf-8"))
        j["_vault"] = str(p.resolve().parents[2])
        return j
    return dict(SIMPLE, _vault=str(Path.cwd()), _secours=True)


def couleurs(j: dict, theme: str | None = None) -> dict:
    return j[theme or j.get("principal", "clair")]


def logo(j: dict) -> Path | None:
    p = Path(j.get("_vault", ".")) / j["logo"] if j.get("logo") else None
    return p if p and p.exists() else None


def dossier_polices(j: dict) -> Path | None:
    """bibliotheque/marque/polices/ : les fichiers .ttf de la charte, si elles ne sont pas installées sur le PC."""
    p = Path(j.get("_vault", ".")) / "bibliotheque/marque/polices"
    return p if p.is_dir() else None


def css(j: dict) -> str:
    """Variables CSS de la charte (même noms que charte.css), pour une page quand charte.css manque."""
    def v(t):
        x = [f"--{k.replace('_', '-')}:{c}" for k, c in j[t].items()]
        return ";".join(x + [f"--police-titres:'{j['polices']['titres']}',system-ui,sans-serif",
                             f"--police-texte:'{j['polices']['texte']}',system-ui,sans-serif", f"--rayon:{j.get('rayon', 10)}px"])
    return f':root{{{v(j["principal"])}}}\n[data-theme="clair"]{{{v("clair")}}}\n[data-theme="sombre"]{{{v("sombre")}}}\n'


# ------------------------------------------------------------------------------------------------ ASS
def ass_couleur(h: str, alpha: int = 0) -> str:
    """#rrggbb -> &HAABBGGRR (alpha 0 = opaque, 255 = transparent)."""
    h = h.lstrip("#")
    return f"&H{alpha:02X}{h[4:6]}{h[2:4]}{h[0:2]}".upper()


def ass_temps(t: float) -> str:
    t = max(0.0, t)
    cs = int(round(t * 100))
    return f"{cs // 360000}:{cs // 6000 % 60:02d}:{cs // 100 % 60:02d}.{cs % 100:02d}"


def ass_texte(s: str) -> str:
    return s.replace("\\", "/").replace("{", "(").replace("}", ")").replace("\n", "\\N")


def ass_style(nom, police, taille, texte, fond=None, gras=True, italique=False, align=2, marges=(60, 60, 60),
              contour=0, boite=False) -> str:
    """Un style ASS. boite=True : boîte pleine de couleur fond derrière le texte (contour = marge intérieure)."""
    fd = ass_couleur(fond or texte)
    return (f"Style: {nom},{police},{taille},{ass_couleur(texte)},{ass_couleur(texte)},{fd},{fd},{-1 if gras else 0},"
            f"{-1 if italique else 0},0,0,100,100,0,0,{3 if boite else 1},{contour},0,{align},{marges[0]},{marges[1]},"
            f"{marges[2]},1")


def ass_entete(w: int, h: int, styles: list[str]) -> str:
    return ("[Script Info]\nScriptType: v4.00+\nPlayResX: %d\nPlayResY: %d\nWrapStyle: 0\nScaledBorderAndShadow: yes\n\n"
            "[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, "
            "Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, "
            "MarginL, MarginR, MarginV, Encoding\n%s\n\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, "
            "MarginV, Effect, Text\n") % (w, h, "\n".join(styles))


def ass_ligne(debut, fin, style, texte, couche=0) -> str:
    return f"Dialogue: {couche},{ass_temps(debut)},{ass_temps(fin)},{style},,0,0,0,,{texte}\n"


def ass_rect(x, y, w, h, couleur, alpha=0) -> str:
    """Rectangle plein dessiné en ASS (fond de carte, panneau)."""
    return (f"{{\\an7\\pos(0,0)\\bord0\\shad0\\1c{ass_couleur(couleur)}\\1a&H{alpha:02X}&\\p1}}"
            f"m {x} {y} l {x + w} {y} {x + w} {y + h} {x} {y + h}{{\\p0}}")


def filtre_ass(ass: Path, j: dict) -> str:
    """Le filtre ffmpeg qui brûle un fichier ASS, avec le dossier des polices de la charte s'il existe."""
    f = f"subtitles=filename={chemin_filtre(ass)}"
    d = dossier_polices(j)
    return f + (f":fontsdir={chemin_filtre(d)}" if d else "")


def polices_remplacees(stderr: str) -> list[str]:
    """Lit les lignes « fontselect » de libass (ffmpeg -v verbose) : polices demandées mais remplacées."""
    out = []
    for nom, rendu in re.findall(r"fontselect: \(([^,]+), \d+, \d\) -> ([^,\s]+)", stderr):
        if re.sub(r"[\s-]", "", nom).lower() not in re.sub(r"[\s-]", "", rendu).lower() and nom not in out:
            out.append(nom)
    return out


# ------------------------------------------------------------------------------------------------ transcription
def lire_mots(f) -> list[tuple[str, float, float]]:
    """[(mot, début, fin)] depuis un JSON au format Whisper (segments[].words[]) ou une liste [{w|word, s|start, e|end}].
    Le mot garde son espace de tête (« bonjour » collé = morceau du mot précédent, comme une élision)."""
    j = json.loads(Path(f).read_text(encoding="utf-8"))
    brut = [w for s in j["segments"] for w in s.get("words", [])] if isinstance(j, dict) and "segments" in j else j
    out = []
    for w in brut:
        m = w.get("word", w.get("w", ""))
        d, e = float(w.get("start", w.get("s", 0))), float(w.get("end", w.get("e", 0)))
        if m.strip():
            out.append((m, d, max(d, e)))
    return out


def ecrire_mots(mots, f, langue="fr") -> None:
    """Écrit au format Whisper (une phrase = un segment), lisible par tous les outils du kit."""
    segs, cur = [], []
    for m in mots:
        cur.append({"word": m[0], "start": round(m[1], 3), "end": round(m[2], 3)})
        if re.search(r"[.!?…]$", m[0].strip()):
            segs.append(cur)
            cur = []
    if cur:
        segs.append(cur)
    out = {"language": langue, "segments": [{"id": i, "start": s[0]["start"], "end": s[-1]["end"],
                                             "text": "".join(w["word"] for w in s), "words": s} for i, s in enumerate(segs)]}
    out["text"] = "".join(s["text"] for s in out["segments"])
    Path(f).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")


def coller(mots):
    """Recolle les morceaux sans espace de tête (« l » + « 'envie ») au mot d'avant."""
    out = []
    for m in mots:
        if out and not m[0].startswith(" ") and out[-1][0].strip():
            out[-1] = (out[-1][0] + m[0], out[-1][1], m[2])
        else:
            out.append((m[0] if m[0].startswith(" ") else " " + m[0], m[1], m[2]))
    return out


def blocs(mots, max_mots=3, max_car=15, fin=None, capitales=False) -> list[tuple[float, float, str]]:
    """Sous-titres : blocs de 1 à max_mots mots, coupés sur la ponctuation, ponctuation gardée. [(début, fin, texte)]"""
    out, cur = [], []
    m2 = [m for m in coller(mots) if fin is None or m[1] < fin]
    for k, m in enumerate(m2):
        cur.append(m)
        if (len(cur) >= max_mots or m[0].strip()[-1:] in ",.?!…;:" or sum(len(x[0].strip()) for x in cur) >= max_car
                or k + 1 == len(m2)):
            t = " ".join(x[0].strip() for x in cur).rstrip(";:")
            out.append((cur[0][1], cur[-1][2], t.upper() if capitales else t))
            cur = []
    return out


def enveloppe(f, sr: int = 8000) -> list[float]:
    """Volume de la piste son en dBFS toutes les 10 ms (0 = le plus fort possible, -90 = silence)."""
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(f), "-vn", "-ac", "1", "-ar", str(sr), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    a = array("h")
    a.frombytes(raw[: len(raw) // 2 * 2])
    if sys.byteorder == "big":
        a.byteswap()
    hop = sr // 100
    return [20 * math.log10(math.sqrt(sum(x * x for x in a[i:i + hop]) / hop) / 32768 + 3e-5)
            for i in range(0, len(a) - hop + 1, hop)]


# ------------------------------------------------------------------------------------------------ test
def test_video(f, duree=4.0, taille="640x360", son=True, frequence=440) -> Path:
    """Fabrique une petite vidéo de test (mire + bip). Sert aux --test de tous les outils."""
    cmd = ["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", f"testsrc=duration={duree}:size={taille}:rate=25"]
    if son:
        cmd += ["-f", "lavfi", "-i", f"sine=frequency={frequence}:duration={duree}", "-shortest", "-c:a", "aac"]
    run(cmd + ["-c:v", "libx264", "-preset", "ultrafast", "-pix_fmt", "yuv420p", f])
    return Path(f)


def auto_test() -> None:
    assert ass_couleur("#2f5bd3") == "&H00D35B2F" and ass_couleur("#ffffff", 128) == "&H80FFFFFF"
    assert ass_temps(3725.456) == "1:02:05.46" and ass_texte("a{b}\nc") == "a(b)\\Nc"
    assert chemin_filtre("C:/x/y.ass").startswith("'") and "\\:" in chemin_filtre(Path.cwd() / "a.ass") or os.name != "nt"
    mots = [(" Bonjour", 0, .4), (" l", .5, .6), ("'ami,", .6, .9), (" tu", 1, 1.1), (" vas", 1.1, 1.3), (" bien", 1.3, 1.5),
            (" aujourd'hui", 1.5, 2), (" ?", 2, 2.1)]
    b = blocs(mots)
    assert b[0] == (0, .9, "Bonjour l'ami,") and all(1 <= len(t.split()) <= 3 for _, _, t in b), b
    assert blocs(mots, capitales=True)[0][2] == "BONJOUR L'AMI,"
    assert polices_remplacees("fontselect: (Fraunces, 700, 0) -> Arial-BoldMT, 0, Arial-BoldMT\n"
                              "fontselect: (Inter, 400, 0) -> Inter-Regular, 0, Inter-Regular") == ["Fraunces"]
    j = charte()
    assert j["polices"]["titres"] and couleurs(j)["accent"].startswith("#")
    kit = ICI.parents[1] / "charte-graphique" / "outils"
    if (kit / "charte.py").exists():
        sys.path.insert(0, str(kit))
        import charte as ch
        assert ch.jetons(ch.PROPOSITIONS["simple"]) == SIMPLE, "SIMPLE ne suit plus charte.py"
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "m.json"
        ecrire_mots(mots, f)
        assert lire_mots(f) == mots
        cj = Path(tmp) / "bibliotheque/marque/charte-jetons.json"
        cj.parent.mkdir(parents=True)
        cj.write_text(json.dumps(dict(SIMPLE, nom="Essai")), encoding="utf-8")
        assert charte(cj)["nom"] == "Essai" and Path(charte(cj)["_vault"]) == Path(tmp).resolve()
        if shutil.which("ffmpeg"):
            v = test_video(Path(tmp) / "t.mp4", 1.0)
            i = infos(v)
            assert (i["w"], i["h"], i["son"]) == (640, 360, True) and abs(i["duree"] - 1.0) < .1, i
            env = enveloppe(v)
            assert 95 <= len(env) <= 110 and -30 < max(env) < -10, (len(env), max(env))  # sine de ffmpeg : 1/8 du plein volume
            assert encodeur()[0] == "-c:v"
            with verrou(Path(tmp) / "r.lock"):
                assert (Path(tmp) / "r.lock").exists()
            assert not (Path(tmp) / "r.lock").exists()
            ass = Path(tmp) / "s.ass"
            ass.write_text(ass_entete(640, 360, [ass_style("S", "Inter", 30, "#111111", "#ffffff", boite=True, contour=8)])
                           + ass_ligne(0, 1, "S", "ESSAI") + ass_ligne(0, 1, "S", ass_rect(0, 0, 100, 50, "#ff0000")),
                           encoding="utf-8")
            run(["ffmpeg", "-y", "-v", "error", "-i", v, "-vf", filtre_ass(ass, j), "-frames:v", "5", "-f", "null", "-"])
        else:
            print("ffmpeg absent : tests ffmpeg sautés")
    print("AUTO-TEST OK")


if __name__ == "__main__":
    if "--test" in sys.argv:
        auto_test()
    else:
        print(__doc__)
