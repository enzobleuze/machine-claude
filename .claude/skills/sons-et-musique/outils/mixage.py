"""mixage.py : la couche son d'un montage. Musique sous la voix, bruitages calés sur leur pic, niveau final mesuré.

  python mixage.py video.mp4 -o sortie.mp4 [--musique fichier.mp3|auto] [--sous-voix 18] [--intro 20]
                   [--sons sons.json] [--cible -14] [--plateforme youtube] [--catalogue ...] [--sans-variante]
  python mixage.py mesurer fichier.mp4            volume intégré (LUFS) et crête vraie
  python mixage.py --test

--musique auto : la musique du catalogue la mieux accordée aux mots de la charte, permise sur --plateforme,
                 jamais une des 5 dernières. Sans musique permise, le mixage se fait voix et bruitages seuls.
--sous-voix 18 : la musique reste 18 dB sous la voix (le système d'origine a rejeté 12 dB, trop fort).
--intro 20     : vidéo longue : la musique joue seulement dans les 20 premières secondes, puis fondu de 2,5 s.
--sons sons.json : [{"role": "whoosh", "t": 3.2}, {"role": "pop", "t": 5.0, "fichier": "chemin.wav", "gain_db": -2}]
                 t = l'instant de l'action visible ; le pic du son tombe dessus. Un son trop près du précédent du même
                 rôle est retiré (pop : 1,5 s ; whoosh : 0,35 s ; impact : 1,5 s...). Jamais deux fois le même fichier de suite.
--cible -14    : niveau final pour les réseaux. Si le premier mot sonne écrasé, essaie -16.
Écrit aussi <sortie>_sans_musique.mp4 (bouton de l'app de revue), <sortie>.son.json (ce qui a été placé ou retiré)
et <sortie>.evenements.json (frise de la revue).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path[:0] = [str(ICI), str(ICI.parents[1] / "montage-video-code" / "outils")]
import commun as C  # noqa: E402
import sonotheque as S  # noqa: E402

ECART_VOIX = {"impact": 14, "notification": 14, "whoosh": 16, "riser": 16, "frappe": 16, "pop": 16, "clic": 18, "tick": 18}
AF = "aformat=sample_rates=48000:channel_layouts=stereo"


def mesurer(f, avant: str = "") -> dict:
    r = C.run(["ffmpeg", "-hide_banner", "-nostats", "-i", f, "-vn", "-af", (avant + "," if avant else "") + "loudnorm=print_format=json",
               "-f", "null", "-"])
    j = json.loads(re.findall(r"\{[^{}]*\}", r.stderr)[-1])
    return {"lufs": float(j["input_i"]), "crete": float(j["input_tp"]), "lra": float(j["input_lra"]),
            "seuil": float(j["input_thresh"]), "decalage": float(j["target_offset"])}


def placer(sons: list[dict], cat: Path, voix_lufs: float, plateforme=None):
    """-> (placés [(fichier, début, gain_db, rôle, t)], retirés [texte]). Rotation des fichiers par rôle."""
    d = S.lire(cat)
    places, retires, dernier, compte = [], [], {}, {}
    for s in sorted(sons, key=lambda s: s["t"]):
        role = s.get("role", "clic")
        if role in dernier and s["t"] - dernier[role] < S.ECART_MIN.get(role, .08):
            retires.append(f"{role} à {s['t']:.2f} s : à moins de {S.ECART_MIN.get(role, .08)} s du précédent")
            continue
        if s.get("fichier"):
            f, m = Path(s["fichier"]), S.mesurer(s["fichier"])
        else:
            cands = [x for x in d["sons"] if x["type"] == "bruitage" and x["role"] == role and S.permis(x, plateforme)]
            if not cands:
                retires.append(f"{role} à {s['t']:.2f} s : aucun son de ce rôle permis dans le catalogue")
                continue
            x = cands[compte.get(role, 0) % len(cands)]
            f, m = cat.parent / x["fichier"], x
        compte[role] = compte.get(role, 0) + 1
        dernier[role] = s["t"]
        gain = (voix_lufs - ECART_VOIX.get(role, 18)) - m["niveau_db"] + float(s.get("gain_db", 0))
        places.append((f, max(0.0, s["t"] - m["pic"]), round(gain, 1), role, s["t"]))
    return places, retires


def un_mixage(video, sortie, duree, musique, gain_mus, intro, places, cible):
    entrees, g = [video], [f"[0:a]{AF}[voix]"]
    noms = ["[voix]"]
    if musique:
        entrees.append(musique)
        fin = min(duree, intro) if intro else duree
        g.append(f"[1:a]{AF},volume={gain_mus:.1f}dB,atrim=0:{fin:.3f},afade=t=in:d=1,"
                 f"afade=t=out:st={max(0, fin - 2.5):.3f}:d=2.5[mus]")
        noms.append("[mus]")
    for k, (f, debut, gain, _, _) in enumerate(places):
        entrees.append(f)
        ms = int(debut * 1000)
        g.append(f"[{len(entrees) - 1}:a]{AF},volume={gain:.1f}dB,adelay={ms}|{ms}[s{k}]")
        noms.append(f"[s{k}]")
    g.append("".join(noms) + f"amix=inputs={len(noms)}:normalize=0:duration=first:dropout_transition=0[mix]")
    with tempfile.TemporaryDirectory() as tmp:
        wav, script = Path(tmp) / "mix.wav", Path(tmp) / "graphe.txt"
        script.write_text(";\n".join(g), encoding="utf-8")
        cmd = ["ffmpeg", "-y", "-v", "error"]
        for k, f in enumerate(entrees):
            cmd += (["-stream_loop", "-1"] if musique and k == 1 else []) + ["-i", f]
        C.run(cmd + ["-/filter_complex", script, "-map", "[mix]", "-t", f"{duree:.3f}", wav], basse=True)
        m = mesurer(wav)
        ln = (f"loudnorm=I={cible}:TP=-1.5:LRA=11:measured_I={m['lufs']}:measured_TP={m['crete']}:measured_LRA={m['lra']}"
              f":measured_thresh={m['seuil']}:offset={m['decalage']}:linear=true")
        C.run(["ffmpeg", "-y", "-v", "error", "-i", video, "-i", wav, "-map", "0:v?", "-map", "1:a", "-c:v", "copy", "-af", ln,
               "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", sortie], basse=True)


def mixer(video, sortie=None, musique=None, sous_voix=18.0, intro=0.0, sons=None, cible=-14.0, plateforme=None,
          catalogue=None, variante=True) -> dict:
    C.verifier_ffmpeg()
    video = Path(video)
    sortie = Path(sortie or video.with_name(video.stem + "-son.mp4"))
    cat = S.chemin_catalogue(catalogue)
    i = C.infos(video)
    if not i["son"]:
        raise SystemExit("La vidéo n'a pas de voix à mixer.")
    voix = mesurer(video)
    info = {"voix_lufs": voix["lufs"], "musique": None, "retires": []}
    if musique == "auto":
        s = S.choisir(cat, "musique", humeur="auto", plateforme=plateforme, usage=sortie.stem)
        musique = cat.parent / s["fichier"] if s else None
        if not musique:
            info["retires"].append("aucune musique permise sur cette plateforme : voix et bruitages seuls")
    gain_mus = 0.0
    if musique:
        gain_mus = (voix["lufs"] - sous_voix) - mesurer(musique)["lufs"]
        info["musique"] = {"fichier": str(musique), "gain_db": round(gain_mus, 1), "sous_voix_db": sous_voix,
                           "jusqu_a": intro or round(i["duree"], 2)}
    liste = json.loads(Path(sons).read_text(encoding="utf-8")) if sons else []
    places, retires = placer(liste, cat, voix["lufs"], plateforme)
    info["retires"] += retires
    info["places"] = [{"role": r, "t": t, "fichier": Path(f).name, "gain_db": g} for f, _, g, r, t in places]
    with C.verrou():
        un_mixage(video, sortie, i["duree"], musique, gain_mus, intro, places, cible)
        if musique and variante:
            un_mixage(video, sortie.with_name(sortie.stem + "_sans_musique" + sortie.suffix), i["duree"], None, 0, 0, places, cible)
    fin = mesurer(sortie)
    info["final"] = {"lufs": fin["lufs"], "crete": fin["crete"]}
    sortie.with_suffix(".son.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    evf = video.with_suffix(".evenements.json")
    ev = json.loads(evf.read_text(encoding="utf-8")) if evf.exists() else []
    ev += [{"type": "son", "t0": t, "t1": t + .3, "texte": f"{r} {Path(f).name} ({g} dB)"} for f, _, g, r, t in places]
    if musique:
        ev.append({"type": "musique", "t0": 0, "t1": intro or i["duree"], "texte": f"{Path(musique).name}, {sous_voix} dB sous la voix"})
    sortie.with_suffix(".evenements.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {sortie} : {fin['lufs']:.1f} LUFS, crête {fin['crete']:.1f} dBTP, {len(places)} bruitages"
          + (f", {len(info['retires'])} retirés" if info["retires"] else ""))
    for r in info["retires"]:
        print("   retiré :", r)
    return info


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=6:size=320x240:rate=25", "-f", "lavfi", "-i",
               "aevalsrc='0.4*sin(2*PI*220*t)*mod(floor(t*3),2)':s=48000:d=6", "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", "-c:a", "aac", t / "v.mp4"])
        (t / "v.evenements.json").write_text('[{"type":"texte","t0":1,"t1":2,"texte":"x"}]', encoding="utf-8")
        cat = t / S.REL
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "sine=frequency=440:duration=2.5", t / "musique.wav"])
        S.ajouter(cat, t / "musique.wav", "musique", "musique", "CC0", "https://exemple.org", humeurs="sobre")
        for nom in ("pop-a", "pop-b", "whoosh-a"):
            C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "aevalsrc='0.8*sin(2*PI*900*t)*exp(-25*abs(t-0.1))':d=0.3",
                   t / f"{nom}.wav"])
            S.ajouter(cat, t / f"{nom}.wav", "bruitage", nom.split("-")[0], "CC0", "https://exemple.org")
        (t / "sons.json").write_text(json.dumps([{"role": "pop", "t": 1.0}, {"role": "pop", "t": 1.8}, {"role": "pop", "t": 3.0},
                                                 {"role": "whoosh", "t": 4.0}, {"role": "riser", "t": 5.0}]), encoding="utf-8")
        info = mixer(t / "v.mp4", t / "final.mp4", "auto", sons=t / "sons.json", catalogue=cat, plateforme="youtube")
        assert abs(info["final"]["lufs"] + 14) <= 1.0 and info["final"]["crete"] <= -1.0, info["final"]
        assert [p["role"] for p in info["places"]] == ["pop", "pop", "whoosh"], info["places"]
        pops = [p["fichier"] for p in info["places"] if p["role"] == "pop"]
        assert pops[0] != pops[1], "deux fois le même pop de suite"
        assert any("1.80" in r for r in info["retires"]) and any("riser" in r for r in info["retires"]), info["retires"]
        assert abs(info["musique"]["gain_db"] - ((info["voix_lufs"] - 18) - mesurer(t / "musique.wav")["lufs"])) < .2
        assert (t / "final_sans_musique.mp4").exists() and C.infos(t / "final.mp4")["w"] == 320
        ev = json.loads((t / "final.evenements.json").read_text(encoding="utf-8"))
        assert {"texte", "son", "musique"} <= {e["type"] for e in ev}
        info2 = mixer(t / "v.mp4", t / "intro.mp4", t / "musique.wav", intro=3.0, cible=-16, variante=False, catalogue=cat)
        assert abs(info2["final"]["lufs"] + 16) <= 1.0 and not (t / "intro_sans_musique.mp4").exists()
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Musique sous la voix, bruitages sur leur pic, niveau final mesuré.")
    ap.add_argument("video", nargs="?")
    ap.add_argument("fichier", nargs="?")
    ap.add_argument("-o", "--sortie")
    ap.add_argument("--musique")
    ap.add_argument("--sous-voix", type=float, default=18.0)
    ap.add_argument("--intro", type=float, default=0.0)
    ap.add_argument("--sons")
    ap.add_argument("--cible", type=float, default=-14.0)
    ap.add_argument("--plateforme")
    ap.add_argument("--catalogue")
    ap.add_argument("--sans-variante", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.video == "mesurer" and a.fichier:
        m = mesurer(a.fichier)
        print(f"{m['lufs']:.1f} LUFS intégrés, crête vraie {m['crete']:.1f} dBTP")
    elif a.video:
        mixer(a.video, a.sortie, a.musique, a.sous_voix, a.intro, a.sons, a.cible, a.plateforme, a.catalogue, not a.sans_variante)
    else:
        ap.print_help()
