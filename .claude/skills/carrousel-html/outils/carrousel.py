"""carrousel.py : un carrousel décrit en JSON devient des PNG (1080x1350 par défaut), en local, sans IA d'image.

Comment : chaque slide devient une page HTML, puis Chrome, Chromium ou Edge en mode sans fenêtre
en prend une capture. Aucune bibliothèque Python à installer. Coût : zéro crédit.

  python carrousel.py rendre slides.json [-o dossier]
  python carrousel.py exemple > slides.json        (un JSON de départ à remplir)
  python carrousel.py --test                       (auto-test : rend 2 slides et vérifie la taille des PNG)

Navigateur : variable d'environnement NAVIGATEUR si tu veux forcer un chemin, sinon recherche automatique
(Windows : Chrome ou Edge ; Mac : Google Chrome.app ; Linux : chromium ou google-chrome).

Le JSON :
{
  "theme": {"fond": "#141414", "texte": "#F4EFE6", "accent": "#C9A227", "police": "Georgia, serif",
            "police_texte": "Arial, sans-serif", "pied": "@toncompte"},
  "taille": [1080, 1350],
  "max_mots": 35,
  "slides": [
    {"titre": "Une scène qui *pique*", "texte": "Deux phrases au plus.\\nUne idée par ligne.", "image": "img/1.jpg"},
    {"titre": "Ce que tu fais ce soir", "coches": ["Action 1", "Action 2"]},
    {"titre": "Garde ce post", "appel": "Écris MOT en commentaire"}
  ]
}
Dans les textes : *mot* = mot en couleur d'accent, \\n = retour à la ligne. Les chemins d'images sont relatifs au JSON.
Refus avant rendu : slide sans titre ni texte, slide au-delà de max_mots, image introuvable.
"""
import argparse, html, json, os, re, shutil, struct, subprocess, sys, tempfile
from pathlib import Path

EXEMPLE = {
    "theme": {"fond": "#141414", "texte": "#F4EFE6", "accent": "#C9A227", "police": "Georgia, serif",
              "police_texte": "Arial, sans-serif", "pied": "@toncompte"},
    "taille": [1080, 1350],
    "max_mots": 35,
    "slides": [
        {"titre": "Le moment où tout *bascule*", "texte": "Une scène précise que ton client reconnaît.\nPas un résumé de son problème."},
        {"titre": "Ce que tu fais ce soir", "coches": ["Une action simple", "Une deuxième action"]},
        {"titre": "Garde ce post", "appel": "Écris MOT en commentaire"},
    ],
}


def navigateur():
    if os.environ.get("NAVIGATEUR"):
        return os.environ["NAVIGATEUR"]
    for nom in ("chrome", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge"):
        if shutil.which(nom):
            return shutil.which(nom)
    for chemin in (r"C:\Program Files\Google\Chrome\Application\chrome.exe",
                   r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
                   r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
                   r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
                   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                   "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"):
        if os.path.exists(chemin):
            return chemin
    raise SystemExit("Aucun navigateur Chrome, Chromium ou Edge trouvé. Installe-en un ou pose NAVIGATEUR=<chemin>.")


def marque(t):
    t = html.escape(t or "")
    t = re.sub(r"\*(.+?)\*", r'<span class="a">\1</span>', t)
    return t.replace("\\n", "<br>").replace("\n", "<br>")


def mots(s):
    return len(re.findall(r"\w+", " ".join([s.get("titre", ""), s.get("texte", ""), s.get("appel", "")] + s.get("coches", []))))


def verifier(donnees, base):
    erreurs = []
    lim = donnees.get("max_mots", 35)
    for i, s in enumerate(donnees.get("slides", []), 1):
        if not (s.get("titre") or s.get("texte")):
            erreurs.append(f"slide {i} : ni titre ni texte")
        if mots(s) > lim:
            erreurs.append(f"slide {i} : {mots(s)} mots, plus que {lim}. Coupe ou découpe en deux slides.")
        if s.get("image") and not (base / s["image"]).exists():
            erreurs.append(f"slide {i} : image introuvable ({s['image']})")
    if not donnees.get("slides"):
        erreurs.append("aucune slide")
    return erreurs


def page(s, i, n, th, w, h, base):
    fond_img = ""
    if s.get("image"):
        uri = (base / s["image"]).resolve().as_uri()
        fond_img = f'<div class="img" style="background-image:url(\'{uri}\')"></div><div class="voile"></div>'
    coches = "".join(f"<li>{marque(c)}</li>" for c in s.get("coches", []))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
*{{margin:0;padding:0;box-sizing:border-box}}
html,body{{width:{w}px;height:{h}px;overflow:hidden;background:{th['fond']};color:{th['texte']}}}
.img{{position:absolute;inset:0;background-size:cover;background-position:center}}
.voile{{position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.25),rgba(0,0,0,.75))}}
.z{{position:absolute;left:{w*0.08:.0f}px;right:{w*0.08:.0f}px;top:{h*0.12:.0f}px;bottom:{h*0.12:.0f}px;display:flex;flex-direction:column;justify-content:center;gap:{h*0.03:.0f}px}}
h1{{font-family:{th['police']};font-size:{w*0.085:.0f}px;line-height:1.12;font-weight:700}}
p{{font-family:{th.get('police_texte', th['police'])};font-size:{w*0.045:.0f}px;line-height:1.4}}
ul{{list-style:none;font-family:{th.get('police_texte', th['police'])};font-size:{w*0.045:.0f}px;line-height:1.5}}
li::before{{content:"\\2713  ";color:{th['accent']}}}
.a{{color:{th['accent']}}}
.appel{{border:3px solid {th['accent']};border-radius:18px;padding:{w*0.03:.0f}px;font-family:{th.get('police_texte', th['police'])};font-size:{w*0.05:.0f}px;text-align:center}}
.pied{{position:absolute;bottom:{h*0.04:.0f}px;left:{w*0.08:.0f}px;right:{w*0.08:.0f}px;display:flex;justify-content:space-between;font-family:monospace;font-size:{w*0.028:.0f}px;opacity:.7}}
</style></head><body>{fond_img}<div class="z">
{f'<h1>{marque(s.get("titre"))}</h1>' if s.get("titre") else ''}
{f'<p>{marque(s.get("texte"))}</p>' if s.get("texte") else ''}
{f'<ul>{coches}</ul>' if coches else ''}
{f'<div class="appel">{marque(s.get("appel"))}</div>' if s.get("appel") else ''}
</div><div class="pied"><span>{html.escape(th.get('pied', ''))}</span><span>{i}/{n}</span></div></body></html>"""


def taille_png(f):
    with open(f, "rb") as fh:
        tete = fh.read(24)
    if tete[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("pas un PNG")
    return struct.unpack(">II", tete[16:24])


def rendre(chemin_json, sortie=None):
    chemin_json = Path(chemin_json)
    donnees = json.loads(chemin_json.read_text(encoding="utf-8"))
    base = chemin_json.parent
    erreurs = verifier(donnees, base)
    if erreurs:
        raise SystemExit("Refusé :\n- " + "\n- ".join(erreurs))
    th = {**EXEMPLE["theme"], **donnees.get("theme", {})}
    w, h = donnees.get("taille", [1080, 1350])
    sortie = Path(sortie or base / "png")
    sortie.mkdir(parents=True, exist_ok=True)
    nav = navigateur()
    slides = donnees["slides"]
    faits = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, s in enumerate(slides, 1):
            f_html = Path(tmp) / f"slide-{i:02d}.html"
            f_html.write_text(page(s, i, len(slides), th, w, h, base), encoding="utf-8")
            f_png = (sortie / f"slide-{i:02d}.png").resolve()
            profil = Path(tmp) / "profil"
            cmd = [nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                   f"--user-data-dir={profil}", f"--window-size={w},{h}", "--force-device-scale-factor=1",
                   f"--screenshot={f_png}", f_html.resolve().as_uri()]
            r = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            if not f_png.exists():
                raise SystemExit(f"Le navigateur n'a pas rendu la slide {i}.\n{r.stderr[-600:]}")
            if taille_png(f_png) != (w, h):
                raise SystemExit(f"Slide {i} rendue en {taille_png(f_png)}, attendu {(w, h)}.")
            faits.append(f_png)
    print(f"{len(faits)} slides rendues dans {sortie}")
    return faits


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        j = Path(tmp) / "slides.json"
        d = json.loads(json.dumps(EXEMPLE))
        j.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        faits = rendre(j, Path(tmp) / "png")
        assert len(faits) == 3 and all(taille_png(f) == (1080, 1350) for f in faits)
        d["slides"].append({"titre": "trop long " * 30})
        j.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
        try:
            rendre(j)
            raise AssertionError("la slide trop longue aurait dû être refusée")
        except SystemExit as e:
            assert "mots" in str(e)
    print("AUTO-TEST OK")


def main():
    p = argparse.ArgumentParser(description="Carrousel JSON -> PNG, rendu local par navigateur sans fenêtre.")
    p.add_argument("commande", nargs="?", choices=["rendre", "exemple"])
    p.add_argument("json", nargs="?")
    p.add_argument("-o", "--sortie")
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        return auto_test()
    if a.commande == "exemple":
        print(json.dumps(EXEMPLE, ensure_ascii=False, indent=2))
    elif a.commande == "rendre" and a.json:
        rendre(a.json, a.sortie)
    else:
        p.print_help()


if __name__ == "__main__":
    main()
