"""transcrire.py : une prise (vidéo ou son) -> transcription mot par mot, au format Whisper, en local et gratuit.

  python transcrire.py prise.mp4 transcription.json [--moteur auto|faster-whisper|ffmpeg] [--langue fr]
                       [--modele large-v3-turbo] [--modele-ggml chemin/ggml-large-v3-turbo.bin]
  python transcrire.py --test

Deux moteurs :
  faster-whisper (conseillé, celui du système d'origine) : pip install faster-whisper. Le modèle se télécharge seul
      au premier usage (environ 1,5 Go pour large-v3-turbo). Tourne sur le processeur ; une prise de 15 minutes
      prend quelques minutes.
  ffmpeg : le filtre whisper intégré aux versions récentes de ffmpeg (paquet « full » de gyan.dev sous Windows).
      Aucun paquet Python, mais un fichier modèle ggml à télécharger une fois (huggingface.co/ggerganov/whisper.cpp).
      Ce chemin n'a pas tourné dans le système d'origine : vérifie la première transcription mot à mot.
auto essaie faster-whisper, puis ffmpeg si --modele-ggml est donné.

Sortie : segments[].words[] avec word (espace de tête gardée), start, end, en secondes. Tous les outils vidéo du kit
la lisent (couper, habiller, gabarit, decoupe).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import commun as C  # noqa: E402


def par_faster_whisper(src, modele, langue):
    from faster_whisper import WhisperModel  # pip install faster-whisper
    m = WhisperModel(modele, device="cpu", compute_type="int8")
    segs, _ = m.transcribe(str(src), language=langue, word_timestamps=True)
    return [(w.word, w.start, w.end) for s in segs for w in (s.words or [])]


def lignes_ffmpeg(lignes):
    """Lignes JSON du filtre whisper de ffmpeg ({"start": ms, "end": ms, "text": "..."}) -> [(mot, début, fin)].
    Avec max_len=1, un mot peut arriver en plusieurs morceaux : un morceau sans espace de tête se colle au précédent."""
    out = []
    for l in lignes:
        l = l.strip()
        if not l.startswith("{"):
            continue
        j = json.loads(l)
        t, d, e = j.get("text", ""), j["start"] / 1000, j["end"] / 1000
        if not t.strip():
            continue
        if out and not t.startswith(" "):
            out[-1] = (out[-1][0] + t, out[-1][1], e)
        else:
            out.append((t if t.startswith(" ") else " " + t, d, e))
    return out


def par_ffmpeg(src, modele_ggml, langue):
    if not modele_ggml or not Path(modele_ggml).exists():
        raise SystemExit("Moteur ffmpeg : donne --modele-ggml (fichier .bin de whisper.cpp).")
    with tempfile.TemporaryDirectory() as tmp:
        sortie = Path(tmp) / "w.jsonl"
        filtre = (f"whisper=model={C.chemin_filtre(modele_ggml)}:language={langue}:format=json:max_len=1"
                  f":destination={C.chemin_filtre(sortie)}")
        C.run(["ffmpeg", "-v", "error", "-i", src, "-vn", "-af", filtre, "-f", "null", "-"], basse=True)
        return lignes_ffmpeg(sortie.read_text(encoding="utf-8").splitlines())


def transcrire(src, sortie, moteur="auto", langue="fr", modele="large-v3-turbo", modele_ggml=None):
    C.verifier_ffmpeg()
    mots = None
    if moteur in ("auto", "faster-whisper"):
        try:
            mots = par_faster_whisper(src, modele, langue)
        except ImportError:
            if moteur == "faster-whisper" or not modele_ggml:
                raise SystemExit("faster-whisper absent : pip install faster-whisper (ou --moteur ffmpeg --modele-ggml ...).")
    if mots is None:
        mots = par_ffmpeg(src, modele_ggml, langue)
    if not mots:
        raise SystemExit("Aucune parole reconnue.")
    C.ecrire_mots(mots, sortie, langue)
    print(f"{len(mots)} mots -> {sortie}")


def auto_test():
    l = ['{"start":0,"end":400,"text":" Bonjour"}', '{"start":500,"end":600,"text":" l"}',
         '{"start":600,"end":900,"text":"\'ami."}', "bruit", '{"start":900,"end":950,"text":" "}']
    assert lignes_ffmpeg(l) == [(" Bonjour", 0, .4), (" l'ami.", .5, .9)], lignes_ffmpeg(l)
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "t.json"
        C.ecrire_mots(lignes_ffmpeg(l), f)
        j = json.loads(f.read_text(encoding="utf-8"))
        assert j["segments"][0]["words"][1]["word"] == " l'ami." and C.lire_mots(f)[0] == (" Bonjour", 0, .4)
    try:
        import faster_whisper  # noqa: F401
        print("faster-whisper installé")
    except ImportError:
        print("faster-whisper absent (pip install faster-whisper) : seul le moteur ffmpeg est possible")
    print("AUTO-TEST OK")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Prise -> transcription mot par mot (format Whisper).")
    p.add_argument("src", nargs="?")
    p.add_argument("sortie", nargs="?")
    p.add_argument("--moteur", choices=("auto", "faster-whisper", "ffmpeg"), default="auto")
    p.add_argument("--langue", default="fr")
    p.add_argument("--modele", default="large-v3-turbo")
    p.add_argument("--modele-ggml")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        auto_test()
    elif a.src and a.sortie:
        transcrire(a.src, a.sortie, a.moteur, a.langue, a.modele, a.modele_ggml)
    else:
        p.print_help()
