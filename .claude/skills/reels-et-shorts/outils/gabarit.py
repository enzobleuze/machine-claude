"""gabarit.py : une prise face caméra (déjà coupée) -> un Reel vertical 1080x1920 monté à un gabarit, aux couleurs
de la charte. ffmpeg seul : plans, écran partagé, cartes animées (libass), sous-titres, appel final, son, niveau.

  python gabarit.py prise-coupee.mp4 transcription-coupee.json [--gabarit rythme|editorial|simple] [--visuels visuels.json]
                    [--centre 0.5] [--mot-cle MOT] [--titre "accroche"] [--musique auto|aucune|fichier] [-o dossier]
                    [--miroir] [--apercu] [--charte chemin]
  python gabarit.py --test

Les trois gabarits :
  rythme     un plan toutes les 1,2 s environ, coupé sur un début de mot. Entre deux visuels : visage et visage
             resserré en alternance, zoom marqué sur la phrase clé. Pendant un visuel : écran partagé (carte animée
             ou plan filmé en haut, la personne en bas), puis la carte en plein écran, 2 s au plus.
  editorial  même cadence ; en haut, un panneau clair avec le titre de section et la carte, la personne en bas.
  simple     face caméra seul, cadrage fixe, accroche en titre 3 s, sous-titres. Le plus sobre.
visuels.json (écrit par Claude après lecture de la transcription) :
  {"visuels": [{"de": 4.2, "a": 9.0, "type": "liste", "fort": "Ce qui marche", "titre": "", "items": ["écouter", "attendre"]},
               {"de": 12, "a": 17, "type": "texto", "fort": "Le message", "messages": [["elle", "On peut parler ?"], ["toi", "Oui."]]},
               {"de": 20, "a": 24, "type": "mot", "fort": "La clé", "mot": "PATIENCE", "etiquette": "ce qui change tout"},
               {"de": 27, "a": 30, "type": "clip", "fort": "Le matin", "fichier": "bibliotheque/broll/pexels-123.mp4"}],
   "punch": [14.8], "appel": 41.0}
  Les temps sont ceux de la prise coupée. « appel » = début de l'appel final (« écris MOT en commentaire ») ;
  sans lui et avec --mot-cle, l'appel prend les 3 dernières secondes.
--centre : où est le visage dans une prise paysage (0 = bord gauche, 1 = bord droit). Claude le lit sur une planche.
Sortie dans le dossier : reel.mp4, reel_sans_musique.mp4, plan.json (plans, mesures), sons.json, montage.md,
reel.evenements.json (frise de l'app de revue), reel-rythme.json (contrôle de rythme, avertissement).
"""
from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
sys.path[:0] = [str(ICI)] + [str(ICI.parents[1] / s / "outils") for s in ("montage-video-code", "sons-et-musique")]
import commun as C  # noqa: E402
import mixage as M  # noqa: E402
import rythme as R  # noqa: E402

W, H, FPS = 1080, 1920, 30
SEAM, SEAM_ED = 880, 1010           # écran partagé : panneau de 0 à 880 ; éditorial : panneau de 0 à 1010
PLAN_CIBLE, PLAN_MAX = 1.15, 2.8    # durée visée d'un plan, et au plus
PREMIERE = (.6, 1.0)                # la première coupe tombe entre 0,6 et 1,0 s, sur un début de mot
SANS_VISAGE = 2.0                   # un plein écran dure au plus 2 s, puis la personne revient (jamais absente plus de 3,5 s)
ZOOM = {"visage": 1.0, "serre": 1.12, "punch": 1.22}
ZOOM_ED = {"visage": 1.0, "serre": 1.0, "punch": 1.08}  # éditorial et simple : cadrage fixe, zoom doux sur la phrase clé
Y_ST = {"visage": 1380, "serre": 1380, "punch": 1380, "split": SEAM, "editorial": SEAM_ED, "plein": 1560}
SOUS_VOIX = 18                      # musique 18 dB sous la voix


# ------------------------------------------------------------------------------------------------ plan (logique pure)
def decoupe(a, b, bornes, cible=PLAN_CIBLE, maxi=PLAN_MAX):
    """Coupe [a, b] en plans d'environ cible secondes, sur des débuts de mots, aucun plus long que maxi."""
    pts, t = [a], a
    while b - t > maxi or (b - t >= 1.6 * cible and b - t > 1.6):
        cand = [x for x in bornes if t + .8 <= x <= min(t + maxi, b - .6)]
        if not cand:
            break
        t = min(cand, key=lambda x: abs(x - t - cible))
        pts.append(t)
    return list(zip(pts, pts[1:] + [b]))


def construire(bornes, longueur, fin, gabarit, visuels, punch):
    """Plans [(début, fin, disposition, n° du visuel ou None)] sur tout le Reel. Déterministe."""
    if gabarit == "simple":
        plans, t = [], 0.0
        for p in sorted(punch) + [fin]:
            x = min(bornes + [fin], key=lambda b: abs(b - p))
            if x > t + .5:
                plans.append((t, x, "visage", None))
                t = x
            if x < fin:
                y = next((b for b in bornes if b >= x + 1.2), fin)
                plans.append((x, y, "punch", None))
                t = y
        plans = [p for p in plans if p[1] - p[0] > 1e-3]
        if fin < longueur:
            plans.append((fin, longueur, "appel", None))
        return [(round(a, 3), round(b, 3), d, i) for a, b, d, i in plans]
    debut1 = next((x for x in bornes if PREMIERE[0] <= x <= PREMIERE[1]), next((x for x in bornes if x >= PREMIERE[0]), fin))
    spans = []
    for i, v in enumerate(visuels):
        a = min(bornes, key=lambda x: abs(x - v["de"]))
        b = min(bornes + [fin], key=lambda x: abs(x - v["a"]))
        if a >= debut1 and b - a >= .8 and (not spans or a >= spans[-1][1]):
            spans.append((a, min(b, fin), i))
    plans, t, tour = [(0.0, debut1, "visage", None)], debut1, 0
    pts = {round(min(bornes, key=lambda b: abs(b - p)), 3) for p in punch}
    for a, b, i in spans + [(fin, fin, None)]:
        for x, y in (decoupe(t, a, bornes) if a - t > .05 else []):
            d = "punch" if round(x, 3) in pts else ("serre" if tour % 2 else "visage")
            tour += 1
            if plans and plans[-1][2] == d and d != "punch":
                d = "serre" if d == "visage" else "visage"
            plans.append((x, y, d, None))
        if i is not None:
            for k, (x, y) in enumerate(decoupe(a, b, bornes, cible=1.0)):
                d = "editorial" if gabarit == "editorial" else ("plein" if k % 2 == 1 and y - x <= SANS_VISAGE else "split")
                plans.append((x, y, d, i))
        t = max(t, b)
    if fin < longueur:
        plans.append((fin, longueur, "appel", None))
    plans = [p for p in plans if p[1] - p[0] > 1e-3]
    return [(round(a, 3), round(b, 3), d, i) for a, b, d, i in plans]


def mesures(plans, fin):
    ps = [p for p in plans if p[2] != "appel" and p[0] < fin]
    tot = max(1e-6, sum(b - a for a, b, _, _ in ps))
    part, absent, cur = {}, 0.0, 0.0
    for a, b, d, _ in ps:
        part[d] = part.get(d, 0) + (b - a) / tot
        cur = cur + (b - a) if d == "plein" else 0.0
        absent = max(absent, cur)
    return {"plans": len(ps), "moyenne_s": round(tot / max(1, len(ps)), 2),
            "plus_long_s": round(max((b - a for a, b, _, _ in ps), default=0), 2),
            "parts": {k: round(v, 2) for k, v in sorted(part.items())}, "absent_max_s": round(absent, 2)}


def couche(d):
    return SEAM if d == "split" else SEAM_ED if d == "editorial" else H if d == "plein" else 0


def sons(plans, visuels, fin, appel):
    """Bruitages sur les actions visibles seulement : changement de mise en page, éléments qui arrivent, appel final.
    Rien sur une coupe d'un zoom à l'autre. Les fichiers sont choisis et tournés par mixage.py."""
    out = []
    for p, q in zip(plans, plans[1:]):
        if couche(p[2]) != couche(q[2]) and q[2] != "appel" and q[0] < fin:
            out.append({"role": "whoosh", "t": q[0]})
    for iv, v in enumerate(visuels):
        ps = [p for p in plans if p[3] == iv]
        if not ps or v["type"] == "clip":
            continue
        a, pas_ = ps[0][0], pas(v, ps[-1][1] - ps[0][0])
        if v["type"] == "texto":
            out += [{"role": "notification" if de == "elle" else "clic", "t": a + .45 + j * pas_} for j, (de, _) in enumerate(v["messages"][:3])]
        elif v["type"] == "liste":
            out += [{"role": "tick", "t": a + .45 + j * pas_} for j in range(len(v["items"][:4]))]
        elif v["type"] == "mot":
            out.append({"role": "impact", "t": a + .45})
    if appel is not None:
        out.append({"role": "pop", "t": appel + .3})
    return sorted(out, key=lambda s: s["t"])


def pas(v, duree):
    n = len(v.get("messages", v.get("items", [1])))
    return max(.35, min(.9, (duree - 1.6) / max(1, n)))


# ------------------------------------------------------------------------------------------------ rendu
def cadrage(w0, h0, cx, z, aspect, haut=.3):
    """Fenêtre (largeur, hauteur, x, y) d'aspect donné (largeur/hauteur), zoom z, centrée sur cx (0 à 1)."""
    ch = h0 if w0 / h0 >= aspect else w0 / aspect
    cw = ch * aspect
    cw, ch = int(cw / z) // 2 * 2, int(ch / z) // 2 * 2
    x = int(min(max(cx * w0 - cw / 2, 0), w0 - cw))
    return cw, ch, x, int((h0 - ch) * haut)


def segment(k, a, b, d, v, w0, h0, cx, gabarit, coul, clip_in):
    """Filtre d'un plan : [s{k}] -> [p{k}] en 1080x1920."""
    dur = b - a
    base = f"[s{k}]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS"
    fin = f"fps={FPS},format=yuv420p,setsar=1[p{k}]"
    zooms = ZOOM if gabarit == "rythme" else ZOOM_ED
    if d in zooms or d == "appel":
        cw, ch, x, y = cadrage(w0, h0, cx, zooms.get(d, 1.0), W / H)
        sombre = ",eq=brightness=-0.12" if d == "appel" else ""
        return [f"{base},crop={cw}:{ch}:{x}:{y},scale={W}:{H}{sombre},{fin}"]
    seam = couche(d)
    panneau = coul["panneau_ed"] if d == "editorial" else coul["panneau"]
    g = [f"color=c=0x{panneau.lstrip('#')}:s={W}x{H}:r={FPS}:d={dur:.3f}[bg{k}]"]
    cur = f"bg{k}"
    if seam < H:
        cw, ch, x, y = cadrage(w0, h0, cx, 1.0, W / (H - seam), .25)
        g.append(f"{base},crop={cw}:{ch}:{x}:{y},scale={W}:{H - seam},setsar=1[pp{k}]")
        g.append(f"[{cur}][pp{k}]overlay=0:{seam}:shortest=1[q{k}]")
        cur = f"q{k}"
    else:
        g.append(f"{base},nullsink")
    if clip_in is not None and gabarit == "rythme":
        hh = H if seam >= H else seam
        g.append(f"[{clip_in}:v]trim=duration={dur:.3f},setpts=PTS-STARTPTS,scale={W}:{hh}:force_original_aspect_ratio=increase,"
                 f"crop={W}:{hh},fps={FPS},tpad=stop_mode=clone:stop_duration={dur:.3f},trim=duration={dur:.3f}[c{k}]")
        g.append(f"[{cur}][c{k}]overlay=0:0:shortest=1[r{k}]")
        cur = f"r{k}"
    g.append(f"[{cur}]{fin}")
    return g


def ecrire_ass(plans, visuels, blocs_st, j, coul, gabarit, mot_cle, titre, appel, sortie):
    c = coul["c"]
    pt, ptx = j["polices"]["titres"], j["polices"]["texte"]
    fad, res = "{\\fad(120,100)}", "{\\fscx88\\fscy88\\t(0,160,\\fscx104\\fscy104)\\t(160,280,\\fscx100\\fscy100)}"
    st = [C.ass_style("ST", ptx, 64, c["texte"], c["surface"], align=5, marges=(150, 150, 0), contour=16, boite=True),
          C.ass_style("Bulle", ptx, 46, c["texte"], c["surface_2"], align=5, marges=(90, 90, 0), contour=20, boite=True),
          C.ass_style("Envoi", ptx, 46, c["accent_texte"], c["accent"], align=5, marges=(90, 90, 0), contour=20, boite=True),
          C.ass_style("Fort", pt, 64, coul["texte_panneau"], align=5, marges=(80, 80, 0)),
          C.ass_style("Item", ptx, 56, coul["texte_panneau"], align=4, marges=(160, 80, 0)),
          C.ass_style("Mot", pt, 150, c["accent"], align=5, marges=(60, 60, 0)),
          C.ass_style("Etiq", ptx, 42, coul["doux_panneau"], align=5, marges=(80, 80, 0)),
          C.ass_style("Titre", pt, 76, c["texte"], c["surface"], align=5, marges=(110, 110, 0), contour=24, boite=True)]
    ev, l = [], []
    for iv, v in enumerate(visuels):
        ps = [p for p in plans if p[3] == iv]
        if not ps:
            continue
        a, b = ps[0][0], ps[-1][1]
        ev.append({"type": v["type"], "t0": a, "t1": b, "texte": v.get("fort", "")})
        if gabarit == "editorial" and v.get("fort"):
            l.append(C.ass_ligne(a, b, "Fort", fad + "{\\pos(540,150)}" + C.ass_texte(v["fort"]), 1))
        if v["type"] == "clip":
            continue
        for p in ps:  # la carte se redessine dans chaque plan, centrée dans la zone visible du panneau
            cy = {"split": SEAM // 2, "editorial": 580, "plein": H // 2}[p[2]]
            pas_ = pas(v, b - a)
            if v["type"] == "texto":
                for k, (de, txt) in enumerate(v["messages"][:3]):
                    t0 = a + .45 + k * pas_
                    if t0 < p[1]:
                        x, al = (90, 4) if de == "elle" else (990, 6)
                        y = cy - 150 + k * 150
                        l.append(C.ass_ligne(max(t0, p[0]), p[1], "Bulle" if de == "elle" else "Envoi",
                                             f"{{\\an{al}\\pos({x},{y})}}" + (res if t0 >= p[0] else "") + C.ass_texte(txt), 2))
            elif v["type"] == "liste":
                if v.get("titre"):
                    l.append(C.ass_ligne(p[0], p[1], "Fort", f"{{\\pos(540,{cy - 230})}}" + C.ass_texte(v["titre"]), 2))
                for k, it in enumerate(v["items"][:4]):
                    t0 = a + .45 + k * pas_
                    if t0 < p[1]:
                        l.append(C.ass_ligne(max(t0, p[0]), p[1], "Item", f"{{\\pos(160,{cy - 110 + k * 100})}}"
                                             + (fad if t0 >= p[0] else "") + "{\\1c" + C.ass_couleur(c["accent"]) + "}■  {\\1c"
                                             + C.ass_couleur(coul["texte_panneau"]) + "}" + C.ass_texte(it), 2))
            elif v["type"] == "mot":
                if v.get("etiquette"):
                    l.append(C.ass_ligne(p[0], p[1], "Etiq", f"{{\\pos(540,{cy - 130})}}" + C.ass_texte(v["etiquette"]), 2))
                l.append(C.ass_ligne(max(a + .45, p[0]), p[1], "Mot", f"{{\\pos(540,{cy + 20})}}" + (res if a + .45 >= p[0] else "")
                                     + C.ass_texte(v["mot"]), 2))
    for k, (a, b, t) in enumerate(blocs_st):
        b = min(b + .3, blocs_st[k + 1][0] if k + 1 < len(blocs_st) else 1e9, appel or 1e9)  # jamais deux sous-titres à la fois
        for p in plans:  # place fixe par famille de plan : le sous-titre suit la mise en page s'il la traverse
            x, y = max(a, p[0]), min(b, p[1])
            if y - x > 1e-3 and p[2] != "appel":
                l.append(C.ass_ligne(x - (2 / FPS if x == a else 0), y, "ST", ("{\\fad(80,0)}" if x == a else "")
                                     + f"{{\\pos(540,{Y_ST.get(p[2], 1380)})}}" + C.ass_texte(t), 3))
        ev.append({"type": "sous-titre", "t0": round(a, 2), "t1": round(b, 2), "texte": t})
    if titre:
        l.append(C.ass_ligne(0, 3.0, "Titre", "{\\pos(540,330)}" + C.ass_texte(titre), 4))
        ev.append({"type": "titre", "t0": 0, "t1": 3.0, "texte": titre})
    if appel is not None and mot_cle:
        fin = plans[-1][1]
        l.append(C.ass_ligne(appel, fin, "Titre", res + "{\\pos(540,900)}Écris {\\1c" + C.ass_couleur(c["accent"]) + "}"
                             + C.ass_texte(mot_cle.upper()) + "{\\1c" + C.ass_couleur(c["texte"]) + "}\\Nen commentaire", 4))
        ev.append({"type": "appel", "t0": appel, "t1": fin, "texte": f"Écris {mot_cle.upper()} en commentaire"})
    sortie.write_text(C.ass_entete(W, H, st) + "".join(l), encoding="utf-8")
    return ev


def monter(prise, transcription, gabarit="rythme", visuels_json=None, centre=.5, mot_cle=None, titre=None, musique="auto",
           dossier=None, miroir=False, apercu=False, charte=None):
    C.verifier_ffmpeg()
    prise = Path(prise)
    dossier = Path(dossier or prise.with_name(prise.stem + f"-{gabarit}"))
    dossier.mkdir(parents=True, exist_ok=True)
    j = C.charte(charte)
    i = C.infos(prise)
    w0, h0, longueur = i["w"], i["h"], i["duree"]
    cfg = json.loads(Path(visuels_json).read_text(encoding="utf-8")) if visuels_json else {}
    visuels = [] if gabarit == "simple" else cfg.get("visuels", [])
    appel = cfg.get("appel", longueur - 3.0 if mot_cle else None)
    fin = appel if appel is not None else longueur
    mots = C.lire_mots(transcription)
    st = C.blocs(mots, 3, 15, fin=fin, capitales=gabarit != "simple")
    bornes = sorted({round(b[0], 3) for b in st}) or [0.0]
    plans = construire(bornes, longueur, fin, gabarit, visuels, cfg.get("punch", []))
    clair, princ = j["clair"], C.couleurs(j)
    coul = {"c": princ, "panneau": princ["fond"], "panneau_ed": clair["surface"],
            "texte_panneau": clair["texte"] if gabarit == "editorial" else princ["texte"],
            "doux_panneau": clair["texte_doux"] if gabarit == "editorial" else princ["texte_doux"]}
    cx = 1 - centre if miroir else centre
    entrees = [prise]
    g = [f"[0:v]{'hflip,' if miroir else ''}split={len(plans)}" + "".join(f"[s{k}]" for k in range(len(plans)))]
    for k, (a, b, d, iv) in enumerate(plans):
        clip_in = None
        if iv is not None and visuels[iv]["type"] == "clip" and visuels[iv].get("fichier"):
            entrees.append(Path(visuels_json).parent / visuels[iv]["fichier"])
            clip_in = len(entrees) - 1
        g += segment(k, a, b, d, visuels[iv] if iv is not None else None, w0, h0, cx, gabarit, coul, clip_in)
    g.append("".join(f"[p{k}]" for k in range(len(plans))) + f"concat=n={len(plans)}:v=1:a=0[base]")
    monte = dossier / "monte.mp4"
    with tempfile.TemporaryDirectory() as tmp:
        ass = Path(tmp) / "reel.ass"
        ev = ecrire_ass(plans, visuels, st, j, coul, gabarit, mot_cle, titre, appel, ass)
        g.append(f"[base]{C.filtre_ass(ass, j)}{',scale=540:960' if apercu else ''}[hab]")
        lg = C.logo(j)
        if lg and appel is not None:
            entrees.append(lg)
            g.append(f"[{len(entrees) - 1}:v]scale={70 if apercu else 140}:-1[lg];[hab][lg]overlay=(W-w)/2:{165 if apercu else 330}:"
                     f"enable='gte(t,{appel})'[v]")
        else:
            g.append("[hab]null[v]")
        script = Path(tmp) / "graphe.txt"
        script.write_text(";\n".join(g), encoding="utf-8")
        cmd = ["ffmpeg", "-y", "-v", "verbose"]
        for f in entrees:
            cmd += (["-loop", "1", "-i", f] if Path(f).suffix.lower() in (".png", ".jpg", ".jpeg") else ["-i", f])
        with C.verrou():
            r = C.run(cmd + ["-/filter_complex", script, "-map", "[v]", "-map", "0:a", *C.encodeur(apercu), "-c:a", "aac",
                             "-b:a", "192k", "-t", f"{longueur:.3f}", monte], basse=True)
    manque = C.polices_remplacees(r.stderr)
    monte.with_suffix(".evenements.json").write_text(json.dumps(ev, ensure_ascii=False, indent=1), encoding="utf-8")
    sj = dossier / "sons.json"
    sj.write_text(json.dumps(sons(plans, visuels, fin, appel if mot_cle else None), ensure_ascii=False, indent=1), encoding="utf-8")
    reel = dossier / ("reel-apercu.mp4" if apercu else "reel.mp4")
    info = M.mixer(monte, reel, None if musique == "aucune" else musique, SOUS_VOIX, sons=sj, plateforme="instagram")
    monte.unlink(missing_ok=True)
    monte.with_suffix(".evenements.json").unlink(missing_ok=True)
    m = mesures(plans, fin)
    info["retires"] += [f"visuels {k} et {k + 1} du même type ({a['type']}) : alterne les types" for k, (a, b) in
                        enumerate(zip(visuels, visuels[1:]), 1) if a["type"] == b["type"]]
    (dossier / "plan.json").write_text(json.dumps({"gabarit": gabarit, "plans": plans, "visuels": visuels, "mesures": m,
                                                   "appel": appel}, ensure_ascii=False, indent=1), encoding="utf-8")
    R.avertir(reel, "reel")
    (dossier / "montage.md").write_text(
        f"# Reel au gabarit {gabarit} : {prise.name}\n\n- Reel : `{reel.name}` ({longueur:.1f} s)\n- Mesures : {m}\n"
        f"- Son : {info['final']['lufs']:.1f} LUFS, {len(info['places'])} bruitages, musique : "
        f"{Path(info['musique']['fichier']).name if info['musique'] else 'aucune'}\n"
        + (f"- ATTENTION police remplacée : {', '.join(manque)}\n" if manque else "")
        + "".join(f"- alerte : {x}\n" for x in info["retires"])
        + "\n## Plans\n" + "".join(f"- {a:.1f} à {b:.1f} s : {d}" + (f" ({visuels[iv]['type']})" if iv is not None else "") + "\n"
                                   for a, b, d, iv in plans), encoding="utf-8")
    if manque:
        print(f"ATTENTION police remplacée : {', '.join(manque)}. Installe-la ou range le .ttf dans bibliotheque/marque/polices/.")
    print(f"-> {reel} {m}")
    return reel


# ------------------------------------------------------------------------------------------------ test
def auto_test():
    bornes = [k * .25 for k in range(160)]
    vis = [{"type": "liste", "items": ["a", "b"], "fort": "X", "de": 10, "a": 14}, {"type": "mot", "mot": "Y", "fort": "Y", "de": 30, "a": 35}]
    for g in ("rythme", "editorial", "simple"):
        plans = construire(bornes, 40.0, 38.0, g, vis, [20])
        assert plans[0][0] == 0 and abs(plans[-1][1] - 40.0) < 1e-6, "le plan couvre tout le Reel"
        assert all(abs(x[1] - y[0]) < 1e-6 for x, y in zip(plans, plans[1:])), "plans contigus"
        assert plans[-1][2] == "appel"
        m = mesures(plans, 38.0)
        if g != "simple":
            assert PREMIERE[0] <= plans[0][1] <= PREMIERE[1], "première coupe entre 0,6 et 1,0 s"
            assert m["plus_long_s"] <= PLAN_MAX + 1e-6 and m["absent_max_s"] <= 3.5 and 1.0 <= m["moyenne_s"] <= 1.6, m
            assert {d for _, _, d, i in plans if i is not None} <= ({"editorial"} if g == "editorial" else {"split", "plein"})
        else:
            assert any(d == "punch" for _, _, d, _ in plans)
        ss = sons(plans, vis, 38.0, 38.0)
        assert all(s["t"] < 40 for s in ss) and ss[-1]["role"] == "pop"
    assert cadrage(1920, 1080, .5, 1.0, W / H) == (606, 1078, 657, 0) or cadrage(1920, 1080, .5, 1.0, W / H)[1] == 1080
    with tempfile.TemporaryDirectory() as tmp:
        t = Path(tmp)
        C.run(["ffmpeg", "-y", "-v", "error", "-f", "lavfi", "-i", "testsrc=duration=12:size=1280x720:rate=25", "-f", "lavfi", "-i",
               "aevalsrc='0.4*sin(2*PI*220*t)*mod(floor(t*4),2)':s=48000:d=12", "-c:v", "libx264", "-preset", "ultrafast",
               "-pix_fmt", "yuv420p", "-c:a", "aac", t / "prise.mp4"])
        C.test_video(t / "clip.mp4", 2.0, "640x360", son=False)
        mots = [(f" mot{k}{',' if k % 4 == 3 else ''}", k * .25, k * .25 + .2) for k in range(46)]
        C.ecrire_mots(mots, t / "t.json")
        (t / "visuels.json").write_text(json.dumps({"visuels": [
            {"de": 1.5, "a": 4.0, "type": "texto", "fort": "Le message", "messages": [["elle", "On parle ?"], ["toi", "Oui."]]},
            {"de": 5.0, "a": 7.0, "type": "clip", "fort": "Dehors", "fichier": "clip.mp4"},
            {"de": 7.5, "a": 9.5, "type": "liste", "fort": "Ce qui marche", "items": ["écouter", "attendre"]}],
            "punch": [4.5], "appel": 10.0}), encoding="utf-8")
        r = monter(t / "prise.mp4", t / "t.json", "rythme", t / "visuels.json", .5, "essai", musique="aucune", dossier=t / "r")
        i = C.infos(r)
        assert (i["w"], i["h"]) == (1080, 1920) and abs(i["duree"] - 12) < .2 and i["son"], i
        p = json.loads((t / "r" / "plan.json").read_text(encoding="utf-8"))
        assert {"split", "visage", "appel"} <= {x[2] for x in p["plans"]}
        roles = {s["role"] for s in json.loads((t / "r" / "sons.json").read_text(encoding="utf-8"))}
        assert {"whoosh", "notification", "clic", "tick", "pop"} <= roles, roles
        ev = json.loads((t / "r" / "reel.evenements.json").read_text(encoding="utf-8"))
        assert {"texto", "liste", "sous-titre", "appel"} <= {e["type"] for e in ev}
        r2 = monter(t / "prise.mp4", t / "t.json", "editorial", t / "visuels.json", .5, "essai", musique="aucune",
                    dossier=t / "e", apercu=True)
        assert (C.infos(r2)["w"], C.infos(r2)["h"]) == (540, 960)
        r3 = monter(t / "prise.mp4", t / "t.json", "simple", None, .5, None, "Une accroche", "aucune", t / "s", apercu=True)
        assert C.infos(r3)["h"] == 960
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Prise face caméra -> Reel 1080x1920 monté à un gabarit (ffmpeg seul).")
    ap.add_argument("prise", nargs="?")
    ap.add_argument("transcription", nargs="?")
    ap.add_argument("--gabarit", choices=("rythme", "editorial", "simple"), default="rythme")
    ap.add_argument("--visuels")
    ap.add_argument("--centre", type=float, default=.5)
    ap.add_argument("--mot-cle")
    ap.add_argument("--titre")
    ap.add_argument("--musique", default="auto")
    ap.add_argument("-o", "--dossier")
    ap.add_argument("--miroir", action="store_true")
    ap.add_argument("--apercu", action="store_true")
    ap.add_argument("--charte")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    elif a.prise and a.transcription:
        monter(a.prise, a.transcription, a.gabarit, a.visuels, a.centre, a.mot_cle, a.titre, a.musique, a.dossier, a.miroir,
               a.apercu, a.charte)
    else:
        ap.print_help()
