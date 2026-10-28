"""cerveau.py : chercher dans le wiki par le SENS, pas seulement par les mots.

Usage :  python scripts/cerveau.py "ma question"            (10 meilleurs passages)
         python scripts/cerveau.py "ma question" --top 20
Installation du mode « sens » (une fois) :  pip install fastembed numpy
Sans fastembed, le script marche quand même en mode mots-clés.

Il découpe chaque page de wiki/ en paragraphes, calcule leur sens (embeddings, modèle
multilingue local, rien n'est envoyé sur internet) et garde un cache dans
outputs/cerveau-cache.npz : seules les pages modifiées sont recalculées.
wiki/finances/ est toujours exclu.
"""
from __future__ import annotations

import argparse
import hashlib
import re
import sys
import warnings
from pathlib import Path

warnings.filterwarnings("ignore")  # fastembed affiche des avertissements sans gravité qui inquiètent les débutants

ROOT = Path(__file__).resolve().parent.parent
WIKI = ROOT / "wiki"
CACHE = ROOT / "outputs" / "cerveau-cache.npz"
MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
EXCLUS = ("finances", "archive")


def passages() -> list[tuple[str, str]]:
    """(chemin relatif, texte) pour chaque paragraphe utile du wiki."""
    out = []
    for p in sorted(WIKI.rglob("*.md")):
        rel = p.relative_to(ROOT).as_posix()
        if any(f"/{x}/" in f"/{rel}" for x in EXCLUS):
            continue
        txt = p.read_text(encoding="utf-8", errors="ignore")
        txt = re.sub(r"\A---.*?\n---\n", "", txt, flags=re.S)  # frontmatter
        for bloc in re.split(r"\n\s*\n", txt):
            bloc = bloc.strip()
            if len(bloc) >= 60:
                out.append((rel, bloc[:1500]))
    return out


def mots(texte: str) -> set[str]:
    return {m for m in re.findall(r"\w+", texte.lower()) if len(m) > 3}


def rang_mots(question: str, items: list[tuple[str, str]]) -> list[tuple[float, int]]:
    q = mots(question)
    return sorted(((len(q & mots(t)) / (len(q) or 1), i) for i, (_, t) in enumerate(items)), reverse=True)


def rang_sens(question: str, items: list[tuple[str, str]]) -> list[tuple[float, int]]:
    import numpy as np
    from fastembed import TextEmbedding

    model = TextEmbedding(model_name=MODEL)
    cles = [hashlib.sha1((r + t).encode()).hexdigest() for r, t in items]
    ancien = {}
    if CACHE.exists():
        d = np.load(CACHE, allow_pickle=False)
        ancien = dict(zip(d["cles"].tolist(), d["vecs"]))
    manquants = [i for i, k in enumerate(cles) if k not in ancien]
    if manquants:
        print(f"[cerveau] calcul du sens de {len(manquants)} passage(s)...", file=sys.stderr)
        for i, v in zip(manquants, model.embed([items[i][1] for i in manquants])):
            ancien[cles[i]] = v
    vecs = np.array([ancien[k] for k in cles], dtype="float32")
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    np.savez(CACHE, cles=np.array(cles), vecs=vecs)
    q = np.array(list(model.embed([question]))[0], dtype="float32")
    scores = vecs @ q / (np.linalg.norm(vecs, axis=1) * np.linalg.norm(q) + 1e-9)
    return sorted(((float(s), i) for i, s in enumerate(scores)), reverse=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--top", type=int, default=10)
    a = ap.parse_args()
    items = passages()
    if not items:
        print("Aucune page trouvée dans wiki/.")
        return 1
    try:
        classement, mode = rang_sens(a.question, items), "sens"
    except ImportError:
        classement, mode = rang_mots(a.question, items), "mots-clés (pip install fastembed numpy pour le sens)"
    vus = set()
    for score, i in classement:
        if len(vus) >= a.top:
            break
        rel, txt = items[i]
        if (rel, txt[:80]) in vus:
            continue
        vus.add((rel, txt[:80]))
        print(f"\n[{score:.2f}] {rel}\n{txt[:400]}")
    print(f"\n(mode : {mode})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
