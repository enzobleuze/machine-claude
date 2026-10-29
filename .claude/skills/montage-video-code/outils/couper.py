"""couper.py : une prise + sa transcription -> la prise coupée. Retire les silences, les hésitations (« euh »),
les reprises (on garde la dernière façon de dire la phrase) et les bruits de bouche ou toux entre deux mots.

  python couper.py prise.mp4 transcription.json [-o dossier] [--respiration 0.15] [--pause 0.35] [--sans-reprises] [--apercu]
  python couper.py prise.mp4 transcription.json --depuis dossier/coupes.json [-o dossier] [--apercu]
  python couper.py --test

--depuis : rendu seul, d'après un coupes.json retouché à la main (une coupe annulée, un morceau ajouté).
--apercu : rendu léger en 720p pour la revue. Le rendu final (sans --apercu) se fait une seule fois, après le OK.

Sortie dans le dossier (par défaut : à côté de la prise, dossier <nom>-coupe/) :
  coupe.mp4 ou coupe-apercu.mp4   la prise coupée, à la résolution filmée
  coupes.json                     les morceaux gardés (secondes de la prise) et chaque coupe avec sa raison
  coupes.md                       la même liste, lisible, à relire avant de monter
  transcription-coupee.json       les mots aux nouveaux temps (pour les sous-titres et les cartes)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import commun as C  # noqa: E402

HESITATIONS = {"euh", "heu", "euhm", "hum", "hmm", "mmh", "bah"}
FIN = re.compile(r"[.!?…]$")
PAUSE_MORCEAU = 0.5   # une pause plus longue sépare deux morceaux de parole (pour repérer les reprises)
CALER_MAX = 0.25      # un bord de coupe peut glisser jusque-là vers l'extérieur : Whisper finit souvent un mot trop tôt
BRUIT_MAX = 0.4       # un son fort plus court que ça, entre deux mots, sans mot dessous = lèvres, toux, raclement


def jetons(t: str) -> list[str]:
    return re.findall(r"[a-zà-ÿœæç0-9]+", t.lower())


def suite(a: list, b: list) -> int:
    """Combien de jetons de a se retrouvent dans b, dans l'ordre."""
    k = 0
    for x in b:
        if k < len(a) and x == a[k]:
            k += 1
    return k


def morceaux(idx: list[int], mots) -> list[list[int]]:
    out = []
    for i in idx:
        if out and mots[i][1] - mots[out[-1][-1]][2] < PAUSE_MORCEAU:
            out[-1].append(i)
        else:
            out.append([i])
    return out


def reprise(a: list[str], fin_a: bool, b: list[str]) -> str | None:
    """Pourquoi le morceau a (dit juste avant b) est une reprise, ou None."""
    if not a:
        return None
    n = min(3, len(a))
    if not fin_a and b[:n] == a[:n]:
        return "faux départ, repris juste après"
    court, long_ = (a, b) if len(a) <= len(b) else (b, a)
    if len(court) >= 3 and suite(court, long_) >= 0.8 * len(court):
        return "redit juste après, on garde la dernière version"
    if len(a) <= 4 and not fin_a and len({x for x in a if len(x) >= 3} & set(b)) >= 2:
        return "début reformulé juste après"
    return None


def caler(s: float, e: float, env: list[float], seuil: float, mini: float, maxi: float) -> tuple[float, float]:
    """Pousse chaque bord vers l'extérieur jusqu'au premier creux de la voix, sans dépasser CALER_MAX ni [mini, maxi]."""
    k, lim = int(e * 100), min(len(env) - 1, int((e + CALER_MAX) * 100), int(maxi * 100))
    while k < lim and env[k] > seuil:
        k += 1
    e2 = max(e, k / 100)
    k, lim = min(len(env) - 1, int(s * 100)), max(0, int((s - CALER_MAX) * 100), int(mini * 100))
    while k > lim and env[k] > seuil:
        k -= 1
    return min(s, k / 100), e2


def planifier(mots, env: list[float], duree: float, pause=0.35, respiration=0.15, reprises=True):
    """-> (garder [[début, fin]], decisions [{t0, t1, type, texte}]). Logique pure, testée par auto_test()."""
    dec, jete = [], {}
    for i, m in enumerate(mots):
        if jetons(m[0]) and all(x in HESITATIONS for x in jetons(m[0])):
            jete[i] = "hésitation"
    if reprises:
        mc = morceaux([i for i in range(len(mots)) if i not in jete], mots)
        for k in range(len(mc) - 1):
            a, b = mc[k], mc[k + 1]
            pourquoi = reprise([x for i in a for x in jetons(mots[i][0])], bool(FIN.search(mots[a[-1]][0].strip())),
                               [x for i in b for x in jetons(mots[i][0])])
            if pourquoi:
                for i in a:
                    jete[i] = f"reprise : {pourquoi}"
    for i, why in jete.items():
        dec.append({"t0": mots[i][1], "t1": mots[i][2], "type": why.split(" :")[0], "texte": mots[i][0].strip(),
                    "pourquoi": why})
    srt = sorted(env)
    fond = srt[len(srt) // 10] if srt else -90.0
    seuil_voix, seuil_bruit = fond + 10, max(fond + 25, -40.0)
    gardes = [i for i in range(len(mots)) if i not in jete]
    runs = []
    for i in gardes:  # une suite de mots gardés, sans pause longue ni mot jeté entre eux
        if runs and i == runs[-1][-1] + 1 and mots[i][1] - mots[runs[-1][-1]][2] <= pause:
            # bruit de bouche dans la petite pause entre deux mots ?
            a, b = mots[i - 1][2] + .04, mots[i][1] - .04
            fort = [x for x in env[int(a * 100):int(b * 100)] if x > seuil_bruit]
            if b - a >= .04 and fort and len(fort) / 100 < BRUIT_MAX:
                dec.append({"t0": round(a, 2), "t1": round(b, 2), "type": "bruit", "texte": "",
                            "pourquoi": "son court et fort sans mot : lèvres, toux ou raclement"})
                runs.append([i])
                continue
            runs[-1].append(i)
        else:
            runs.append([i])
    garder = []
    for r in runs:
        mini = garder[-1][1] if garder else 0.0
        s, e = caler(mots[r[0]][1], mots[r[-1]][2], env, seuil_voix, mini, duree)
        s, e = max(mini, s - respiration / 2), min(duree, e + respiration / 2)
        if garder and s <= garder[-1][1] + .02:
            garder[-1][1] = e
        else:
            garder.append([round(s, 3), round(e, 3)])
    prec = 0.0
    for a, b in garder + [[duree, duree]]:
        dedans = sum(d["t1"] - d["t0"] for d in dec if d["t0"] >= prec - .01 and d["t1"] <= a + .01)
        if a - prec - dedans >= 0.6:
            dec.append({"t0": round(prec, 2), "t1": round(a, 2), "type": "silence", "texte": "", "pourquoi": "silence"})
        prec = b
    return garder, sorted(dec, key=lambda d: d["t0"])


def caler_images(garder, fps: float):
    """Bords posés sur des images entières : pas de décalage entre l'image et le son au fil des coupes."""
    out = []
    for a, b in garder:
        a2, b2 = round(a * fps) / fps, round(b * fps) / fps
        if b2 - a2 >= 1 / fps:
            out.append([round(a2, 4), round(b2, 4)])
    return out


def nouveaux_temps(mots, garder):
    """Les mots gardés, aux temps de la vidéo coupée."""
    out, off = [], []
    t = 0.0
    for a, b in garder:
        off.append(t)
        t += b - a
    for m in mots:
        for (a, b), o in zip(garder, off):
            if a - .01 <= m[1] < b:
                out.append((m[0], round(o + max(0, m[1] - a), 3), round(o + min(b, m[2]) - a, 3)))
                break
    return out


def rendre(src, garder, sortie, apercu=False):
    n = len(garder)
    g = [f"[0:v]split={n}" + "".join(f"[v{i}]" for i in range(n)), f"[0:a]asplit={n}" + "".join(f"[a{i}]" for i in range(n))]
    for i, (a, b) in enumerate(garder):
        d = b - a
        g.append(f"[v{i}]trim=start={a}:end={b},setpts=PTS-STARTPTS[V{i}]")
        g.append(f"[a{i}]atrim=start={a}:end={b},asetpts=PTS-STARTPTS,afade=t=in:d=0.008,"
                 f"afade=t=out:st={max(0, d - .008):.4f}:d=0.008[A{i}]")
    g.append("".join(f"[V{i}][A{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=1[v0][a]")
    g.append("[v0]scale=-2:720[v]" if apercu else "[v0]null[v]")
    with tempfile.TemporaryDirectory() as tmp:
        script = Path(tmp) / "graphe.txt"
        script.write_text(";\n".join(g), encoding="utf-8")
        with C.verrou():
            C.run(["ffmpeg", "-y", "-v", "error", "-i", src, "-/filter_complex", script, "-map", "[v]", "-map", "[a]",
                   *C.encodeur(apercu), "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", sortie], basse=True)


def ecrire_md(dossier: Path, src, garder, dec, duree):
    def mmss(t):
        return f"{int(t // 60):02d}:{t % 60:04.1f}"
    gard = sum(b - a for a, b in garder)
    compte = {}
    for d in dec:
        compte[d["type"]] = compte.get(d["type"], 0) + 1
    l = [f"# Coupes de {Path(src).name}", "", f"Durée : {mmss(duree)} avant, {mmss(gard)} après.",
         "Coupes : " + ", ".join(f"{v} {k}" for k, v in sorted(compte.items())), "",
         "Relis surtout les reprises et les bruits. Pour annuler une coupe : ajoute le morceau dans `garder` de "
         "coupes.json, puis relance avec --depuis.", "", "| Temps (prise) | Coupe | Mot | Pourquoi |", "|---|---|---|---|"]
    l += [f"| {mmss(d['t0'])} à {mmss(d['t1'])} | {d['type']} | {d['texte']} | {d['pourquoi']} |"
          for d in dec if d["type"] != "silence"]
    (dossier / "coupes.md").write_text("\n".join(l) + "\n", encoding="utf-8")


def couper(src, transcription=None, dossier=None, pause=0.35, respiration=0.15, reprises=True, apercu=False, depuis=None):
    C.verifier_ffmpeg()
    src = Path(src)
    dossier = Path(dossier or src.with_name(src.stem + "-coupe"))
    dossier.mkdir(parents=True, exist_ok=True)
    i = C.infos(src)
    if not i["son"]:
        raise SystemExit("La prise n'a pas de son : rien à couper.")
    mots = C.lire_mots(transcription) if transcription else []
    if depuis:
        j = json.loads(Path(depuis).read_text(encoding="utf-8"))
        garder, dec = j["garder"], j.get("decisions", [])
    else:
        if not mots:
            raise SystemExit("Donne la transcription (transcrire.py) ou --depuis coupes.json.")
        garder, dec = planifier(mots, C.enveloppe(src), i["duree"], pause, respiration, reprises)
    garder = caler_images(garder, i["fps"] or 25)
    if not garder:
        raise SystemExit("Rien à garder : vérifie la transcription.")
    (dossier / "coupes.json").write_text(json.dumps({"source": src.name, "garder": garder, "decisions": dec},
                                                    ensure_ascii=False, indent=1), encoding="utf-8")
    ecrire_md(dossier, src, garder, dec, i["duree"])
    if mots:
        C.ecrire_mots(nouveaux_temps(mots, garder), dossier / "transcription-coupee.json")
    sortie = dossier / ("coupe-apercu.mp4" if apercu else "coupe.mp4")
    rendre(src, garder, sortie, apercu)
    print(f"{len(garder)} morceaux gardés, {sum(b - a for a, b in garder):.1f} s sur {i['duree']:.1f} s -> {sortie}")
    return sortie


def auto_test():
    mots = [(" Bonjour", .2, .8), (" à", .9, 1.0), (" tous.", 1.05, 1.5), (" Je", 1.75, 1.9), (" euh", 2.0, 2.3),
            (" vais", 2.4, 2.6), (" te", 4.0, 4.2), (" montrer", 4.25, 4.6), (" te", 5.2, 5.4), (" montrer", 5.45, 5.8),
            (" comment.", 5.85, 6.3)]
    assert reprise(["ça", "se", "peut", "qu", "elle", "revienne"], True, ["ça", "se", "peut", "que", "non"]) is None
    assert reprise(["ton", "insistance", "ne", "lui"], False, ["ton", "insistance", "ne", "lui", "rendra", "pas"])
    son = "+".join(f"0.5*sin(2*PI*300*t)*between(t,{s},{e})" for _, s, e in mots if _ != " euh")
    son += "+0.4*sin(2*PI*120*t)*between(t,2.0,2.3)+0.9*(2*random(0)-1)*between(t,1.6,1.65)"  # « euh » et un claquement
    with tempfile.TemporaryDirectory() as tmp:
        v = Path(tmp) / "prise.mp4"
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=6.8:size=320x240:rate=25",
               "-f", "lavfi", "-i", f"aevalsrc='{son}':s=48000:d=6.8", "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", "-c:a", "aac", v])
        env = C.enveloppe(v)
        garder, dec = planifier(mots, env, 6.8)
        types = {d["type"] for d in dec}
        assert {"hésitation", "reprise", "bruit", "silence"} <= types, dec
        assert any(d["type"] == "reprise" and d["t0"] == 4.0 for d in dec), dec
        assert all(b > a for a, b in garder) and all(x[1] <= y[0] for x, y in zip(garder, garder[1:])), garder
        tj = Path(tmp) / "t.json"
        C.ecrire_mots(mots, tj)
        sortie = couper(v, tj, Path(tmp) / "out")
        d_out = C.infos(sortie)["duree"]
        attendu = sum(b - a for a, b in caler_images(garder, 25))
        assert abs(d_out - attendu) < .15 and d_out < 5.0, (d_out, attendu)
        nt = C.lire_mots(Path(tmp) / "out" / "transcription-coupee.json")
        assert [m[0] for m in nt] == [" Bonjour", " à", " tous.", " Je", " vais", " te", " montrer", " comment."], nt
        assert all(m[2] <= d_out + .05 for m in nt) and "reprise" in (Path(tmp) / "out" / "coupes.md").read_text("utf-8")
        couper(v, tj, Path(tmp) / "out", depuis=Path(tmp) / "out" / "coupes.json", apercu=True)
        assert C.infos(Path(tmp) / "out" / "coupe-apercu.mp4")["h"] == 720
    print("AUTO-TEST OK")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Prise + transcription -> prise coupée (silences, hésitations, reprises, bruits).")
    p.add_argument("prise", nargs="?")
    p.add_argument("transcription", nargs="?")
    p.add_argument("-o", "--dossier")
    p.add_argument("--pause", type=float, default=0.35, help="pause plus longue = coupée (s)")
    p.add_argument("--respiration", type=float, default=0.15, help="pause gardée entre deux phrases (s)")
    p.add_argument("--sans-reprises", action="store_true")
    p.add_argument("--apercu", action="store_true")
    p.add_argument("--depuis")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        auto_test()
    elif a.prise:
        couper(a.prise, a.transcription, a.dossier, a.pause, a.respiration, not a.sans_reprises, a.apercu, a.depuis)
    else:
        p.print_help()
