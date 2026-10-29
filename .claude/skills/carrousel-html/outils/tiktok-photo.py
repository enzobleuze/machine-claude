"""tiktok-photo.py : publie un carrousel sur TikTok en mode photo, par TikTok Studio dans un navigateur piloté (option).

Pourquoi : des outils de publication multi-réseaux refusent le carrousel TikTok par API (« needs a video »).
TikTok Studio web accepte des photos (35 au plus). Le script fait ce qu'une personne ferait : onglet Photos, images,
titre, description, un son calme pris dans les suggestions, publication, puis il vérifie que le post apparaît.
Profil de navigateur dédié (~/.tiktok-profil-carrousels) : la personne s'y connecte une fois (--setup, code QR).

Besoin : pip install playwright, puis Google Chrome installé (le script utilise le Chrome du système).
  python outils/tiktok-photo.py --setup                                  fenêtre visible, connexion une seule fois
  python outils/tiktok-photo.py --title "..." --text "..." --image a.jpg --image b.jpg [--dry-run] [--headed] [--contenu-ia]
  python outils/tiktok-photo.py --test                                   hors ligne, sans navigateur
--dry-run : tout est rempli (son compris) puis le brouillon est abandonné, rien n'est publié.
--contenu-ia : coche « contenu généré par IA » (images générées) ; refuse de publier si la case est introuvable.
Sortie : une ligne JSON {"ok": true/false, ...}. Code 0 si ok, 1 sinon.
Testé sur l'interface anglaise de TikTok Studio. Les libellés français probables sont dans LIBELLES : si un bouton
n'est pas trouvé, lance avec --headed --dry-run, regarde la capture du dossier de debug et ajoute le libellé vu.
"""
from __future__ import annotations

import argparse, json, random, re, sys, time
from pathlib import Path

PROFIL = Path.home() / ".tiktok-profil-carrousels"
UPLOAD = "https://www.tiktok.com/tiktokstudio/upload?from=webapp&tab=photo"
CONTENU = "https://www.tiktok.com/tiktokstudio/content"
DEBUG = Path("outputs/carrousels/logs/tiktok")
HISTORIQUE = Path("outputs/carrousels/sons-tiktok.json")
SANS_REPETER = 15  # un son ne revient pas avant ce nombre de carrousels
LIBELLES = {"son": r"Add sound|Ajouter un son", "utiliser": r"Use|Utiliser", "favoris": r"Favorites|Favoris", "pour_toi": r"For You|Pour toi",
            "publier": r"Post|Publier", "abandonner": r"Discard|Abandonner|Supprimer",
            "abandonner2": r"Discard edits|Abandonner les modifications|Supprimer les modifications",
            "titre": r"catchy title|titre accrocheur", "ia": r"AI-generated content|Contenu généré par (?:l')?IA"}
CALME = re.compile(r"calm|quiet|relax|soft|gentle|peace|piano|breath|slow|dream|reflect|still|lofi|lo-fi|ambient|"
                   r"serene|tender|lullaby|rain|warm|hope|morning|doux|calme|paisible", re.I)
ORIGINAL = re.compile(r"^(original sound|son original|suono originale|sonido original|som original|originalton)", re.I)
INTERDIT = re.compile(r"porn|sex|fuck|shit|bitch|nsfw|drug|weed|kill|suicide", re.I)


def choisir_son(titres: list[str], deja: list[str], hasard=random.Random()) -> int | None:
    """Indice du son : au hasard parmi ceux pas utilisés récemment, les titres calmes d'abord. Jamais un « son original »
    d'un inconnu (droits et qualité incertains) ni un titre grossier. None si rien ne passe."""
    ok = [i for i, t in enumerate(titres) if t and not ORIGINAL.match(t) and not INTERDIT.search(t) and t not in deja]
    calmes = [i for i in ok if CALME.search(titres[i])]
    return hasard.choice(calmes or ok) if ok else None


def capture(page, tag: str) -> str:
    DEBUG.mkdir(parents=True, exist_ok=True)
    f = DEBUG / f"{time.strftime('%Y%m%d-%H%M%S')}-{tag}.png"
    try:
        page.screenshot(path=str(f))
    except Exception:
        pass
    return str(f)


def bouton(page, cle: str):
    return page.locator("button").filter(has_text=re.compile(rf"^\s*(?:{LIBELLES[cle]})\s*$")).first


def ajouter_son(page, dry_run: bool) -> str | None:
    bouton(page, "son").click()
    items = page.locator(".MusicPanelMusicItem__wrap")
    items.first.wait_for(state="visible", timeout=20000)
    page.wait_for_timeout(1500)
    lire = lambda: [t.split("\n")[0].strip() for t in items.all_inner_texts()]
    onglets = {"suggestions": lire()}
    try:
        page.get_by_text(re.compile(rf"^(?:{LIBELLES['favoris']})$")).first.click()
        page.wait_for_timeout(3000)
        onglets["favoris"] = lire()
    except Exception:
        pass
    try:
        deja = json.loads(HISTORIQUE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        deja = []
    tous = [(o, t) for o, ts in onglets.items() for t in ts]
    i = choisir_son([t for _, t in tous], deja[-SANS_REPETER:])
    if i is None:
        page.keyboard.press("Escape")
        return None
    onglet, titre = tous[i]
    page.get_by_text(re.compile(rf"^(?:{LIBELLES['pour_toi' if onglet == 'suggestions' else 'favoris']})$")).first.click()
    page.wait_for_timeout(3000)
    items.nth(lire().index(titre)).locator("button").filter(has_text=re.compile(LIBELLES["utiliser"])).first.click()
    page.wait_for_timeout(2000)
    if not dry_run:
        HISTORIQUE.parent.mkdir(parents=True, exist_ok=True)
        HISTORIQUE.write_text(json.dumps((deja + [titre])[-50:], ensure_ascii=False, indent=1), encoding="utf-8")
    return titre


def ecrire_description(page, texte: str):
    """Les hashtags ouvrent une liste de suggestions : Échap la ferme après chacun."""
    ed = page.locator(".public-DraftEditor-content[contenteditable=true]").first
    ed.click()
    for morceau in re.split(r"(#\w+)", texte):
        if not morceau or morceau == " ":
            continue
        page.keyboard.type(morceau + (" " if morceau.startswith("#") else ""), delay=15)
        if morceau.startswith("#"):
            page.wait_for_timeout(800)
            page.keyboard.press("Escape")


def connecte(page) -> bool:
    page.goto(UPLOAD, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_timeout(4000)
    return "login" not in page.url and page.locator("input[type=file]").count() > 0


def run(title, text, images, dry_run, headed, setup, contenu_ia) -> dict:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(str(PROFIL), channel="chrome", headless=not (headed or setup),
                                                   viewport={"width": 1440, "height": 900},
                                                   args=["--disable-blink-features=AutomationControlled"])
        try:
            page = ctx.pages[0] if ctx.pages else ctx.new_page()
            if setup:
                page.goto("https://www.tiktok.com/login", wait_until="domcontentloaded")
                for _ in range(200):  # 10 minutes pour se connecter (code QR du téléphone, le plus simple)
                    page.wait_for_timeout(3000)
                    if "login" not in page.url:
                        break
                return {"ok": connecte(page), "setup": True}
            if not connecte(page):
                return {"ok": False, "erreur": "profil non connecté : lance --setup", "capture": capture(page, "connexion")}
            sondes = [s for s in (text.strip()[:40], title.strip()[:40]) if s]  # TikTok Studio liste les posts par leur description
            present = lambda: any(s in page.inner_text("body") for s in sondes)
            if not dry_run:  # anti-doublon : une relance après un échec de vérification ne reposte pas
                page.goto(CONTENU, wait_until="domcontentloaded", timeout=60000)
                page.wait_for_timeout(5000)
                if present():
                    return {"ok": True, "verifie": "déjà présent, pas reposté"}
                connecte(page)
            page.locator("input[type=file]").first.set_input_files(images)
            champ = page.get_by_placeholder(re.compile(LIBELLES["titre"], re.I)).first
            champ.wait_for(state="visible", timeout=60000)
            page.wait_for_timeout(3000)
            m = re.search(r"(\d+) (?:photos?|images?)", page.inner_text("body"))
            if not m or int(m.group(1)) != len(images):
                return {"ok": False, "erreur": f"photos chargées : {m.group(1) if m else 0} sur {len(images)}", "capture": capture(page, "images")}
            champ.fill(title[:90])
            ecrire_description(page, text)
            try:
                son = ajouter_son(page, dry_run)
            except Exception as e:  # le son est un plus : on publie sans
                son = None
                page.keyboard.press("Escape")
                capture(page, f"son-{type(e).__name__}")
            if contenu_ia:
                case = page.get_by_text(re.compile(LIBELLES["ia"], re.I)).first
                if not case.count():
                    return {"ok": False, "erreur": "case « contenu généré par IA » introuvable : rien publié", "capture": capture(page, "ia")}
                case.click()
            if dry_run:
                f = capture(page, "a-blanc")
                bouton(page, "abandonner").click()
                page.wait_for_timeout(1500)
                bouton(page, "abandonner2").click()
                return {"ok": True, "a_blanc": True, "images": len(images), "son": son, "capture": f}
            bouton(page, "publier").click()
            for _ in range(40):
                page.wait_for_timeout(1500)
                if "/content" in page.url:
                    break
            for _ in range(6):  # le post apparaît dans la liste avec du retard : recharger plusieurs fois avant de conclure
                page.wait_for_timeout(4000)
                if "/content" in page.url and present():
                    return {"ok": True, "verifie": "post en tête de TikTok Studio", "images": len(images), "son": son}
                page.wait_for_timeout(16000)
                page.goto(CONTENU, wait_until="domcontentloaded", timeout=60000)
            return {"ok": False, "erreur": "publié mais introuvable dans TikTok Studio : vérifie à la main", "capture": capture(page, "verif"), "son": son}
        finally:
            ctx.close()


def auto_test():
    assert choisir_son(["Barn Hook", "original sound - x", "Calm Reflections"], []) == 2
    assert choisir_son(["Calm Reflections", "Barn Hook"], ["Calm Reflections"]) == 1
    assert choisir_son(["son original", "Porn Factory"], []) is None and choisir_son([], []) is None
    assert re.fullmatch(LIBELLES["publier"], "Publier") and re.fullmatch(LIBELLES["son"], "Add sound")
    assert main(["--title", "x"]) == 1  # sans image : refus avant d'ouvrir le navigateur
    print("AUTO-TEST OK")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Carrousel TikTok en mode photo par TikTok Studio web.")
    ap.add_argument("--title", default="")
    ap.add_argument("--text", default="")
    ap.add_argument("--image", action="append", default=[], help="photo JPEG, à répéter (35 au plus)")
    for opt in ("--dry-run", "--headed", "--setup", "--contenu-ia", "--test"):
        ap.add_argument(opt, action="store_true")
    a = ap.parse_args(argv)
    if a.test:
        return auto_test()
    if not a.setup and (not a.image or not a.title.strip()):
        print(json.dumps({"ok": False, "erreur": "--title et au moins une --image demandés"}, ensure_ascii=False))
        return 1
    try:
        res = run(a.title, a.text, [str(Path(i).resolve()) for i in a.image[:35]], a.dry_run, a.headed, a.setup, a.contenu_ia)
    except Exception as e:  # noqa: BLE001
        res = {"ok": False, "erreur": f"exception : {e}"[:400]}
    print(json.dumps(res, ensure_ascii=False))
    return 0 if res.get("ok") else 1


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
