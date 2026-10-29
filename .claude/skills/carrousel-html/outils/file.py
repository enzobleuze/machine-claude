"""file.py : la revue et la file des carrousels. La personne revoit tout sur une page, dit oui, non ou une remarque ;
seuls les « oui » entrent dans la file, un carrousel par jour, en alternant les styles. Chaque jour, le carrousel prévu
est préparé (JPEG, légende, limites de chaque réseau) puis écrit dans la file de publication que vide le skill
distribution-api. Bibliothèque standard seule ; ffmpeg pour passer les PNG en JPEG (Instagram refuse le PNG par API).

À lancer depuis la racine du vault.
  python outils/file.py revue                        page outputs/carrousels/revue/index.html (+ revue.json numéroté)
  python outils/file.py ajouter 1,4 [--pas-avant 4:2026-11-02]    les « oui » de la revue entrent dans la file
  python outils/file.py retirer 2                    sort de la file (pas encore publié)
  python outils/file.py etat
  python outils/file.py du-jour [--date AAAA-MM-JJ] [--a-blanc]     tâche quotidienne
  python outils/file.py --test

Un carrousel prêt = un dossier outputs/carrousels/<slug>/ avec slides.json (texte, et "legende" : la légende, pour que
le board couvre les deux), ses images (png/slide-NN.png du rendu local, ou slide-NN.jpg d'un carrousel image IA) et
board.md. Refus à l'entrée dans la file : board pas VERT (porte scripts/porte_board.py si elle existe), légende absente,
trop longue (2 200 caractères), avec un tiret long ou une formule refusée.
Réglages : outputs/carrousels/reseaux.json (écrit au premier lancement) : heure, rotation des styles, et pour chaque
réseau le nombre d'images au plus et si le mot-clé en commentaire y déclenche un message privé.
"""
import argparse, html, json, os, re, shutil, subprocess, sys, tempfile
from datetime import date, datetime, timedelta
from pathlib import Path

O = Path("outputs/carrousels")
FILE, REVUE, PUB, REGLAGES = O / "file.json", O / "revue" / "revue.json", O / "publication", O / "reseaux.json"
FILE_PUB = Path("outputs/file-publication")
DEFAUT = {"heure": "13:30",
          "rotation": ["split", "conversation", "image-ia", "reel", "uni", "podcast", "edito"],
          "reseaux": {"instagram": {"max": 10, "mot_cle": True}, "facebook": {"max": 10, "mot_cle": True}}}
REFUS = [r"\bglisse\b", r"\bswipe\b", r"situation type", r"mise en scène", r"personne ne (?:peut|pourra) te (?:le )?promettre"]
APPEL = re.compile(r"(?i)(?:[ée]cris|commente)\s+\*?([A-ZÉÈÀÂÎÔÛÇ]{3,})\*?")


def lire(f, defaut):
    return json.loads(Path(f).read_text(encoding="utf-8")) if Path(f).exists() else defaut


def ecrire(f, donnees):
    Path(f).parent.mkdir(parents=True, exist_ok=True)
    Path(f).write_text(json.dumps(donnees, ensure_ascii=False, indent=1), encoding="utf-8")


def reglages():
    if not REGLAGES.exists():
        ecrire(REGLAGES, DEFAUT)
    return {**DEFAUT, **lire(REGLAGES, {})}


def images(d):
    d = Path(d)
    return sorted(d.glob("png/slide-*.png")) or sorted([*d.glob("slide-*.jpg"), *d.glob("slide-*.png")])


def style_de(spec):
    if spec.get("modele") or spec.get("script"):
        return "image-ia"
    if spec.get("style") == "edito" and any(s.get("messages") for s in spec.get("slides", [])):
        return "conversation"
    return spec.get("style", "?")


def verdict(d):
    b = Path(d) / "board.md"
    v = re.findall(r"^## Verdict : (.+)$", b.read_text(encoding="utf-8"), re.M) if b.exists() else []
    return v[-1].strip() if v else "board non passé"


def fautes_legende(leg):
    f = [m.group(0) for r in REFUS for m in re.finditer(r, leg, re.I)]
    if not leg.strip():
        f.append("légende absente (champ \"legende\" de slides.json)")
    if len(leg) > 2200:
        f.append(f"légende de {len(leg)} caractères, 2 200 au plus")
    if chr(0x2014) in leg or chr(0x2013) in leg:  # tiret long ou moyen
        f.append("tiret long dans la légende")
    return f


def porte_ouverte(d):
    """Le board a-t-il validé CE texte ? Porte du skill board-textes si elle est installée, sinon le titre du verdict."""
    porte = Path("scripts/porte_board.py")
    if porte.exists():
        r = subprocess.run([sys.executable, str(porte), "verifier", str(Path(d) / "slides.json"), str(Path(d) / "board.md")],
                           capture_output=True, text=True)
        return r.returncode == 0, (r.stdout + r.stderr).strip()[-200:]
    v = verdict(d)
    return v.upper().startswith("VERT"), f"verdict : {v} (porte absente, empreinte non vérifiée)"


def stock():
    """Carrousels prêts à revoir : un dossier avec slides.json et des images, pas encore publié."""
    publies = {x["dossier"] for x in lire(FILE, []) if x.get("statut") in ("programme", "publie")}
    out = []
    for d in sorted(p for p in O.glob("*/") if (p / "slides.json").exists() and images(p)):
        if d.as_posix() in publies:
            continue
        spec = lire(d / "slides.json", {})
        out.append({"dossier": d.as_posix(), "style": style_de(spec), "board": verdict(d), "legende": spec.get("legende", "")})
    return out


def page_revue(items, en_file):
    racine = REVUE.parent
    charte = Path("bibliotheque/marque/charte.css")
    lien = f'<link rel="stylesheet" href="{html.escape(os.path.relpath(charte, racine).replace(os.sep, "/"))}">' if charte.exists() else ""
    cartes = []
    for n, x in enumerate(items, 1):
        imgs = "".join(f'<img src="{html.escape(os.path.relpath(p, racine).replace(os.sep, "/"))}" loading="lazy" alt="">' for p in images(x["dossier"]))
        etat = " · déjà en file" if x["dossier"] in en_file else ""
        leg = f'<details><summary>Légende</summary><pre>{html.escape(x["legende"])}</pre></details>' if x["legende"] else ""
        cartes.append(f'''<section data-n="{n}"><h2><span>{n}</span> {html.escape(Path(x["dossier"]).name)} <em>{html.escape(x["style"])} · board : {html.escape(x["board"])}{etat}</em></h2>
<div class="rang">{imgs}</div>{leg}
<div class="choix"><button data-v="oui">Oui</button><button data-v="non">Non</button><textarea placeholder="Ta remarque (facultatif)"></textarea></div></section>''')
    return f'''<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Revue des carrousels</title>{lien}<style>
body{{margin:0;padding:20px 16px 90px;background:var(--fond,Canvas);color:var(--texte,CanvasText);font:16px var(--police-texte,system-ui,sans-serif)}}
h1{{font:600 24px var(--police-titres,system-ui,sans-serif)}} section{{background:var(--surface,Canvas);border:1px solid var(--ligne,GrayText);border-radius:var(--rayon,10px);padding:14px;margin:0 0 16px}}
h2{{font-size:16px;margin:0 0 10px}} h2 span{{background:var(--accent,Highlight);color:var(--accent-texte,HighlightText);border-radius:6px;padding:2px 8px;margin-right:6px}}
h2 em{{font-style:normal;font-size:13px;color:var(--texte-doux,GrayText);margin-left:6px}} .rang{{display:flex;gap:8px;overflow-x:auto}} .rang img{{height:280px;border-radius:6px}}
pre{{white-space:pre-wrap;font:14px inherit}} .choix{{display:flex;gap:8px;margin-top:10px;flex-wrap:wrap}} button{{font:inherit;padding:8px 18px;border-radius:8px;border:1px solid var(--ligne,GrayText);background:var(--fond,Canvas);color:inherit;cursor:pointer}}
button.actif{{background:var(--accent,Highlight);color:var(--accent-texte,HighlightText)}} textarea{{flex:1;min-width:200px;font:inherit;padding:8px;border-radius:8px;border:1px solid var(--ligne,GrayText);background:var(--fond,Canvas);color:inherit}}
footer{{position:fixed;left:0;right:0;bottom:0;padding:12px 16px;background:var(--surface-2,Canvas);border-top:1px solid var(--ligne,GrayText);display:flex;gap:10px;align-items:center}}
footer code{{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}</style></head><body>
<h1>Revue des carrousels ({len(items)})</h1><p>Pour chaque carrousel : Oui, Non, et une remarque si tu veux. Puis « Copier ma réponse » et colle-la à Claude. Rien ne part sans ton oui.</p>
{"".join(cartes)}<footer><code id="reponse">Aucun choix pour l'instant.</code><button id="copier">Copier ma réponse</button></footer>
<script>
const CLE = "revue-carrousels-" + {len(items)}; let etat = {{}};
try {{ etat = JSON.parse(localStorage.getItem(CLE) || "{{}}"); }} catch (e) {{}}
function maj() {{
  const oui = [], non = [], notes = [];
  document.querySelectorAll("section").forEach(s => {{ const n = s.dataset.n, e = etat[n] || {{}};
    s.querySelectorAll("button").forEach(b => b.classList.toggle("actif", b.dataset.v === e.v));
    s.querySelector("textarea").value = e.note || "";
    if (e.v === "oui") oui.push(n); if (e.v === "non") non.push(n); if (e.note) notes.push(n + " : " + e.note); }});
  const t = [oui.length ? "oui " + oui.join(", ") : "", non.length ? "non " + non.join(", ") : "", ...notes].filter(Boolean).join(" · ");
  document.getElementById("reponse").textContent = t || "Aucun choix pour l'instant.";
  try {{ localStorage.setItem(CLE, JSON.stringify(etat)); }} catch (e) {{}} }}
document.querySelectorAll("section").forEach(s => {{ const n = s.dataset.n;
  s.querySelectorAll("button").forEach(b => b.onclick = () => {{ etat[n] = {{...(etat[n] || {{}}), v: b.dataset.v}}; maj(); }});
  s.querySelector("textarea").oninput = ev => {{ etat[n] = {{...(etat[n] || {{}}), note: ev.target.value}}; maj(); }}; }});
document.getElementById("copier").onclick = async () => {{ const t = document.getElementById("reponse").textContent;
  try {{ await navigator.clipboard.writeText(t); document.getElementById("copier").textContent = "Copié"; }}
  catch (e) {{ const r = document.createRange(); r.selectNode(document.getElementById("reponse")); getSelection().removeAllRanges(); getSelection().addRange(r); }} }};
maj();
</script></body></html>'''


def cmd_revue(_a=None):
    items = stock()
    en_file = {x["dossier"] for x in lire(FILE, []) if x.get("statut") == "en_file"}
    ecrire(REVUE, [{**x, "n": n} for n, x in enumerate(items, 1)])
    (REVUE.parent / "index.html").write_text(page_revue(items, en_file), encoding="utf-8")
    print(f"{len(items)} carrousels à revoir : {REVUE.parent / 'index.html'}")


def ordonner(items, rotation):
    """Jamais deux fois le même style de suite tant que c'est possible : le style qui a le plus de carrousels en attente
    passe d'abord, puis l'ordre de la rotation."""
    reste, out, dernier = list(items), [], None
    while reste:
        x = min(reste, key=lambda x: (x["style"] == dernier, -sum(1 for y in reste if y["style"] == x["style"]),
                                      rotation.index(x["style"]) if x["style"] in rotation else 99))
        out.append(x)
        reste.remove(x)
        dernier = x["style"]
    return out


def dater(f, heure, maintenant=None):
    """Un carrousel par jour, en respectant « pas avant » ; les carrousels déjà programmés gardent leur date."""
    maintenant = maintenant or datetime.now()
    h, m = map(int, heure.split(":"))
    jour = maintenant.date() + timedelta(days=0 if (maintenant.hour, maintenant.minute) < (h, m) else 1)
    pris = {x["date"] for x in f if x.get("statut") in ("programme", "publie")}
    for x in f:
        if x.get("statut") in ("programme", "publie"):
            continue
        j = max(jour, date.fromisoformat(x["pas_avant"])) if x.get("pas_avant") else jour
        while j.isoformat() in pris:
            j += timedelta(days=1)
        x["date"] = j.isoformat()
        pris.add(x["date"])
        if not x.get("pas_avant"):
            jour = j + timedelta(days=1)
    return sorted(f, key=lambda x: x["date"])


def refaire(f, nouveaux, rg):
    fixes = [x for x in f if x.get("statut") in ("programme", "publie")]
    return dater(fixes + ordonner([x for x in f if x.get("statut") == "en_file"] + nouveaux, rg["rotation"]), rg["heure"])


def cmd_ajouter(a):
    rg, rev, f = reglages(), {x["n"]: x for x in lire(REVUE, [])}, lire(FILE, [])
    deja = {x["dossier"] for x in f}
    pas_avant = dict(p.split(":", 1) for p in (a.pas_avant or "").split(",") if p)
    nouveaux, refus = [], []
    for n in (int(v) for v in a.numeros.split(",") if v.strip()):
        x = rev.get(n)
        if not x or x["dossier"] in deja:
            continue
        ok, pourquoi = porte_ouverte(x["dossier"])
        fautes = ([] if ok else [f"board : {pourquoi}"]) + fautes_legende(lire(Path(x["dossier"]) / "slides.json", {}).get("legende", ""))
        if fautes:
            refus.append(f"{n} ({Path(x['dossier']).name}) : " + " ; ".join(fautes))
            continue
        nouveaux.append({"dossier": x["dossier"], "style": x["style"], "statut": "en_file",
                         **({"pas_avant": pas_avant[str(n)]} if str(n) in pas_avant else {})})
    ecrire(FILE, refaire(f, nouveaux, rg))
    for r in refus:
        print("REFUSÉ", r)
    cmd_etat(a)
    return 1 if refus else 0


def cmd_retirer(a):
    rev = {x["n"]: x["dossier"] for x in lire(REVUE, [])}
    hors = {rev[int(v)] for v in a.numeros.split(",") if int(v) in rev}
    rg, f = reglages(), lire(FILE, [])
    ecrire(FILE, refaire([x for x in f if x["dossier"] not in hors or x.get("statut") != "en_file"], [], rg))
    cmd_etat(a)


def cmd_etat(_a=None):
    for x in lire(FILE, []):
        print(f"{x.get('date', '?')}  {x['style']:<13} {x['statut']:<9} {x['dossier']}")


def jpeg(src, dest):
    """PNG vers JPEG (Instagram refuse le PNG par API). Sans ffmpeg : copie telle quelle, avec un avertissement."""
    if src.suffix.lower() == ".jpg":
        shutil.copyfile(src, dest.with_suffix(".jpg"))
        return dest.with_suffix(".jpg")
    if shutil.which("ffmpeg"):
        r = subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(src), "-q:v", "2", str(dest.with_suffix(".jpg"))], capture_output=True, text=True)
        if r.returncode == 0:
            return dest.with_suffix(".jpg")
    print(f"ffmpeg absent ou en échec : {src.name} reste en PNG", file=sys.stderr)
    shutil.copyfile(src, dest.with_suffix(".png"))
    return dest.with_suffix(".png")


def sans_appel(leg):
    return "\n".join(l for l in leg.splitlines() if not APPEL.search(l)).strip()


def cmd_du_jour(a):
    rg, f = reglages(), lire(FILE, [])
    jour = a.date or date.today().isoformat()
    x = next((y for y in f if y.get("date") == jour and y["statut"] == "en_file"), None)
    if not x:
        print(f"aucun carrousel prévu le {jour}")
        return 0
    src = Path(x["dossier"])
    ok, pourquoi = porte_ouverte(src)  # le texte a pu bouger depuis l'entrée dans la file
    spec = lire(src / "slides.json", {})
    fautes = ([] if ok else [f"board : {pourquoi}"]) + fautes_legende(spec.get("legende", ""))
    if fautes:
        print("REFUSÉ :", " ; ".join(fautes))
        return 1
    d = PUB / f"{jour}-{src.name}"
    d.mkdir(parents=True, exist_ok=True)
    imgs = [jpeg(p, d / f"slide-{k:02d}") for k, p in enumerate(images(src), 1)]
    appel_fin = bool(spec.get("slides")) and bool(APPEL.search(json.dumps(spec["slides"][-1], ensure_ascii=False)))
    entrees = []
    for res, r in rg["reseaux"].items():
        sel = imgs if r.get("mot_cle") or not appel_fin else imgs[:-1]  # « écris MOT » n'est vrai que là où le message privé répond
        mx = r.get("max", 10)
        if len(sel) > mx:
            sel = sel[:mx - 1] + sel[-1:] if mx > 1 and r.get("mot_cle") else sel[:mx]  # on garde l'appel final
        entrees.append({"reseau": res, "texte": spec["legende"] if r.get("mot_cle") else sans_appel(spec["legende"]),
                        "medias": [p.as_posix() for p in sel], "date": f"{jour}T{rg['heure']}", "source": src.as_posix(),
                        "board": (src / "board.md").as_posix(), **({"voie": r["voie"]} if r.get("voie") else {})})
    if a.a_blanc:
        print(json.dumps(entrees, ensure_ascii=False, indent=1))
        return 0
    cible = FILE_PUB / f"{jour}.json"
    deja = lire(cible, [])
    vus = {(e.get("source"), e.get("reseau")) for e in deja}
    ecrire(cible, deja + [e for e in entrees if (e["source"], e["reseau"]) not in vus])
    x["statut"], x["publication"] = "programme", d.as_posix()
    ecrire(FILE, f)
    print(f"{src.name} : {len(entrees)} réseau(x) dans {cible}")
    return 0


def _png(f):
    import struct, zlib
    bloc = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    Path(f).write_bytes(b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", 8, 10, 8, 2, 0, 0, 0))
                        + bloc(b"IDAT", zlib.compress(b"".join(b"\x00" + b"\x50\x60\x70" * 8 for _ in range(10)))) + bloc(b"IEND", b""))


def auto_test():
    ici = Path.cwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        try:
            leg = "Ton potager boit trop.\nÉcris POTAGER en commentaire et je t'envoie le plan.\n\n#potager #jardin #semis"
            for nom, style, n, mots in (("a-uni", "uni", 3, False), ("b-uni", "uni", 3, False), ("c-conv", "edito", 12, True),
                                        ("d-split", "split", 3, False)):
                d = O / nom
                (d / "png").mkdir(parents=True)
                slides = [{"titre": f"Slide {k}"} for k in range(1, n)] + [{"titre": "Fin", "lien": "Écris *POTAGER* en commentaire"}]
                if mots:
                    slides[0]["messages"] = [{"de": "autre", "texte": "Bonjour"}]
                ecrire(d / "slides.json", {"style": style, "legende": leg, "slides": slides})
                for k in range(1, n + 1):
                    _png(d / "png" / f"slide-{k:02d}.png")
                (d / "board.md").write_text("# Board\n## Verdict : VERT\n", encoding="utf-8")
            (O / "d-split" / "board.md").write_text("## Verdict : À TRANCHER\n", encoding="utf-8")
            cmd_revue()
            rev = lire(REVUE, [])
            assert len(rev) == 4 and rev[2]["style"] == "conversation"
            assert "Copier ma réponse" in (REVUE.parent / "index.html").read_text(encoding="utf-8")
            ns = argparse.Namespace
            assert cmd_ajouter(ns(numeros="1,2,3,4", pas_avant="")) == 1  # le 4 n'a pas de verdict VERT
            f = lire(FILE, [])
            assert [x["style"] for x in f] == ["uni", "conversation", "uni"], [x["style"] for x in f]
            assert len({x["date"] for x in f}) == 3, "un carrousel par jour"
            assert dater([{"dossier": "z", "statut": "en_file", "pas_avant": "2030-01-05"}], "13:30", datetime(2030, 1, 1, 9))[0]["date"] == "2030-01-05"
            assert dater([{"dossier": "z", "statut": "en_file"}], "13:30", datetime(2030, 1, 1, 15))[0]["date"] == "2030-01-02"
            assert fautes_legende("Glisse pour voir " + chr(0x2014) + " ok") and not fautes_legende(leg)
            reg = lire(REGLAGES, {})
            reg["reseaux"].update({"linkedin": {"max": 10, "mot_cle": False}, "bluesky": {"max": 4, "mot_cle": False},
                                   "tiktok": {"max": 35, "mot_cle": False, "voie": "navigateur"}})
            ecrire(REGLAGES, reg)
            conv = next(x for x in f if x["style"] == "conversation")
            assert cmd_du_jour(ns(date=conv["date"], a_blanc=False)) == 0
            e = {x["reseau"]: x for x in lire(FILE_PUB / f"{conv['date']}.json", [])}
            assert len(e["instagram"]["medias"]) == 10 and e["instagram"]["medias"][-1].endswith(("slide-12.jpg", "slide-12.png")), "appel final gardé"
            assert len(e["linkedin"]["medias"]) == 10 and not any(m.endswith(("slide-12.jpg", "slide-12.png")) for m in e["linkedin"]["medias"])
            assert len(e["bluesky"]["medias"]) == 4 and "POTAGER" not in e["bluesky"]["texte"] and "POTAGER" in e["facebook"]["texte"]
            assert e["tiktok"]["voie"] == "navigateur"
            assert cmd_du_jour(ns(date=conv["date"], a_blanc=False)) == 0  # déjà programmé : rien de plus
            assert len(lire(FILE_PUB / f"{conv['date']}.json", [])) == 5
            cmd_revue()
            assert all(x["dossier"] != conv["dossier"] for x in lire(REVUE, [])), "un carrousel programmé sort de la revue"
        finally:
            os.chdir(ici)
    print("AUTO-TEST OK")
    return 0


def main():
    if sys.argv[1:] == ["--test"]:
        return auto_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("revue")
    s = sub.add_parser("ajouter"); s.add_argument("numeros"); s.add_argument("--pas-avant", default="")
    s = sub.add_parser("retirer"); s.add_argument("numeros")
    sub.add_parser("etat")
    s = sub.add_parser("du-jour"); s.add_argument("--date"); s.add_argument("--a-blanc", action="store_true")
    a = ap.parse_args()
    return {"revue": cmd_revue, "ajouter": cmd_ajouter, "retirer": cmd_retirer, "etat": cmd_etat, "du-jour": cmd_du_jour}[a.cmd](a) or 0


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
