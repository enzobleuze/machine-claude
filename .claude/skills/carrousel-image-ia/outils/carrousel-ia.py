"""carrousel-ia.py : le livre de règles d'un carrousel aux images générées par IA, rendu bloquant AVANT le premier crédit,
puis les prompts aux couleurs de la charte, la banque d'images réutilisables et la finition en 1080x1350.

À lancer depuis la racine du vault. Besoin : carrousel.py (skill carrousel-html) dans le même dossier, ffmpeg pour finir.
  python outils/carrousel-ia.py exemple > outputs/carrousels/<slug>/slides.json        (modèle complet à remplir)
  python outils/carrousel-ia.py verifier outputs/carrousels/<slug>/slides.json
  python outils/carrousel-ia.py prompts  outputs/carrousels/<slug>/slides.json [--credit 0.5] [--budget 20] [--sans-texte]
  python outils/carrousel-ia.py finir    outputs/carrousels/<slug>
  python outils/carrousel-ia.py banque   outputs/carrousels/<slug>/slides.json 2,3     (slides aimées : elles pourront revenir)
  python outils/carrousel-ia.py --test

slides.json : {"modele": "affiche|verre", "script": {...}, "legende": "...", "slides": [...]}, voir EXEMPLE plus bas.
Contrôles bloquants : script complet (destination et phrase prouvée, accroche, boucles payées dans le carrousel, longueur
égale au nombre de slides, de 6 à 15, une slide à garder, mot du commentaire présent en fin et en légende) ; chaîne
(chaque slide répond à la précédente et ouvre la suivante) ; ouverture dépendante (« Et donc »...) ; une seule action, en
dernière slide ; plafonds de lecture (titre 6 mots, texte 20 mots, 3 lignes et 2 phrases, 1 mot d'accent, phrase de 16 mots,
slide à garder 55 mots, couverture et fin 26 mots) ; tiret long ; « glisse » ; visage repris d'une image générée ;
image de la banque revenue trop tôt ou avec le même texte. « prompts » exige en plus le verdict VERT du board.
"""
import argparse, importlib.util, json, re, shutil, subprocess, sys, tempfile
from pathlib import Path

ICI = Path(__file__).resolve().parent
for _d in (ICI, ICI.parents[1] / "carrousel-html" / "outils"):
    if (_d / "carrousel.py").exists():
        _s = importlib.util.spec_from_file_location("carrousel", _d / "carrousel.py")
        C = importlib.util.module_from_spec(_s)
        _s.loader.exec_module(C)
        break
else:
    raise SystemExit("carrousel.py introuvable : installe d'abord le skill carrousel-html (même dossier outils/).")

BANQUE = Path("bibliotheque/images/banque-carrousels.json")
ATTENTE = 5  # une image de la banque revient après 5 autres carrousels
ROLES = {  # énergie visuelle par rôle : le rythme se voit en feuilletant vite
    "couverture": "haute : image forte, titre énorme, une seule chose à regarder",
    "reponse": "haute : même gabarit et même place que la couverture, elle y répond tout de suite",
    "contexte": "basse : texte presque seul, beaucoup d'air",
    "etape": "moyenne : image chaude et texturée",
    "tension": "haute : image inattendue, conceptuelle",
    "bascule": "haute : change de famille de fond par rapport à la slide d'avant",
    "payoff": "moyenne : propre, résolu, ouvert",
    "garder": "moyenne : une carte claire et lisible (liste, plan ou script à garder)",
    "action": "basse : fond simple, le mot-clé en couleur d'accent",
}
MODELES = {
    "affiche": "photo pleine page au rendu de film, sujet net, le tiers haut reste calme pour le texte, grand et net",
    "verre": "fond sombre et profond, cartes en verre dépoli translucide posées dessus, texte dans les cartes, lumière douce qui vient de l'écran",
}
OUVERTURES = re.compile(r"(?i)^\s*(?:et donc|c'est pour ça que|voilà pourquoi|comme on l'a vu)\b")
ACTIONS = re.compile(r"(?i)\b(?:enregistre|partage|abonne-toi|suis-moi|lien en bio)\b")
APPEL = re.compile(r"(?i)(?:[ée]cris|commente)\s+\*?([A-ZÉÈÀÂÎÔÛÇ]{3,})")
INTERDITS = ("texte déformé ou inventé, lettres en trop ; mains abîmées ; logos, marques ou filigranes ; fausse interface "
             "d'application ; tiret long ; plus de trois couleurs fortes ; visage générique au sourire publicitaire")

EXEMPLE = {
    "modele": "affiche",
    "script": {"destination": "Il croit qu'arroser plus sauve ses tomates ; il touche la terre avant d'arroser. Phrase prouvée : la terre dit quand arroser.",
               "accroche": "Il arrose tous les soirs et ses tomates craquent.",
               "boucles": [{"ouvre": 1, "paie": 5}],
               "longueur": {"slides": 6, "raison": "une couverture, sa réponse, deux étapes, le plan à garder, l'action"},
               "sauvegarde": [5],
               "commentaire": {"mot": "POTAGER", "recoit": "le plan d'arrosage en vidéo"}},
    "legende": "Tes tomates craquent alors que tu arroses tous les soirs.\nÉcris POTAGER en commentaire et je t'envoie le plan d'arrosage en vidéo.\n\n#potager #jardin #tomates",
    "slides": [
        {"role": "couverture", "titre": "Tes tomates *craquent* ?", "texte": "Tu arroses pourtant tous les soirs.",
         "ouvre": "Pourquoi l'eau ne suffit pas ?", "fond": "sombre", "scene": "une tomate fendue au soleil couchant, gros plan"},
        {"role": "reponse", "titre": "Elles boivent trop d'un coup.", "repond": "Pourquoi l'eau ne suffit pas ?",
         "ouvre": "Que faire à la place ?", "fond": "sombre", "scene": "un arrosoir qui déborde sur la terre"},
        {"role": "etape", "titre": "Touche la terre.", "texte": "Enfonce un doigt avant d'arroser.", "repond": "Que faire à la place ?",
         "ouvre": "Et si elle est humide ?", "fond": "clair", "scene": "une main dans la terre, lumière du matin"},
        {"role": "etape", "titre": "Humide ? Attends demain.", "repond": "Et si elle est humide ?", "ouvre": "Comment s'en souvenir ?",
         "fond": "sombre", "scene": "un rang de tomates sous un ciel gris"},
        {"role": "garder", "titre": "Ton plan d'arrosage", "texte": "Le matin, touche la terre.\nSèche : arrose au pied.\nHumide : attends demain.",
         "repond": "Comment s'en souvenir ?", "ouvre": "Comment avoir le plan complet ?", "fond": "clair", "scene": "une carte posée sur une table de jardin"},
        {"role": "action", "titre": "Écris *POTAGER*", "texte": "et je t'envoie le plan d'arrosage en vidéo.",
         "repond": "Comment avoir le plan complet ?", "fond": "sombre", "scene": "un potager au lever du jour, calme"},
    ],
}


def mots(t):
    return len(re.findall(r"\w+", t or ""))


def phrases(t):
    return [p for p in re.split(r"(?<=[.!?…])\s+", (t or "").replace("\\n", "\n").replace("\n", " ").strip()) if p]


def lignes(t):
    return [l for l in (t or "").replace("\\n", "\n").split("\n") if l.strip()]


def banque():
    return json.loads(BANQUE.read_text(encoding="utf-8")) if BANQUE.exists() else {"journal": [], "images": {}}


def verifier(spec, slug="", bq=None):
    e, sc, sl = [], spec.get("script") or {}, spec.get("slides") or []
    n = len(sl)
    for k in ("destination", "accroche", "boucles", "longueur", "sauvegarde", "commentaire"):
        if not sc.get(k):
            e.append(f"script : « {k} » manquant")
    if sc.get("destination") and "phrase prouvée" not in sc["destination"].lower():
        e.append("script : finis la destination par « Phrase prouvée : ... » (la phrase que tout le carrousel prouve)")
    lg = sc.get("longueur") or {}
    if lg and (lg.get("slides") != n or not lg.get("raison")):
        e.append(f"script : longueur {lg.get('slides')} pour {n} slides, ou raison absente")
    if not 6 <= n <= 15:
        e.append(f"{n} slides : de 6 à 15 (le sujet décide)")
    b = sc.get("boucles") or []
    if b and not any(x.get("ouvre") == 1 for x in b):
        e.append("script : la couverture doit ouvrir une boucle")
    e += [f"script : la boucle ouverte en {x.get('ouvre')} se paie en {x.get('paie')}, hors du carrousel" for x in b
          if not (isinstance(x.get("paie"), int) and (x.get("ouvre") or 0) < x["paie"] <= n)]
    gardes = sc.get("sauvegarde") or []
    e += [f"script : slide à garder {g} inexistante" for g in gardes if not (isinstance(g, int) and 1 <= g <= n)]
    mot = (sc.get("commentaire") or {}).get("mot", "")
    if sc.get("commentaire"):
        if not re.fullmatch(r"[A-ZÉÈÀÂÎÔÛÇ]{3,}", mot) or not (sc["commentaire"].get("recoit") or "").strip():
            e.append("script : le mot du commentaire est un seul mot en capitales, avec ce qu'il reçoit")
        elif n and mot not in json.dumps(sl[-1], ensure_ascii=False):
            e.append(f"dernière slide : le mot {mot} n'y est pas")
        if mot and mot not in spec.get("legende", ""):
            e.append(f"légende : le mot {mot} n'y est pas")
    leg = spec.get("legende", "")
    if not leg.strip():
        e.append("légende absente")
    if ACTIONS.search(leg):
        e.append(f"légende : une seule action (« {ACTIONS.search(leg).group(0)} » en trop)")
    vus = set()
    for i, s in enumerate(sl, 1):
        t = f"slide {i}"
        titre, texte, etiq = s.get("titre", ""), s.get("texte", ""), s.get("etiquettes", [])
        tout = " ".join([titre, texte, *etiq])
        if i > 1 and not s.get("repond"):
            e.append(f"{t} : « repond » vide (à quelle question de la slide d'avant répond-elle ?)")
        if i < n and not s.get("ouvre"):
            e.append(f"{t} : « ouvre » vide (quelle question laisse-t-elle pour la suivante ?)")
        if OUVERTURES.search(titre or texte):
            e.append(f"{t} : ouverture dépendante (« {OUVERTURES.search(titre or texte).group(0).strip()} »), une slide se lit seule")
        if (APPEL.search(tout) and i < n) or ACTIONS.search(tout):
            e.append(f"{t} : une seule action, et seulement en dernière slide")
        if C.GLISSER.search(tout):
            e.append(f"{t} : « glisse » ou « swipe » interdit")
        if chr(0x2014) in tout or chr(0x2013) in tout:  # tiret long ou moyen
            e.append(f"{t} : tiret long ou moyen")
        if s.get("role") not in ROLES:
            e.append(f"{t} : rôle « {s.get('role')} » inconnu ({', '.join(ROLES)})")
        if not s.get("scene"):
            e.append(f"{t} : « scene » manquante (ce que montre l'image)")
        if mots(titre) > 6:
            e.append(f"{t} : titre de {mots(titre)} mots, 6 au plus")
        accent = sum(mots(m) for m in re.findall(r"\*(.+?)\*", tout))
        if accent > 1:
            e.append(f"{t} : {accent} mots en accent, 1 au plus")
        e += [f"{t} : phrase de {mots(p)} mots, 16 au plus" for p in phrases(tout.replace("*", "")) if mots(p) > 16]
        if i in gardes:
            if mots(tout) > 55:
                e.append(f"{t} : slide à garder de {mots(tout)} mots, 55 au plus")
        else:
            if mots(texte) > 20 or len(phrases(texte)) > 2:
                e.append(f"{t} : texte de {mots(texte)} mots et {len(phrases(texte))} phrases, 20 mots et 2 phrases au plus")
            if i in (1, n):
                if mots(tout) > 26:
                    e.append(f"{t} : couverture ou fin de {mots(tout)} mots, 26 au plus")
            elif len(lignes(texte)) > 3:
                e.append(f"{t} : {len(lignes(texte))} lignes, 3 au plus")
        if s.get("visage") and any(str(r).replace("\\", "/").startswith("outputs/") for r in s.get("references", [])):
            e.append(f"{t} : visage tiré d'une image générée (il « cuit » à chaque passage) : seulement la photo d'origine")
        if s.get("image") and bq is not None:
            im = bq["images"].get(s["image"])
            if not im:
                e.append(f"{t} : image « {s['image']} » absente de la banque")
                continue
            us, j = im.get("usages", []), bq["journal"]
            # carrousels finis depuis son dernier usage ; un carrousel déjà fini (slug au journal) n'est plus jugé
            if us and slug not in j and us[-1]["carrousel"] in j and len(j) - 1 - j.index(us[-1]["carrousel"]) < ATTENTE:
                e.append(f"{t} : image « {s['image']} » servie il y a moins de {ATTENTE} carrousels")
            if any(u.get("texte") == titre for u in us):
                e.append(f"{t} : image « {s['image']} » déjà vue avec ce même titre")
            if i == 1 and us and j and us[-1]["carrousel"] == j[-1] and us[-1].get("couverture"):
                e.append(f"{t} : cette image était déjà la couverture du carrousel précédent")
            if s["image"] in vus:
                e.append(f"{t} : image « {s['image']} » deux fois dans le même carrousel")
            vus.add(s["image"])
    return e


def recette():
    """Recette d'image de la marque : section « Recette » de wiki/maps/style-maison.md (skill images-de-marque)."""
    f = Path("wiki/maps/style-maison.md")
    m = re.search(r"^#+ .*[Rr]ecette.*\n(.*?)(?=^#+ |\Z)", f.read_text(encoding="utf-8"), re.S | re.M) if f.exists() else None
    return " ".join(m.group(1).split()) if m else "lumière naturelle douce, grain léger, couleurs de la palette, sujet réel et simple"


def prompt(spec, i, jt, sans_texte):
    s, n = spec["slides"][i - 1], len(spec["slides"])
    th = jt[s["fond"] if s.get("fond") in ("clair", "sombre") else jt.get("principal", "clair")]
    accent = [m for m in re.findall(r"\*(.+?)\*", " ".join([s.get("titre", ""), s.get("texte", "")]))]
    net = lambda x: x.replace("*", "").replace("\\n", " / ").replace("\n", " / ")
    if sans_texte:
        txt = "AUCUN TEXTE dans l'image : garde le tiers haut calme et libre, le texte sera posé ensuite."
    else:
        txt = ("TEXTE EXACT À ÉCRIRE, rien d'autre, sans faute, espaces avant ? ! : comme en français :\n"
               + (f"- titre (énorme) : « {net(s['titre'])} »\n" if s.get("titre") else "")
               + (f"- texte (environ deux fois plus petit) : « {net(s['texte'])} »\n" if s.get("texte") else "")
               + "".join(f"- petite étiquette : « {net(x)} »\n" for x in s.get("etiquettes", []))
               + (f"- seul mot en couleur d'accent ({th['accent']}) : « {accent[0]} » ; tout le reste en {th['texte']}\n" if accent else "")
               + "Hiérarchie lisible les yeux plissés et à bout de bras ; lettres nettes, aucun accent ne touche la ligne du dessus.")
    return "\n".join([
        f"FORMAT : image verticale 4:5 (1080x1350), slide {i} sur {n} d'un carrousel Instagram.",
        f"MODÈLE : {MODELES.get(spec.get('modele', 'affiche'), MODELES['affiche'])}.",
        f"RÔLE : {s['role']}, énergie {ROLES[s['role']]}.",
        f"SCÈNE : {s['scene']}.",
        f"FOND : famille {s.get('fond', jt.get('principal', 'clair'))} (sombre pour la tension, clair pour la relâche).",
        f"PALETTE DE LA MARQUE : fond {th['fond']}, texte {th['texte']}, accent {th['accent']}, accent 2 {th['accent_2']}. "
        f"Ambiance : {', '.join(jt.get('mots', []))}.",
        f"TYPOGRAPHIE : titres en {jt['polices']['titres']}, texte en {jt['polices']['texte']}.",
        txt,
        f"RECETTE MAISON : {recette()}.",
        *(["VISAGE : uniquement la photo de référence d'origine jointe, jamais une image générée."] if s.get("visage") else []),
        f"INTERDITS : {INTERDITS}.",
    ])


def porte(d):
    p = Path("scripts/porte_board.py")
    if p.exists():
        r = subprocess.run([sys.executable, str(p), "verifier", str(d / "slides.json"), str(d / "board.md")], capture_output=True, text=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[-300:]
    b = d / "board.md"
    v = re.findall(r"^## Verdict : (.+)$", b.read_text(encoding="utf-8"), re.M) if b.exists() else []
    return bool(v) and v[-1].strip().upper().startswith("VERT"), f"verdict : {v[-1] if v else 'board non passé'} (porte absente)"


def cmd_verifier(f):
    f = Path(f)
    e = verifier(json.loads(f.read_text(encoding="utf-8")), f.parent.name, banque())
    print("\n".join(f"- {x}" for x in e) if e else "Livre de règles : tout passe.")
    return 1 if e else 0


def cmd_prompts(f, credit, budget, sans_texte):
    f = Path(f)
    spec, d = json.loads(f.read_text(encoding="utf-8")), f.parent
    e = verifier(spec, d.name, banque())
    ok, pourquoi = porte(d)
    if not ok:
        e.append(f"board : {pourquoi}. Aucun crédit avant le verdict VERT sur ce texte exact.")
    if e:
        print("Refusé :\n" + "\n".join(f"- {x}" for x in e))
        return 1
    jt, _, _ = C.charger_charte(None, d)
    (d / "prompts").mkdir(exist_ok=True)
    reqs, bq = [], banque()
    for i in range(1, len(spec["slides"]) + 1):
        p = prompt(spec, i, jt, sans_texte)
        (d / "prompts" / f"{i:02d}.txt").write_text(p, encoding="utf-8")
        s = spec["slides"][i - 1]
        refs = list(s.get("references", [])) + ([bq["images"][s["image"]]["fichier"]] if s.get("image") else [])
        reqs.append({"n": i, "ratio": "4:5", "prompt": p, "references": refs, "sortie": f"brut/{i:02d}"})
    (d / "requests.json").write_text(json.dumps(reqs, ensure_ascii=False, indent=1), encoding="utf-8")
    cout = len(reqs) * credit
    print(f"{len(reqs)} prompts dans {d / 'prompts'} ; coût estimé {cout:g} crédits (plus 2 reprises au plus : {cout + 2 * credit:g}).")
    if budget is not None and cout + 2 * credit > budget:
        print(f"ATTENTION : au-delà du budget restant ({budget:g}). Demande avant de générer.")
        return 2
    print("Génère d'abord la couverture seule et montre-la. Le reste seulement après son oui.")
    return 0


def cmd_finir(d):
    d = Path(d)
    spec = json.loads((d / "slides.json").read_text(encoding="utf-8"))
    if not shutil.which("ffmpeg"):
        raise SystemExit("ffmpeg introuvable : installe-le (Windows : winget install ffmpeg).")
    faits = []
    for i in range(1, len(spec["slides"]) + 1):
        src = next((p for p in sorted((d / "brut").glob(f"{i:02d}.*"))), None)
        if not src:
            raise SystemExit(f"image brute manquante : brut/{i:02d}.(png|jpg|webp)")
        out = d / f"slide-{i:02d}.jpg"
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-vf",
                            "scale=1080:1350:force_original_aspect_ratio=increase,crop=1080:1350", "-q:v", "2", str(out)],
                           capture_output=True, text=True)
        if r.returncode:
            raise SystemExit(f"ffmpeg : {r.stderr[-300:]}")
        faits.append(out)
    bq = banque()
    if d.name not in bq["journal"]:
        bq["journal"].append(d.name)
        for i, s in enumerate(spec["slides"], 1):
            if s.get("image") in bq["images"]:
                bq["images"][s["image"]]["usages"].append({"carrousel": d.name, "rang": i, "texte": s.get("titre", ""), "couverture": i == 1})
        BANQUE.parent.mkdir(parents=True, exist_ok=True)
        BANQUE.write_text(json.dumps(bq, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(faits)} slides finies dans {d}. Planche : python outils/planche.py \"{d.as_posix()}/slide-*.jpg\" -o {d.as_posix()}/planche.jpg")
    return 0


def cmd_banque(f, rangs):
    f = Path(f)
    spec, d, bq = json.loads(f.read_text(encoding="utf-8")), f.parent, banque()
    for r in (int(x) for x in rangs.split(",")):
        s = spec["slides"][r - 1]
        if s.get("visage"):
            print(f"slide {r} : un visage n'entre jamais dans la banque (il cuirait en référence)")
            continue
        img = d / f"slide-{r:02d}.jpg"
        if not img.exists():
            print(f"slide {r} : {img} absente, lance d'abord « finir »")
            continue
        cle = f"{d.name}-{r:02d}"
        bq["images"].setdefault(cle, {"fichier": img.as_posix(), "scene": s.get("scene", ""), "usages": [
            {"carrousel": d.name, "rang": r, "texte": s.get("titre", ""), "couverture": r == 1}]})
        print(f"banque : {cle}")
    if d.name not in bq["journal"]:
        bq["journal"].append(d.name)
    BANQUE.parent.mkdir(parents=True, exist_ok=True)
    BANQUE.write_text(json.dumps(bq, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


def auto_test():
    import os
    assert verifier(EXEMPLE) == [], verifier(EXEMPLE)
    casse = lambda f: (lambda s: (f(s), verifier(s))[1])(json.loads(json.dumps(EXEMPLE)))
    assert any("6 au plus" in x for x in casse(lambda s: s["slides"][2].update(titre="Un titre bien trop long pour la slide")))
    assert any("accent" in x for x in casse(lambda s: s["slides"][2].update(titre="*Touche* la *terre*.")))
    assert any("repond" in x for x in casse(lambda s: s["slides"][3].pop("repond")))
    assert any("action" in x for x in casse(lambda s: s["slides"][2].update(texte="Écris POTAGER maintenant.")))
    assert any("action" in x for x in casse(lambda s: s.update(legende=s["legende"] + "\nPartage ce post.")))
    assert any("boucle" in x for x in casse(lambda s: s["script"].update(boucles=[{"ouvre": 2, "paie": 9}])))
    assert any("longueur" in x for x in casse(lambda s: s["script"]["longueur"].update(slides=7)))
    assert any("dépendante" in x for x in casse(lambda s: s["slides"][3].update(titre="Et donc, attends.")))
    assert any("cuit" in x for x in casse(lambda s: s["slides"][0].update(visage=True, references=["outputs/carrousels/x/slide-01.jpg"])))
    assert any("phrase" in x for x in casse(lambda s: s["slides"][4].update(texte="Le matin tu touches la terre avec un doigt puis tu regardes si elle colle encore un peu.")))
    ici = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            d = Path("outputs/carrousels/potager")
            d.mkdir(parents=True)
            (d / "slides.json").write_text(json.dumps(EXEMPLE, ensure_ascii=False), encoding="utf-8")
            assert cmd_prompts(d / "slides.json", 0.5, None, False) == 1, "sans board, aucun prompt"
            (d / "board.md").write_text("## Verdict : VERT\n", encoding="utf-8")
            assert cmd_prompts(d / "slides.json", 0.5, None, False) == 0
            p1 = (d / "prompts" / "01.txt").read_text(encoding="utf-8")
            assert "#2f5bd3" not in p1 and "#4068d7" in p1 and "« Tes tomates craquent ? »" in p1, p1  # fond sombre : accent sombre
            assert len(json.loads((d / "requests.json").read_text(encoding="utf-8"))) == 6
            assert cmd_prompts(d / "slides.json", 0.5, 3, False) == 2, "budget dépassé"
            assert "AUCUN TEXTE" in prompt(EXEMPLE, 2, C.SIMPLE_JETONS, True)
            if shutil.which("ffmpeg"):
                (d / "brut").mkdir()
                for i in range(1, 7):
                    C._png_test(d / "brut" / f"{i:02d}.png", 64, 64)
                assert cmd_finir(d) == 0
                r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height", "-of", "csv=p=0", str(d / "slide-01.jpg")],
                                   capture_output=True, text=True)
                assert r.stdout.strip() == "1080,1350", r.stdout
                cmd_banque(d / "slides.json", "3")
                bq = banque()
                assert "potager-03" in bq["images"] and bq["journal"] == ["potager"]
                s2 = json.loads(json.dumps(EXEMPLE))
                s2["slides"][2]["image"] = "potager-03"
                assert any("moins de" in x for x in verifier(s2, "nouveau", bq)), "image revenue trop tôt"
                bq["journal"] += [f"c{k}" for k in range(ATTENTE)]
                assert any("même titre" in x for x in verifier(s2, "nouveau", bq))
                s2["slides"][2]["titre"] = "Plonge un doigt."
                assert verifier(s2, "nouveau", bq) == []
            else:
                print("ffmpeg absent : finition non testée")
        finally:
            os.chdir(ici)
    print("AUTO-TEST OK")
    return 0


def main():
    if sys.argv[1:] == ["--test"]:
        return auto_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("verifier").add_argument("json")
    p = sub.add_parser("prompts"); p.add_argument("json"); p.add_argument("--credit", type=float, default=1.0)
    p.add_argument("--budget", type=float); p.add_argument("--sans-texte", action="store_true")
    sub.add_parser("finir").add_argument("dossier")
    b = sub.add_parser("banque"); b.add_argument("json"); b.add_argument("rangs")
    sub.add_parser("exemple")
    a = ap.parse_args()
    if a.cmd == "verifier":
        return cmd_verifier(a.json)
    if a.cmd == "prompts":
        return cmd_prompts(a.json, a.credit, a.budget, a.sans_texte)
    if a.cmd == "finir":
        return cmd_finir(a.dossier)
    if a.cmd == "banque":
        return cmd_banque(a.json, a.rangs)
    print(json.dumps(EXEMPLE, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
