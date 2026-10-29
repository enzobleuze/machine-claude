"""habiller.py : la vidéo coupée + un plan des moments (plan.json) -> la vidéo habillée aux couleurs de la charte.
Cartes de chapitre, citations, listes, textes à l'écran, zooms sur la phrase clé, plans de coupe (B-roll),
sous-titres, logo. ffmpeg seul (les textes passent par libass). Toutes les couleurs et polices viennent de la charte.

  python habiller.py verifier plan.json [--video coupe.mp4]        le tableau des moments + les alertes (sortie 1 si alerte)
  python habiller.py chapitres plan.json                            les chapitres YouTube (00:00 Titre), vrais temps du montage
  python habiller.py rendre coupe.mp4 plan.json [-o final.mp4] [--sous-titres transcription-coupee.json] [--srt]
                     [--apercu] [--charte bibliotheque/marque/charte-jetons.json]
  python habiller.py --test

plan.json :
  {"format": "16:9", "elements": [
    {"type": "chapitre", "debut": 0,    "duree": 2.5, "texte": "Le vrai problème", "etiquette": "Partie 1",
     "dit": "la phrase dite à ce moment", "prouve": "ce que l'élément montre ou prouve"},
    {"type": "texte",    "debut": 12.3, "duree": 2.0, "texte": "Un seul mot fort", "accent": "fort"},
    {"type": "citation", "debut": 40,   "duree": 3.5, "texte": "La phrase-principe, mot pour mot."},
    {"type": "liste",    "debut": 60,   "duree": 4.0, "titre": "Ce qui marche", "items": ["écouter", "attendre"]},
    {"type": "zoom",     "debut": 80,   "duree": 2.0, "force": 1.15},
    {"type": "plan",     "debut": 90,   "duree": 3.0, "fichier": "broll/rue-matin.mp4"}]}
Les temps sont ceux de la vidéo coupée. « dit » et « prouve » servent au tableau des moments : un élément sans raison
d'être à l'écran n'y va pas.
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

PLEIN = ("chapitre", "citation", "liste")      # cartes qui couvrent tout l'écran
MOTS_MAX, TENUE_MIN, ECART_ZOOM = 6, 1.5, 4.0  # 6 mots à l'écran, 1,5 s à l'écran au moins, 4 s entre deux zooms
VISAGE_PAR_MINUTE = 10.0                       # long format : au moins 10 s de visage seul par minute
TIRETS = (chr(0x2014), chr(0x2013))  # tiret long et tiret moyen


def lire_plan(f) -> dict:
    p = json.loads(Path(f).read_text(encoding="utf-8"))
    for e in p.get("elements", []):
        e["fin"] = round(float(e["debut"]) + float(e["duree"]), 3)
    p["elements"].sort(key=lambda e: e["debut"])
    return p


def texte_de(e) -> str:
    return " ".join([e.get("etiquette", ""), e.get("titre", ""), e.get("texte", ""), *e.get("items", [])]).strip()


# ------------------------------------------------------------------------------------------------ tableau des moments
def alertes(p: dict, duree: float | None = None) -> list[tuple[int, str]]:
    """[(n° d'élément, alerte)]. Règles chiffrées du système d'origine, à garder ou à régler dans wiki/maps/montage.md."""
    out, els = [], p["elements"]
    zooms = [e for e in els if e["type"] == "zoom"]
    for k, e in enumerate(els, 1):
        t = texte_de(e)
        if e["type"] == "texte" and len(t.split()) > MOTS_MAX:
            out.append((k, f"{len(t.split())} mots à l'écran (6 au plus)"))
        if e.get("accent") and (len(e["accent"].split()) > 1 or e["accent"].lower() not in t.lower()):
            out.append((k, "accent : un seul mot, pris dans le texte"))
        if e["type"] != "zoom" and e["duree"] < TENUE_MIN:
            out.append((k, f"à l'écran {e['duree']} s (1,5 s au moins pour être lu)"))
        if any(x in t for x in TIRETS):
            out.append((k, "tiret long ou moyen à l'écran"))
        if e["type"] == "plan" and not e.get("fichier"):
            out.append((k, "plan de coupe sans fichier"))
        if duree and e["fin"] > duree + .05:
            out.append((k, f"finit après la vidéo ({duree:.1f} s)"))
        for k2, e2 in enumerate(els[k:], k + 1):
            if e2["debut"] < e["fin"] - .01 and "zoom" not in (e["type"], e2["type"]):
                out.append((k, f"chevauche l'élément {k2}"))
    for a, b in zip(zooms, zooms[1:]):
        if b["debut"] - a["debut"] < ECART_ZOOM:
            out.append((els.index(b) + 1, f"zoom à moins de 4 s du précédent ({b['debut'] - a['debut']:.1f} s)"))
    if p.get("format", "16:9") == "16:9" and duree and duree >= 60:
        couvert = [(e["debut"], e["fin"]) for e in els if e["type"] in PLEIN + ("plan",)]
        for m in range(int(duree // 60)):
            a, b = m * 60, m * 60 + 60
            cache = sum(max(0, min(b, y) - max(a, x)) for x, y in couvert)
            if 60 - cache < VISAGE_PAR_MINUTE:
                out.append((0, f"minute {m + 1} : {60 - cache:.0f} s de visage seul (10 s au moins pour respirer)"))
    return out


def tableau(p: dict, duree: float | None, sortie: Path) -> list:
    al = alertes(p, duree)
    l = ["# Tableau des moments", "", "| # | Temps | Type | À l'écran | Phrase dite | Ce que ça prouve | Alerte |",
         "|---|---|---|---|---|---|---|"]
    for k, e in enumerate(p["elements"], 1):
        a = "; ".join(x for n, x in al if n == k)
        manque = "" if e["type"] == "zoom" or (e.get("dit") and e.get("prouve")) else " (dit ou prouve manquant)"
        l.append(f"| {k} | {e['debut']:.1f} à {e['fin']:.1f} | {e['type']} | {texte_de(e) or e.get('fichier', '')} | "
                 f"{e.get('dit', '')} | {e.get('prouve', '')} | {a}{manque} |")
    l += ["", *[f"- {x}" for n, x in al if n == 0]]
    instants = ",".join(f"{(e['debut'] + e['fin']) / 2:.1f}" for e in p["elements"])
    l += ["", "Planche avant de montrer : `python outils/planche.py <rendu-apercu.mp4> --at " + instants + " -o planche.jpg`"]
    sortie.write_text("\n".join(l) + "\n", encoding="utf-8")
    return al


# ------------------------------------------------------------------------------------------------ chapitres YouTube
def chapitres(p: dict) -> tuple[list[str], list[str]]:
    """Lignes « 00:00 Titre » depuis les cartes de chapitre, et les avertissements des règles YouTube."""
    ch = [(e["debut"], e.get("texte", "")) for e in p["elements"] if e["type"] == "chapitre"]
    av = []
    if not ch:
        return [], ["aucune carte de chapitre dans le plan"]
    if ch[0][0] > .5:
        av.append("premier chapitre forcé à 00:00 (règle YouTube)")
    ch = [(0.0, ch[0][1])] + ch[1:]
    if len(ch) < 3:
        av.append(f"{len(ch)} chapitre(s) : YouTube en demande 3 au moins")
    for (a, _), (b, t) in zip(ch, ch[1:]):
        if b - a < 10:
            av.append(f"« {t} » à moins de 10 s du précédent")

    def ts(s):
        s = int(s)
        return f"{s // 3600}:{s // 60 % 60:02d}:{s % 60:02d}" if s >= 3600 else f"{s // 60:02d}:{s % 60:02d}"
    return [f"{ts(t)} {x}" for t, x in ch], av


# ------------------------------------------------------------------------------------------------ rendu
def ecrire_ass(p, j, w, h, mots, sortie: Path) -> list[dict]:
    c, s = C.couleurs(j), h / 1080
    vertical = h > w
    pt, ptx = j["polices"]["titres"], j["polices"]["texte"]
    fad = "{\\fad(250,200)}"
    ressort = "{\\fscx92\\fscy92\\t(0,180,\\fscx103\\fscy103)\\t(180,300,\\fscx100\\fscy100)}"  # rebond de 3 % au plus
    st = [C.ass_style("Titre", pt, int(96 * s), c["texte"], align=5, marges=(int(.12 * w), int(.12 * w), 0)),
          C.ass_style("Etiquette", ptx, int(40 * s), c["accent"], align=5),
          C.ass_style("Citation", pt, int(62 * s), c["texte"], italique=True, align=5, marges=(int(.15 * w), int(.15 * w), 0)),
          C.ass_style("Item", ptx, int(52 * s), c["texte"], align=4, marges=(int(.25 * w), int(.1 * w), 0)),
          C.ass_style("Texte", ptx, int(58 * s), c["texte"], c["fond"], align=2, marges=(60, 60, int(.2 * h)), contour=int(22 * s),
                      boite=True),
          C.ass_style("ST", ptx, int((70 if vertical else 50) * s * (1080 / w if vertical else 1)), c["texte"], c["fond"], align=2,
                      marges=(int(.1 * w), int(.1 * w), int(.15 * h if vertical else .06 * h)), contour=int(14 * s), boite=True)]
    ev, l = [], []
    for e in p["elements"]:
        a, b, t = e["debut"], e["fin"], e["type"]
        if t in PLEIN:
            l.append(C.ass_ligne(a, b, "Titre", "{\\fad(200,200)}" + C.ass_rect(0, 0, w, h, c["surface_2" if t == "citation" else "fond"])))
        if t == "chapitre":
            if e.get("etiquette"):
                l.append(C.ass_ligne(a, b, "Etiquette", fad + f"{{\\pos({w // 2},{int(h * .38)})}}" + C.ass_texte(e["etiquette"]), 1))
            l.append(C.ass_ligne(a, b, "Titre", fad + ressort + C.ass_texte(e.get("texte", "")), 1))
            l.append(C.ass_ligne(a + .15, b, "Titre", fad + C.ass_rect(w // 2 - int(60 * s), int(h * .6), int(120 * s), int(8 * s),
                                                                     c["accent"]), 1))
        elif t == "citation":
            l.append(C.ass_ligne(a, b, "Citation", fad + "{\\1c" + C.ass_couleur(c["accent"]) + "}« {\\1c"
                                 + C.ass_couleur(c["texte"]) + "}" + C.ass_texte(e.get("texte", "")) + " {\\1c"
                                 + C.ass_couleur(c["accent"]) + "}»", 1))
        elif t == "liste":
            if e.get("titre"):
                l.append(C.ass_ligne(a, b, "Titre", fad + f"{{\\pos({w // 2},{int(h * .2)})}}" + C.ass_texte(e["titre"]), 1))
            items = e.get("items", [])
            pas = min(.7, max(.3, (e["duree"] - 1) / max(1, len(items))))
            y0 = h * .38
            for k, it in enumerate(items):
                l.append(C.ass_ligne(a + .3 + k * pas, b, "Item", fad + f"{{\\pos({int(.25 * w)},{int(y0 + k * 90 * s)})}}"
                                     + "{\\1c" + C.ass_couleur(c["accent"]) + "}■  {\\1c" + C.ass_couleur(c["texte"]) + "}"
                                     + C.ass_texte(it), 1))
        elif t == "texte":
            txt = C.ass_texte(e.get("texte", ""))
            if e.get("accent"):
                txt = re.sub(re.escape(e["accent"]), lambda m: "{\\1c" + C.ass_couleur(c["accent"]) + "}" + m.group(0)
                             + "{\\1c" + C.ass_couleur(c["texte"]) + "}", txt, count=1, flags=re.I)
            l.append(C.ass_ligne(a, b, "Texte", fad + ressort + txt, 2))
        ev.append({"type": t, "t0": a, "t1": b, "texte": texte_de(e) or e.get("fichier", "")})
    pleins = [(e["debut"], e["fin"]) for e in p["elements"] if e["type"] in PLEIN]
    for a, b, t in C.blocs(mots, 3 if vertical else 5, 15 if vertical else 32, capitales=vertical) if mots else []:
        for x, y in pleins:  # pas de sous-titre sur une carte plein écran : le bloc s'arrête avant ou reprend après
            if a < x < b:
                b = x
            elif x <= a < y:
                a = y
        if b - a >= .3:
            l.append(C.ass_ligne(a - 2 / 30, b, "ST", C.ass_texte(t), 3))
            ev.append({"type": "sous-titre", "t0": round(a, 2), "t1": round(b, 2), "texte": t})
    sortie.write_text(C.ass_entete(w, h, st) + "".join(l), encoding="utf-8")
    return ev


def ecrire_srt(mots, sortie: Path):
    def ts(t):
        ms = int(round(t * 1000))
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    b = C.blocs(mots, 7, 42)
    sortie.write_text("".join(f"{k}\n{ts(a)} --> {ts(e)}\n{t}\n\n" for k, (a, e, t) in enumerate(b, 1)), encoding="utf-8")


def rendre(video, plan, sortie=None, transcription=None, srt=False, apercu=False, charte=None):
    C.verifier_ffmpeg()
    video, p, j = Path(video), lire_plan(plan), C.charte(charte)
    if j.get("_secours"):
        print("charte absente : charte « simple » utilisée (brique charte-graphique pour la tienne)")
    i = C.infos(video)
    al = [x for x in alertes(p, i["duree"]) if "chevauche" in x[1] or "finit après" in x[1]]
    if al:
        raise SystemExit("Plan à corriger avant le rendu :\n- " + "\n- ".join(f"élément {n} : {x}" for n, x in al))
    w, h = (round(i["w"] * 720 / i["h"] / 2) * 2, 720) if apercu else (i["w"], i["h"])
    sortie = Path(sortie or video.with_name(video.stem + ("-habille-apercu.mp4" if apercu else "-habille.mp4")))
    mots = C.lire_mots(transcription) if transcription else []
    if srt and mots:
        ecrire_srt(mots, sortie.with_suffix(".srt"))
    pieces, t = [], 0.0  # (début, fin, zoom, fichier) sur toute la durée
    for e in [e for e in p["elements"] if e["type"] in ("zoom", "plan")] + [{"debut": i["duree"], "fin": i["duree"], "type": ""}]:
        if e["debut"] > t + .01:
            pieces.append((t, e["debut"], 1.0, None))
        if e["type"]:
            pieces.append((e["debut"], e["fin"], float(e.get("force", 1.15)), e.get("fichier") if e["type"] == "plan" else None))
        t = max(t, e["fin"])
    entrees = [video] + [Path(plan).parent / f for _, _, _, f in pieces if f]
    g, n_in = [f"[0:v]split={len(pieces)}" + "".join(f"[s{k}]" for k in range(len(pieces)))], 0
    for k, (a, b, z, f) in enumerate(pieces):
        if f:
            n_in += 1
            g.append(f"[{n_in}:v]trim=duration={b - a:.3f},setpts=PTS-STARTPTS,fps={i['fps'] or 25},"
                     f"scale={w}:{h}:force_original_aspect_ratio=increase,crop={w}:{h},tpad=stop_mode=clone:stop_duration={b - a:.3f},"
                     f"trim=duration={b - a:.3f},setsar=1[p{k}];[s{k}]nullsink")
        else:
            zc = f",crop=iw/{z}:ih/{z}:(iw-iw/{z})/2:(ih-ih/{z})*0.4" if z > 1.001 else ""  # zoom un peu au-dessus du centre : le visage
            g.append(f"[s{k}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS{zc},scale={w}:{h},setsar=1[p{k}]")
    g.append("".join(f"[p{k}]" for k in range(len(pieces))) + f"concat=n={len(pieces)}:v=1:a=0[base]")
    with tempfile.TemporaryDirectory() as tmp:
        ass = Path(tmp) / "habillage.ass"
        ev = ecrire_ass(p, j, w, h, mots, ass)
        g.append(f"[base]{C.filtre_ass(ass, j)}[hab]")
        lg = C.logo(j)
        pleins = [(e["debut"], e["fin"]) for e in p["elements"] if e["type"] in PLEIN]
        if lg and pleins:  # le logo signe les cartes plein écran, en haut à droite
            entrees.append(lg)
            quand = "+".join(f"between(t,{a},{b})" for a, b in pleins)
            g.append(f"[{len(entrees) - 1}:v]scale={int(w * .08)}:-1[lg];[hab][lg]overlay=W-w-{int(w * .03)}:{int(w * .03)}:"
                     f"enable='{quand}'[v]")
        else:
            g.append("[hab]null[v]")
        script = Path(tmp) / "graphe.txt"
        script.write_text(";\n".join(g), encoding="utf-8")
        cmd = ["ffmpeg", "-y", "-v", "verbose"]
        for f in entrees:
            cmd += (["-loop", "1", "-i", f] if Path(f).suffix.lower() in (".png", ".jpg", ".jpeg") else ["-i", f])
        with C.verrou():
            r = C.run(cmd + ["-/filter_complex", script, "-map", "[v]", "-map", "0:a?", *C.encodeur(apercu), "-c:a", "aac",
                             "-b:a", "192k", "-t", f"{i['duree']:.3f}", "-movflags", "+faststart", sortie], basse=True)
    manque = C.polices_remplacees(r.stderr)
    if manque:
        print(f"ATTENTION police remplacée : {', '.join(manque)}. Installe-la ou range le .ttf dans bibliotheque/marque/polices/.")
    sortie.with_suffix(".evenements.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"-> {sortie} ({w}x{h})")
    return sortie


def auto_test():
    p = {"format": "16:9", "elements": [
        {"type": "chapitre", "debut": 0, "duree": 2, "texte": "Le début", "etiquette": "Partie 1", "dit": "x", "prouve": "y"},
        {"type": "texte", "debut": 2.5, "duree": 1.6, "texte": "Un mot fort", "accent": "fort", "dit": "x", "prouve": "y"},
        {"type": "zoom", "debut": 4.2, "duree": 1.0, "force": 1.2},
        {"type": "citation", "debut": 5.4, "duree": 1.6, "texte": "Une phrase.", "dit": "x", "prouve": "y"},
        {"type": "plan", "debut": 7.2, "duree": 1.5, "fichier": "broll.mp4", "dit": "x", "prouve": "y"},
        {"type": "liste", "debut": 8.8, "duree": 1.6, "titre": "Liste", "items": ["un", "deux"], "dit": "x", "prouve": "y"}]}
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "plan.json"
        f.write_text(json.dumps(p), encoding="utf-8")
        pl = lire_plan(f)
        assert alertes(pl, 11) == [], alertes(pl, 11)
        mauvais = json.loads(json.dumps(p))
        mauvais["elements"][1].update(texte="Un texte bien trop long pour être lu " + chr(0x2014) + " vite", duree=1.0, accent="deux mots")
        mauvais["elements"][2]["debut"] = 0.5
        mauvais["elements"].append({"type": "zoom", "debut": 3.0, "duree": 1})
        f2 = Path(tmp) / "mauvais.json"
        f2.write_text(json.dumps(mauvais), encoding="utf-8")
        al = " ".join(x for _, x in alertes(lire_plan(f2), 5))
        for attendu in ("mots à l'écran", "accent", "1,5 s", "tiret", "moins de 4 s", "finit après"):
            assert attendu in al, (attendu, al)
        lignes, av = chapitres(pl)
        assert lignes == ["00:00 Le début"] and any("3 au moins" in x for x in av)
        assert any("visage seul" in x for _, x in alertes({"format": "16:9", "elements": [
            {"type": "citation", "debut": 0, "duree": 55, "fin": 55, "texte": "x"}]}, 120))
        v = C.test_video(Path(tmp) / "coupe.mp4", 11.0, "640x360")
        C.test_video(Path(tmp) / "broll.mp4", 1.0, "320x240", son=False)
        mots = [(f" mot{k}{'.' if k % 5 == 4 else ''}", k * .5, k * .5 + .4) for k in range(20)]
        C.ecrire_mots(mots, Path(tmp) / "t.json")
        out = rendre(v, f, Path(tmp) / "final.mp4", Path(tmp) / "t.json", srt=True)
        i = C.infos(out)
        assert (i["w"], i["h"], i["son"]) == (640, 360, True) and abs(i["duree"] - 11) < .2, i
        assert (Path(tmp) / "final.srt").read_text(encoding="utf-8").startswith("1\n00:00:00,000 --> ")
        ev = json.loads((Path(tmp) / "final.evenements.json").read_text(encoding="utf-8"))
        assert {"chapitre", "texte", "sous-titre", "plan"} <= {e["type"] for e in ev}
        assert not any(e["type"] == "sous-titre" and e["t0"] < x[1] and e["t1"] > x[0] for e in ev
                       for x in ((0, 2), (5.4, 7.0), (8.8, 10.4))), "sous-titre sur une carte plein écran"
        assert tableau(pl, 11, Path(tmp) / "tableau.md") == [] and "--at 1.0," in (Path(tmp) / "tableau.md").read_text("utf-8")
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Vidéo coupée + plan.json -> vidéo habillée (charte, ffmpeg seul).")
    ap.add_argument("action", nargs="?", choices=("verifier", "chapitres", "rendre"))
    ap.add_argument("args", nargs="*")
    ap.add_argument("-o", "--sortie")
    ap.add_argument("--video")
    ap.add_argument("--sous-titres")
    ap.add_argument("--srt", action="store_true")
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--charte")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.action == "verifier" and a.args:
        pl = lire_plan(a.args[0])
        d = C.infos(a.video)["duree"] if a.video else None
        res = tableau(pl, d, Path(a.args[0]).with_name("tableau-moments.md"))
        print("\n".join(f"élément {n} : {x}" if n else x for n, x in res) or "Aucune alerte.")
        print(f"-> {Path(a.args[0]).with_name('tableau-moments.md')}")
        sys.exit(1 if res else 0)
    elif a.action == "chapitres" and a.args:
        lignes, av = chapitres(lire_plan(a.args[0]))
        print("\n".join(lignes + [f"(avertissement) {x}" for x in av]))
    elif a.action == "rendre" and len(a.args) == 2:
        rendre(a.args[0], a.args[1], a.sortie, a.sous_titres, a.srt, a.apercu, a.charte)
    else:
        ap.print_help()
