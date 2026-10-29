"""carrousel.py : un carrousel décrit en JSON devient des PNG 1080x1350, rendus en local par le navigateur, aux couleurs
et aux polices de la charte (bibliotheque/marque/charte.css et charte-jetons.json). Aucune bibliothèque Python à
installer, aucun crédit d'image. Sans charte, la charte « simple » sert en attendant.

Cinq styles, un par carrousel :
  podcast : une image de vidéo par slide, voile sombre, gros texte en capitales ; la couverture porte un mot géant
            rempli par la photo. Pour une idée forte dite face caméra.
  uni     : texte sur fond uni, gros titre, lignes aérées, carte ou tableau au besoin. Le plus rapide à produire.
  edito   : titre centré, image au milieu, phrase, liste à coches, bulle de l'appel final. Le champ "messages" en
            fait une conversation façon messagerie. Une seule slide (taille 1080x1080 ou 1080x1350) = une pub statique.
  reel    : captures d'une vidéo courte en plein cadre, texte en boîtes façon Instagram, carte « à faire » en fin.
  split   : deux captures d'une vidéo longue empilées, chacune avec la phrase dite à cet instant en sous-titre.

  python carrousel.py exemple <style> > slides.json
  python carrousel.py rendre slides.json [-o dossier] [--charte bibliotheque/marque/charte-jetons.json]
  python carrousel.py images video.mp4 --at 30,150.5 -o dossier/img          (image la plus nette autour de chaque instant)
  python carrousel.py reel video.mp4 --srt video.srt --debut 81 --fin 117 -o dossier    (brouillon slides.json + img/)
  python carrousel.py split video.mp4 --srt video.srt --debut 96 --fin 141 -o dossier   (brouillon, 2 phrases par slide)
  python carrousel.py --test

Le JSON : {"style": "...", "pied": "@toncompte", "taille": [1080, 1350], "max_mots": 35, "slides": [...]}
Champs des slides par style : voir EXEMPLES plus bas (python carrousel.py exemple <style>). Chemins d'images relatifs
au JSON. Dans les textes : *mot* = mot mis en valeur (italique, ou couleur d'accent selon le style), \\n = à la ligne.

Refus avant rendu : style inconnu, slide vide, trop de mots (35 par défaut, 22 en style reel), image introuvable,
deux boîtes fortes sur une slide, « glisse » ou « swipe », « situation type », « mise en scène », tiret long.
Refus au rendu : texte qui déborde de sa zone, texte hors de la zone sûre (60 px), logo qui touche un texte,
contraste sous 4,5 (3 pour un texte de 24 px et plus) sur un fond uni ou une boîte. Le texte posé sur une photo
n'est pas mesuré : il reste sur un voile sombre (champ "voile", 0,7 par défaut).
Navigateur : variable NAVIGATEUR pour forcer un chemin, sinon Chrome, Chromium ou Edge trouvés seuls.
Vidéo : ffmpeg et ffprobe sur le PATH. Sous-titres : un fichier .srt ou .vtt (faster-whisper, ou ceux de YouTube).
"""
import argparse, html, json, os, re, shutil, struct, subprocess, sys, tempfile, zlib
from pathlib import Path

STYLES = ("podcast", "uni", "edito", "reel", "split")
SAFE = 60
CLES_TEXTE = {"titre", "texte", "mot", "ligne", "italique", "lignes", "lien", "sous_titre", "phrase", "bulle", "coches",
              "messages", "boites", "devoir", "items", "carte", "tableau", "note", "haut", "bas"}
# « Glisse pour voir », « Swipe », « Fais défiler » : refusés ; « le vélo glisse sur la route » passe
GLISSER = re.compile(r"(?i)(?:^\s*(?:glisse|swipe|fais défiler|fais glisser)\b|\b(?:glisse|swipe)\b(?=\s*(?:pour|vers|[.!?:>)]|$)))")
INTERDITS = re.compile(r"(?i)situation type|mise en scène")

# Charte « simple » de charte.py (repli quand bibliotheque/marque/ n'existe pas encore ; --test vérifie l'égalité)
SIMPLE_JETONS = {
    "nom": "Simple", "principal": "clair",
    "clair": {"fond": "#fafaf8", "surface": "#f1f1ef", "surface_2": "#e8e8e6", "ligne": "#d7d7d5", "texte": "#1d1d1b",
              "texte_doux": "#6a6a68", "accent": "#2f5bd3", "accent_texte": "#ffffff", "accent_2": "#284289",
              "ok": "#2e8b57", "alerte": "#c77f1c", "erreur": "#c8374d"},
    "sombre": {"fond": "#141413", "surface": "#1d1d1c", "surface_2": "#262625", "ligne": "#393938", "texte": "#fafaf8",
               "texte_doux": "#aaaaa8", "accent": "#4068d7", "accent_texte": "#ffffff", "accent_2": "#8aa2e4",
               "ok": "#2e8b57", "alerte": "#d98a1f", "erreur": "#c8374d"},
    "polices": {"titres": "Inter", "texte": "Inter"}, "rayon": 10, "logo": "", "mots": ["net", "lisible", "sobre"]}
_P = "'Inter', system-ui, 'Segoe UI', sans-serif"


def _vars(t, schema):
    return (";".join(f"--{k.replace('_', '-')}:{v}" for k, v in SIMPLE_JETONS[t].items())
            + f";--police-titres:{_P};--police-texte:{_P};--rayon:10px;color-scheme:{schema}")


SIMPLE_CSS = ('@import url("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap");\n'
              f":root{{{_vars('clair', 'light')}}}\n[data-theme=\"clair\"]{{{_vars('clair', 'light')}}}\n"
              f"[data-theme=\"sombre\"]{{{_vars('sombre', 'dark')}}}\n")

EXEMPLES = {
    "uni": {"style": "uni", "pied": "@toncompte", "slides": [
        {"titre": "Tes tomates *craquent* au soleil ?", "lignes": ["L'arrosage du soir arrive trop tard.",
                                                                    "La terre a déjà séché toute la journée."]},
        {"carte": {"titre": "Ce que tu changes demain", "sous_titre": "Une seule habitude",
                   "tableau": [["Arroser le soir", "Le matin"], ["Un peu chaque jour", "Beaucoup, deux fois"]]}},
        {"titre": "Garde ce post pour l'été.", "lien": "Écris *POTAGER* en commentaire", "milieu": True}]},
    "edito": {"style": "edito", "slides": [
        {"titre": "Tes semis *jaunissent* ?", "messages": [
            {"de": "autre", "texte": "Mes semis jaunissent, j'ai tout essayé."},
            {"de": "moi", "texte": "Tu les arroses tous les jours ?"},
            {"de": "autre", "texte": "Oui, matin et soir."}]},
        {"titre": "Ce soir, trois gestes", "coches": ["Touche la terre", "Arrose si elle est sèche", "Sinon, attends"]},
        {"phrase": "La terre sèche entre deux arrosages.", "bulle": "Écris *SEMIS* en commentaire"}]},
    "podcast": {"style": "podcast", "pied": "@toncompte", "slides": [
        {"type": "couverture", "image": "img/01.jpg", "mot": "Patience", "ligne": "Ce que le potager t'apprend",
         "italique": "avant la première récolte"},
        {"image": "img/02.jpg", "texte": "On veut tout récolter en juin.\n*La terre a son rythme.*", "cx": 0.5, "cy": 0.2}]},
    "reel": {"style": "reel", "boite": "claire", "slides": [
        {"image": "img/01.jpg", "y": 0.1, "boites": [{"texte": "Tu arroses trop."},
                                                      {"texte": "Et tes racines restent en surface.", "forte": True, "taille": "m"}]},
        {"image": "img/02.jpg", "devoir": {"titre": "Ta semaine", "items": ["Arrose le matin", "Paille le sol"]}}]},
    "split": {"style": "split", "slides": [
        {"haut": {"image": "img/01.jpg", "texte": "J'arrosais tous les soirs.\nEt rien ne poussait."},
         "bas": {"image": "img/02.jpg", "texte": "Puis j'ai touché la terre *avant* d'arroser."}}]},
}

BASE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--fond)}
.slide{position:relative;overflow:hidden;background:var(--fond);color:var(--texte);font-family:var(--police-texte)}
.slide em{font-style:italic}
.nowrap{white-space:nowrap}
.logo{position:absolute;left:60px;top:60px;height:48px;width:auto;z-index:5}
.mini{position:absolute;right:26px;bottom:24px;font:600 15px var(--police-texte);color:var(--texte)}
.fleche{position:absolute;right:72px;bottom:72px;width:104px;color:var(--texte);z-index:6;
  filter:drop-shadow(0 4px 10px color-mix(in srgb,var(--ombre) 45%,transparent))}
.coin{position:absolute;right:0;bottom:0;width:460px;height:460px;pointer-events:none;background:radial-gradient(circle at 82% 82%,
  color-mix(in srgb,var(--ombre) 55%,transparent) 0,color-mix(in srgb,var(--ombre) 28%,transparent) 28%,transparent 62%)}
/* boîte façon Instagram en deux couches : les fonds d'abord, le texte par-dessus (sinon la ligne suivante mange les jambages) */
.bx{position:relative} .bx .fond{color:transparent} .bx .dessus{position:absolute;inset:0;padding:inherit}
"""

CSS = {
    "podcast": """
.st-podcast{--voile-mot:color-mix(in srgb,var(--texte) 55%,transparent)}
.st-podcast .flou{position:absolute;inset:-60px;width:calc(100% + 120px);height:calc(100% + 120px);object-fit:cover;filter:blur(38px) brightness(.62) saturate(.9)}
.st-podcast .photo{position:absolute;left:0;right:0;bottom:0;-webkit-mask-image:linear-gradient(to bottom,transparent 0,var(--fond) 16%);mask-image:linear-gradient(to bottom,transparent 0,var(--fond) 16%)}
.st-podcast .photo img{width:100%;height:100%;object-fit:cover}
.st-podcast .vig{position:absolute;inset:0;background:radial-gradient(ellipse 78% 72% at 50% 60%,transparent 38%,color-mix(in srgb,var(--fond) 88%,transparent) 100%),
  linear-gradient(to bottom,color-mix(in srgb,var(--fond) var(--voile),transparent) 0%,color-mix(in srgb,var(--fond) var(--voile2),transparent) 38%,transparent 58%)}
.st-podcast .zone{position:absolute;left:81px;right:81px;top:160px;max-height:560px;overflow:hidden;text-align:center;padding-bottom:10px;text-wrap:balance}
.st-podcast .zone.gauche{text-align:left;right:300px} .st-podcast .zone.droite{text-align:right;left:300px}
.st-podcast .corps{font:700 51px/65px var(--police-titres);letter-spacing:-.035em;text-transform:uppercase}
.st-podcast .corps em{display:block;letter-spacing:-.04em}
.st-podcast .couv{top:150px;max-height:620px}
.st-podcast .couv h1{font:700 130px/117px var(--police-titres);letter-spacing:-.045em;background-size:cover;background-position:center;
  background-blend-mode:screen;-webkit-background-clip:text;background-clip:text;color:transparent;padding-bottom:12px}
.st-podcast .couv .l{font:700 36px/1 var(--police-titres);letter-spacing:-.025em;text-transform:uppercase;margin-top:34px}
.st-podcast .couv .it{font:italic 700 57px/1.05 var(--police-titres);letter-spacing:-.045em;text-transform:uppercase;margin-top:22px}
""",
    "uni": """
.st-uni .zone{position:absolute;left:70px;right:90px;top:237px;bottom:180px;overflow:hidden}
.st-uni .zone.milieu{top:0;bottom:0;display:flex;flex-direction:column;justify-content:center;left:112px}
.st-uni .titre{font:600 62px/88px var(--police-titres);letter-spacing:-.012em}
.st-uni .ligne{font:400 40px/1.3 var(--police-texte);margin-top:62px}
.st-uni .ligne+.ligne{margin-top:56px}
.st-uni .lien{font:600 62px/88px var(--police-titres);margin-top:88px}
.st-uni .lien em,.st-uni .titre em{color:var(--accent)}
.st-uni .pied{position:absolute;left:71px;bottom:96px;font:500 22px var(--police-texte);letter-spacing:.12em;text-transform:uppercase;color:var(--texte-doux)}
.st-uni .carte{position:absolute;left:66px;right:68px;top:206px;bottom:206px;background:var(--fond);color:var(--texte);border-radius:var(--rayon);
  padding:56px 54px;display:flex;flex-direction:column;overflow:hidden;
  box-shadow:0 14px 12px -10px color-mix(in srgb,var(--ombre) 30%,transparent),0 44px 60px -20px color-mix(in srgb,var(--ombre) 35%,transparent)}
.st-uni .carte .ct{font:700 40px/1.2 var(--police-titres)}
.st-uni .carte .cs{font:400 26px/1.35 var(--police-texte);color:var(--texte-doux);margin-top:14px}
.st-uni .rangs{flex:1;display:flex;flex-direction:column;justify-content:center;gap:34px}
.st-uni .rang{display:flex;align-items:center;gap:26px}
.st-uni .rang .a{flex:1.25;font:italic 500 38px/1.25 var(--police-titres)}
.st-uni .rang .fl{font:500 34px var(--police-texte);color:var(--accent)}
.st-uni .rang .b{flex:.75;font:800 34px/1.2 var(--police-texte);text-transform:uppercase;background:var(--texte);color:var(--fond);
  border-radius:calc(var(--rayon) * .8);padding:14px 18px;text-align:center}
.st-uni .carte .cn{font:500 19px/1.4 var(--police-texte);letter-spacing:.06em;color:var(--texte-doux);text-transform:uppercase;margin-top:auto}
.st-uni .carte img{flex:1;min-height:0;width:100%;object-fit:cover;border-radius:calc(var(--rayon) / 2);margin-top:28px}
""",
    "edito": """
.st-edito .zone{position:absolute;left:96px;right:96px;top:150px;bottom:110px;display:flex;flex-direction:column;align-items:center;
  justify-content:flex-start;text-align:center;overflow:hidden;padding-bottom:24px;text-wrap:balance}
.st-edito .zone.milieu{justify-content:center}
.st-edito .titre{font:400 74px/1.08 var(--police-titres);letter-spacing:-.025em}
.st-edito .titre em{font-weight:500}
.st-edito .media{flex:1 1 0;min-height:0;display:flex;justify-content:center;align-items:center;width:100%;margin:44px 0 40px}
.st-edito .media img{height:100%;max-width:100%;aspect-ratio:var(--ratio);object-fit:cover;object-position:var(--cx) 30%;border-radius:var(--rayon);
  box-shadow:0 12px 14px -8px color-mix(in srgb,var(--ombre) 28%,transparent),0 40px 70px -24px color-mix(in srgb,var(--ombre) 45%,transparent)}
.st-edito .phrase{font:400 52px/1.12 var(--police-titres);letter-spacing:-.02em}
.st-edito .seule{font-size:60px}
.st-edito .sous{font:400 50px/1.15 var(--police-titres);letter-spacing:-.02em;margin-top:96px}
.st-edito .coches{list-style:none;align-self:flex-start;margin:64px 0 0 70px;text-align:left}
.st-edito .coches li{display:flex;align-items:center;gap:26px;font:500 27px/1.2 var(--police-texte);letter-spacing:.22em;text-transform:uppercase;margin-bottom:46px}
.st-edito .coches svg{flex:none;width:40px;height:40px;color:var(--accent)}
.st-edito .bulle{margin-top:auto;max-width:900px;text-align:center;line-height:0;padding:20px 0}
.st-edito .bulle .fond,.st-edito .bulle .t{font:400 50px/62px var(--police-titres);letter-spacing:-.02em;padding:4px 26px 8px;border-radius:22px;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}
.st-edito .bulle .fond{background:var(--texte)} .st-edito .bulle .t{color:var(--fond)}
.st-edito .bulle em{font-weight:600}
.st-edito .conv{flex:1 1 0;min-height:0;width:100%;display:flex;flex-direction:column;justify-content:center;gap:22px;margin:40px 0 20px}
.st-edito .msg{max-width:74%;font:400 40px/1.3 var(--police-texte);letter-spacing:-.01em;padding:22px 30px;border-radius:34px;text-align:left;text-wrap:pretty}
.st-edito .msg.autre{align-self:flex-start;background:var(--surface-2);color:var(--texte);border-bottom-left-radius:8px}
.st-edito .msg.moi{align-self:flex-end;background:var(--accent);color:var(--accent-texte);border-bottom-right-radius:8px}
""",
    "reel": """
.st-reel .plein{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.st-reel .zone{position:absolute;left:66px;right:66px;text-align:center;max-height:560px;overflow:hidden;padding:4px 0;text-wrap:balance}
.st-reel .b{line-height:0;margin-bottom:16px;padding:3px 0 6px}
.st-reel .b .fond,.st-reel .b .t{font:600 58px/74px var(--police-texte);letter-spacing:-.012em;padding:2px 22px 6px;border-radius:14px;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}
.st-reel .b.m .fond,.st-reel .b.m .t{font-size:46px;line-height:59px;border-radius:12px;padding:2px 18px 5px}
.st-reel .b.s .fond,.st-reel .b.s .t{font-size:34px;line-height:44px;border-radius:10px;padding:1px 14px 4px}
.st-reel .b .fond{background:var(--fond)} .st-reel .b .t{color:var(--texte)}
.st-reel .b.forte .fond{background:var(--accent)} .st-reel .b.forte .t{color:var(--accent-texte)}
.st-reel .b em{font-family:var(--police-titres)}
.st-reel .devoir{position:absolute;left:142px;right:137px;background:var(--fond);border-radius:calc(var(--rayon) * 2);padding:40px 44px 34px;
  color:var(--texte);text-align:left;box-shadow:0 10px 30px color-mix(in srgb,var(--ombre) 25%,transparent)}
.st-reel .devoir .dt{font:500 40px/1.25 var(--police-titres);margin-bottom:22px}
.st-reel .devoir mark{background:var(--accent);color:var(--accent-texte);padding:0 6px;-webkit-box-decoration-break:clone;box-decoration-break:clone}
.st-reel .devoir ol{padding-left:40px}
.st-reel .devoir li{font:400 27px/1.35 var(--police-texte);margin-bottom:8px}
""",
    "split": """
.st-split{display:flex;flex-direction:column;gap:4px}
.st-split .moitie{position:relative;flex:1;overflow:hidden}
.st-split .moitie img{position:absolute;inset:0;width:100%;height:100%;object-fit:cover}
.st-split .zone{position:absolute;left:66px;right:66px;bottom:64px;max-height:214px;overflow:hidden;text-align:center;padding:2px 0;text-wrap:balance}
.st-split .cap{line-height:0;padding:3px 0 6px}
.st-split .cap .fond,.st-split .cap .t{font:700 46px/64px var(--police-texte);letter-spacing:-.022em;padding:2px 16px 7px;border-radius:10px;
  -webkit-box-decoration-break:clone;box-decoration-break:clone}
.st-split .cap .fond{background:var(--fond);opacity:.92} .st-split .cap .t{color:var(--texte)}
.st-split .cap em{font-style:normal} .st-split .cap .t em{color:var(--accent)}
""",
}

COCHE = ("<svg viewBox='0 0 40 40'><rect x='2' y='2' width='36' height='36' rx='8' fill='none' stroke='currentColor' stroke-width='3'/>"
         "<path d='M11 21l6 6 12-14' fill='none' stroke='currentColor' stroke-width='4' stroke-linecap='round' stroke-linejoin='round'/></svg>")
FLECHE = ("<svg class='fleche'{pos} viewBox='0 0 100 60'><path d='M8 30 H84 M60 9 L87 30 L60 51' fill='none' stroke='currentColor' "
          "stroke-width='11' stroke-linecap='round' stroke-linejoin='round'/></svg>")

# Tourne dans la page : ajuste les tailles, contrôle chaque slide, écrit le rapport dans #controle (lu par --dump-dom)
JS = r"""(() => {
const W = __W__, H = __H__, SAFE = __SAFE__;
const parse = s => { const n = (s || '').match(/[\d.]+/g); if (!n) return null; const v = n.map(Number);
  return s.startsWith('color(') ? [v[0] * 255, v[1] * 255, v[2] * 255, v.length > 3 ? v[3] : 1] : [v[0], v[1], v[2], v.length > 3 ? v[3] : 1]; };
const lum = c => { const f = v => { v /= 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); };
  return 0.2126 * f(c[0]) + 0.7152 * f(c[1]) + 0.0722 * f(c[2]); };
const ratio = (a, b) => { const x = lum(a), y = lum(b); return (Math.max(x, y) + 0.05) / (Math.min(x, y) + 0.05); };
const fondDe = el => {  // couleur pleine derrière le texte ; null s'il est posé sur une photo
  const bx = el.closest('.bx'); if (bx) return parse(getComputedStyle(bx.querySelector('.fond')).backgroundColor);
  for (let n = el; n; n = n.parentElement) {
    if (n.classList.contains('slide') && n.classList.contains('photo')) return null;
    const cs = getComputedStyle(n); if (cs.backgroundImage !== 'none') return null;
    const c = parse(cs.backgroundColor); if (c && c[3] > 0.5) return c;
  } return null; };
function ajuster() {
  document.querySelectorAll('.geant').forEach(g => {  // le mot géant fait 78 % de la largeur
    g.style.display = 'inline-block'; const fs = parseFloat(getComputedStyle(g).fontSize);
    const f = Math.min(220, fs * W * 0.78 / g.getBoundingClientRect().width); g.style.fontSize = f + 'px'; g.style.lineHeight = (f * .9) + 'px'; });
  document.querySelectorAll('.zone').forEach(z => {  // un texte long passe plus petit, jamais sous data-mini
    const t = z.querySelector('.ajuste'); if (!t) return;
    let fs = parseFloat(getComputedStyle(t).fontSize); const k = parseFloat(getComputedStyle(t).lineHeight) / fs, mini = parseFloat(t.dataset.mini || 34);
    while (z.scrollHeight > z.clientHeight + 8 && fs > mini) { fs = Math.max(mini, fs * 0.96); t.style.fontSize = fs + 'px'; t.style.lineHeight = (fs * k) + 'px'; } }); }
function verifier() {
  const pb = [], pires = [];
  document.querySelectorAll('.slide').forEach((s, i) => {
    const r0 = s.getBoundingClientRect(); let pire = 99;
    s.querySelectorAll('.zone').forEach(z => { if (z.scrollHeight > z.clientHeight + 8 || z.scrollWidth > z.clientWidth + 8)
      pb.push([i + 1, z.innerText.slice(0, 50), 'texte trop long pour sa zone']); });
    const logo = s.querySelector('.logo'), rl = logo && logo.getBoundingClientRect();
    s.querySelectorAll('.t').forEach(t => { for (const r of t.getClientRects()) {
      const x0 = r.left - r0.left, y0 = r.top - r0.top, x1 = r.right - r0.left, y1 = r.bottom - r0.top;
      if (!t.classList.contains('mini') && (x0 < SAFE - 1 || y0 < SAFE - 1 || x1 > W - SAFE + 1 || y1 > H - SAFE + 1)) {
        pb.push([i + 1, t.innerText.slice(0, 50), 'hors de la zone sûre']); break; }
      if (rl && r.right > rl.left && r.left < rl.right && r.bottom > rl.top && r.top < rl.bottom) {
        pb.push([i + 1, t.innerText.slice(0, 50), 'le logo touche le texte']); break; } } });
    s.querySelectorAll('.t, .t em').forEach(t => {
      if (!t.innerText.trim()) return; const bg = fondDe(t); if (!bg) return;
      const cs = getComputedStyle(t), c = parse(cs.color); if (!c || c[3] === 0) return;
      const v = ratio(c, bg), seuil = parseFloat(cs.fontSize) >= 24 ? 3 : 4.5; pire = Math.min(pire, v);
      if (v < seuil) pb.push([i + 1, t.innerText.slice(0, 50), 'contraste ' + v.toFixed(1) + ' sous ' + seuil]); });
    pires.push(Math.round(pire * 10) / 10); });
  return {problemes: pb, contraste: pires}; }
const n = parseInt(location.hash.slice(1), 10);
if (n) document.querySelectorAll('.slide').forEach((s, i) => { if (i + 1 !== n) s.style.display = 'none'; });
window.addEventListener('load', () => (document.fonts ? document.fonts.ready : Promise.resolve()).then(() => {
  ajuster(); document.getElementById('controle').textContent = JSON.stringify(verifier()); }));
})();"""


class Refus(SystemExit):
    """Le carrousel n'est pas rendu : la raison est dans le message."""


def fmt(s):
    """Échappe le HTML ; *mot* devient <em>, \\n un retour à la ligne, espaces insécables de la typographie française."""
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", html.escape(str(s), quote=False))
    s = re.sub(r" ([»?!:;])", "\u00a0\\1", s.replace("« ", "«\u00a0"))
    s = re.sub(r"(\w+(?:-\w+)+)", r'<span class="nowrap">\1</span>', s)  # un mot composé ne se coupe pas au trait d'union
    return s.replace("\\n", "<br>").replace("\n", "<br>")


def textes(x, cle=None):
    """Tous les textes affichés d'une slide (pour compter les mots et chercher les interdits)."""
    if isinstance(x, str):
        return [x] if cle in CLES_TEXTE else []
    if isinstance(x, list):
        return [t for v in x for t in textes(v, cle)]
    if isinstance(x, dict):
        return [t for k, v in x.items() if k in CLES_TEXTE for t in textes(v, k)]
    return []


def images(sl):
    out = [sl["image"]] if isinstance(sl.get("image"), str) else []
    if isinstance(sl.get("image"), dict):
        out.append(sl["image"].get("src", ""))
    return out + [sl[k]["image"] for k in ("haut", "bas", "carte") if isinstance(sl.get(k), dict) and sl[k].get("image")]


def champs(st, sl, i):
    e = []
    if st in ("podcast", "reel") and not sl.get("image"):
        e.append(f"slide {i} : image manquante")
    if st == "podcast":
        e += [f"slide {i} : champ « {k} » manquant" for k in (("mot", "ligne", "italique") if sl.get("type") == "couverture" else ("texte",))
              if not sl.get(k)]
    if st == "uni" and not (sl.get("titre") or (sl.get("carte") or {}).get("titre")):
        e.append(f"slide {i} : titre ou carte avec titre attendu")
    if st == "reel":
        if not (sl.get("boites") or sl.get("devoir")):
            e.append(f"slide {i} : boites ou devoir attendu")
        if sum(1 for b in sl.get("boites", []) if b.get("forte")) > 1:
            e.append(f"slide {i} : une seule boîte forte par slide (la couleur seulement là où l'œil doit se poser)")
    if st == "split":
        e += [f"slide {i} : {k} demande image et texte" for k in ("haut", "bas") if not ((sl.get(k) or {}).get("image") and (sl.get(k) or {}).get("texte"))]
    if sl.get("fond") not in (None, "clair", "sombre"):
        e.append(f"slide {i} : fond vaut clair ou sombre")
    return e


def verifier(spec, base):
    st = spec.get("style")
    if st not in STYLES:
        return [f"style inconnu : {st!r} (au choix : {', '.join(STYLES)})"]
    e = []
    w, h = spec.get("taille", [1080, 1350])
    if w != 1080 or not 1080 <= h <= 1920:
        e.append("taille : largeur 1080, hauteur de 1080 à 1920")
    slides = spec.get("slides") or []
    if not slides:
        e.append("aucune slide")
    lim = spec.get("max_mots", 22 if st == "reel" else 35)
    for i, sl in enumerate(slides, 1):
        txt = textes(sl)
        n = sum(len(re.findall(r"\w+", t)) for t in txt)
        if not txt:
            e.append(f"slide {i} : aucun texte")
        if n > lim:
            e.append(f"slide {i} : {n} mots, plus que {lim}. Coupe ou découpe en deux slides.")
        if any(GLISSER.search(t) for t in txt):
            e.append(f"slide {i} : « glisse » ou « swipe » interdit, l'accroche suffit à donner envie")
        if any(INTERDITS.search(t) for t in txt):
            e.append(f"slide {i} : mention inutile (« situation type », « mise en scène ») interdite")
        if any("\u2014" in t or "\u2013" in t for t in txt):
            e.append(f"slide {i} : tiret long ou moyen")
        e += [f"slide {i} : image introuvable ({p})" for p in images(sl) if not (base / p).exists()]
        e += champs(st, sl, i)
    return e


def boite(contenu, classes, theme=""):
    dt = f' data-theme="{theme}"' if theme else ""
    return f'<div class="bx {classes}"{dt}><span class="fond">{contenu}</span><div class="dessus"><span class="t">{contenu}</span></div></div>'


def _pos(m, cy=0.5):
    return f'{m.get("cx", .5) * 100:.0f}% {m.get("cy", cy) * 100:.0f}%'


def s_podcast(sl, i, c):
    img, pos = c["uri"](sl["image"]), _pos(sl, 0)
    fond = (f'<img class="flou" src="{img}"><div class="photo" style="height:{sl.get("photo", .68) * 100:.1f}%">'
            f'<img src="{img}" style="object-position:{pos};transform:scale({sl.get("zoom", 1)});transform-origin:{pos}"></div><div class="vig"></div>')
    if sl.get("type") == "couverture":
        txt = (f'<div class="zone couv"><h1 class="t geant" style="background-image:linear-gradient(var(--voile-mot),var(--voile-mot)),'
               f'url(\'{img}\')">{fmt(sl["mot"])}</h1><p class="t l">{fmt(sl["ligne"])}</p><p class="t it">{fmt(sl["italique"])}</p></div>')
    else:
        al = {"gauche": " gauche", "droite": " droite"}.get(sl.get("align"), "")
        corps = fmt(sl["texte"]).replace("<br><em>", "<em>").replace("</em><br>", "</em>")  # l'italique est déjà sa ligne
        txt = f'<div class="zone{al}"><p class="t corps ajuste">{corps}</p></div>'
    mini = f'<div class="t mini">{html.escape(c["pied"])}</div>' if c["pied"] else ""
    v = sl.get("voile", .7)
    return fond + txt + mini, "sombre", "photo", f"--voile:{v * 100:.0f}%;--voile2:{v * 60:.0f}%"


def s_uni(sl, i, c):
    pied = f'<div class="t pied">{html.escape(c["pied"])}</div>' if c["pied"] else ""
    theme = sl.get("fond", c["principal"])
    if sl.get("carte"):
        k = sl["carte"]
        corps = f'<p class="t ct">{fmt(k["titre"])}</p>' + (f'<p class="t cs">{fmt(k["sous_titre"])}</p>' if k.get("sous_titre") else "")
        if k.get("tableau"):
            corps += '<div class="rangs">' + "".join(
                f'<div class="rang"><span class="t a">{fmt(a)}</span>' + (f'<span class="t fl">&rarr;</span><span class="t b">{fmt(b)}</span>' if b else "")
                + "</div>" for a, b in k["tableau"]) + "</div>"
        if k.get("image"):
            corps += f'<img src="{c["uri"](k["image"])}">'
        if k.get("note"):
            corps += f'<p class="t cn">{fmt(k["note"])}</p>'
        return f'<div class="carte zone" data-theme="clair">{corps}</div>' + pied, theme, "", ""
    lignes = "".join(f'<p class="t ligne">{fmt(x)}</p>' for x in sl.get("lignes", []))
    lien = f'<p class="t lien">{fmt(sl["lien"])}</p>' if sl.get("lien") else ""
    return f'<div class="zone{" milieu" if sl.get("milieu") else ""}"><p class="t titre">{fmt(sl["titre"])}</p>{lignes}{lien}</div>' + pied, theme, "", ""


def s_edito(sl, i, c):
    theme = sl.get("fond", (c["principal"], c["autre"])[i % 2])  # clair et sombre alternés, comme la référence
    parts = [f'<p class="t titre">{fmt(sl["titre"])}</p>'] if sl.get("titre") else []
    if sl.get("image"):
        m = sl["image"]
        parts.append(f'<div class="media" style="--ratio:{m.get("ratio", "9/16")};--cx:{m.get("cx", .5) * 100:.0f}%">'
                     f'<img src="{c["uri"](m["src"])}"></div>')
    if sl.get("sous_titre"):
        parts.append(f'<p class="t sous">{fmt(sl["sous_titre"])}</p>')
    if sl.get("messages"):  # conversation : l'autre à gauche, moi à droite ; ni prénom, ni heure, ni interface d'application
        parts.append('<div class="conv">' + "".join(
            f'<p class="t msg {"moi" if m.get("de") == "moi" else "autre"}">{fmt(m["texte"])}</p>' for m in sl["messages"]) + "</div>")
    if sl.get("coches"):
        parts.append('<ul class="coches">' + "".join(f'<li>{COCHE}<span class="t">{fmt(x)}</span></li>' for x in sl["coches"]) + "</ul>")
    if sl.get("phrase"):
        parts.append(f'<p class="t phrase{" seule" if not parts else ""}">{fmt(sl["phrase"])}</p>')
    if sl.get("bulle"):
        parts.append(boite(fmt(sl["bulle"]), "bulle"))
    milieu = "" if (sl.get("image") or sl.get("bulle") or sl.get("messages")) else " milieu"
    return f'<div class="zone{milieu}">{"".join(parts)}</div>', theme, "", ""


def s_reel(sl, i, c):
    pos = _pos(sl)
    th = "sombre" if c["spec"].get("boite") == "sombre" else "clair"
    zone = "".join(boite(fmt(b["texte"]), f'b {b.get("taille", "l")}{" forte" if b.get("forte") else ""}', th) for b in sl.get("boites", []))
    out = (f'<img class="plein" src="{c["uri"](sl["image"])}" style="object-position:{pos};transform:scale({sl.get("zoom", 1)});'
           f'transform-origin:{pos}"><div class="zone" style="top:{sl.get("y", .1) * 100:.1f}%">{zone}</div>')
    if sl.get("devoir"):
        d = sl["devoir"]
        out += (f'<div class="devoir zone" data-theme="clair" style="top:{d.get("y", .36) * 100:.1f}%"><p class="dt"><mark class="t">'
                f'{fmt(d["titre"])}</mark></p><ol>' + "".join(f'<li class="t">{fmt(x)}</li>' for x in d["items"]) + "</ol></div>")
    return out, "sombre", "photo", ""


def s_split(sl, i, c):
    out = ""
    for cle, zoom in (("haut", 1.0), ("bas", 1.2)):  # le bas en plan plus serré, comme une deuxième caméra
        m = sl[cle]
        pos = _pos(m, .3)
        out += (f'<div class="moitie"><img src="{c["uri"](m["image"])}" style="object-position:{pos};transform:scale({m.get("zoom", zoom)});'
                f'transform-origin:{pos}"><div class="zone">{boite(fmt(m["texte"]), "cap", "sombre")}</div></div>')
    return out, "sombre", "photo", ""


GABARITS = {"podcast": s_podcast, "uni": s_uni, "edito": s_edito, "reel": s_reel, "split": s_split}


def trouver_marque(depart):
    for d in [Path(depart).resolve(), *Path(depart).resolve().parents, Path.cwd()]:
        m = d / "bibliotheque" / "marque"
        if (m / "charte-jetons.json").exists() and (m / "charte.css").exists():
            return m
    return None


def charger_charte(chemin, base):
    """-> (jetons, css, uri du logo ou None). Repli sur la charte simple si bibliotheque/marque/ n'existe pas."""
    m = Path(chemin).resolve().parent if chemin else trouver_marque(base)
    if not m:
        print("charte absente (bibliotheque/marque/) : charte simple utilisée", file=sys.stderr)
        return SIMPLE_JETONS, SIMPLE_CSS, None
    jt = json.loads((m / "charte-jetons.json").read_text(encoding="utf-8"))
    logo = None
    if jt.get("logo"):
        f = m.parent.parent / jt["logo"]  # le chemin du logo part de la racine du vault
        if f.exists():
            logo = f.resolve().as_uri()
        else:
            print(f"logo introuvable ({f}), rendu sans logo", file=sys.stderr)
    return jt, (m / "charte.css").read_text(encoding="utf-8"), logo


def page(spec, base, jt, css_charte, logo):
    st, (w, h) = spec["style"], spec.get("taille", [1080, 1350])
    principal = jt.get("principal", "clair")
    c = {"spec": spec, "principal": principal, "autre": "sombre" if principal == "clair" else "clair",
         "pied": spec.get("pied") or ("" if jt is SIMPLE_JETONS else jt.get("nom", "")),
         "uri": lambda p: (base / p).resolve().as_uri()}
    slides, n = [], len(spec["slides"])
    for i, sl in enumerate(spec["slides"]):
        corps, theme, cls, style = GABARITS[st](sl, i, c)
        if i == 0 and n > 1 and sl.get("fleche", True):  # flèche sur la couverture seulement, jamais le mot « glisse »
            pos = f" style='top:{(h - 4) // 2 + 30}px;bottom:auto'" if st == "split" else ""
            corps += ('<div class="coin"></div>' if st in ("podcast", "reel") else "") + FLECHE.format(pos=pos)
        if logo and i in (0, n - 1):
            corps += f'<img class="logo" src="{logo}" alt="">'
        slides.append(f'<div class="slide st-{st} {cls}" data-theme="{theme}" style="width:{w}px;height:{h}px;{style}">{corps}</div>')
    js = JS.replace("__W__", str(w)).replace("__H__", str(h)).replace("__SAFE__", str(SAFE))
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{css_charte}</style>'
            f'<style>:root{{--ombre:{jt["sombre"]["fond"]}}}{BASE_CSS}{CSS[st]}</style></head><body>{"".join(slides)}'
            f'<script type="application/json" id="controle"></script><script>{js}</script></body></html>')


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
    return None


def taille_png(f):
    with open(f, "rb") as fh:
        tete = fh.read(24)
    if tete[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("pas un PNG")
    return struct.unpack(">II", tete[16:24])


def rendre(chemin_json, sortie=None, charte=None):
    chemin_json = Path(chemin_json).resolve()
    spec = json.loads(chemin_json.read_text(encoding="utf-8"))
    base = chemin_json.parent
    erreurs = verifier(spec, base)
    if erreurs:
        raise Refus("Refusé :\n- " + "\n- ".join(erreurs))
    nav = navigateur()
    if not nav:
        raise SystemExit("Aucun navigateur Chrome, Chromium ou Edge trouvé. Installe-en un ou pose NAVIGATEUR=<chemin>.")
    jt, css_charte, logo = charger_charte(charte, base)
    w, h = spec.get("taille", [1080, 1350])
    sortie = Path(sortie or base / "png").resolve()
    sortie.mkdir(parents=True, exist_ok=True)
    f_html = sortie / "_carrousel.html"
    f_html.write_text(page(spec, base, jt, css_charte, logo), encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [nav, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run", "--no-default-browser-check",
               f"--user-data-dir={Path(tmp) / 'profil'}", f"--window-size={w},{h}", "--force-device-scale-factor=1",
               "--virtual-time-budget=8000"]  # attend les polices et les images avant de juger ou de capturer
        r = subprocess.run(cmd + ["--dump-dom", f_html.as_uri()], capture_output=True, text=True, encoding="utf-8", timeout=180)
        m = re.search(r'<script type="application/json" id="controle">(.*?)</script>', r.stdout or "", re.S)
        if not m or not m.group(1).strip():
            raise SystemExit(f"Les contrôles n'ont pas tourné dans le navigateur.\n{(r.stderr or '')[-600:]}")
        rapport = json.loads(m.group(1))
        if rapport["problemes"]:
            raise Refus("Refusé :\n" + "\n".join(f"- slide {n} : {pb} : « {t.strip()} »" for n, t, pb in rapport["problemes"]))
        faits = []
        for i in range(1, len(spec["slides"]) + 1):
            f_png = sortie / f"slide-{i:02d}.png"
            f_png.unlink(missing_ok=True)
            r = subprocess.run(cmd + [f"--screenshot={f_png}", f"{f_html.as_uri()}#{i}"], capture_output=True, text=True, timeout=180)
            if not f_png.exists():
                raise SystemExit(f"Le navigateur n'a pas rendu la slide {i}.\n{r.stderr[-600:]}")
            if taille_png(f_png) != (w, h):
                raise SystemExit(f"Slide {i} rendue en {taille_png(f_png)}, attendu {(w, h)}.")
            faits.append(f_png)
    (sortie / "_controles.txt").write_text("".join(f"slide {i:02d} : contraste mini {v}\n" for i, v in enumerate(rapport["contraste"], 1)),
                                           encoding="utf-8")
    print(f"{len(faits)} slides rendues dans {sortie}")
    return faits


# ------------------------------------------------------------------------------------------ vidéo
def ffmpeg(*args):
    r = subprocess.run(["ffmpeg", "-v", "error", "-y", *args], capture_output=True, text=True)
    if r.returncode:
        raise SystemExit(f"Erreur ffmpeg :\n{r.stderr[-600:]}")


def filtre_sdr(video):
    """Vidéo HDR de téléphone : sans conversion, les images sortent délavées. -> début de filtre ffmpeg, ou ''."""
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=color_transfer",
                        "-of", "csv=p=0", str(video)], capture_output=True, text=True)
    if r.stdout.strip() not in ("smpte2084", "arib-std-b67"):
        return ""
    if "zscale" in subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout:
        return "zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,"
    print("vidéo HDR et ffmpeg sans zscale : images peut-être délavées (installe une version complète de ffmpeg)", file=sys.stderr)
    return ""


def image_nette(video, t, sortie, sdr=""):
    """Autour de t (plus ou moins 0,6 s), garde l'image la plus nette. shortcut: la netteté se lit au poids du JPEG
    (plus de détails = fichier plus lourd), pas de détecteur d'yeux : vérifier les yeux ouverts sur la planche."""
    d0 = max(0.0, t - 0.6)
    with tempfile.TemporaryDirectory() as tmp:
        ffmpeg("-ss", f"{d0:.3f}", "-t", "1.2", "-i", str(video), "-vf", f"{sdr}fps=10,scale=480:-2", "-q:v", "3", str(Path(tmp) / "c%02d.jpg"))
        cands = sorted(Path(tmp).glob("c*.jpg"), key=lambda f: f.stat().st_size)
        if not cands:
            raise SystemExit(f"aucune image à {t} s (la vidéo est-elle plus courte ?)")
        meilleur = d0 + (int(cands[-1].stem[1:]) - 1) / 10
    ffmpeg("-ss", f"{meilleur:.3f}", "-i", str(video), "-frames:v", "1", "-vf", f"{sdr}null", "-q:v", "2", str(sortie))
    return sortie


def extraire(video, instants, dossier):
    for outil in ("ffmpeg", "ffprobe"):
        if not shutil.which(outil):
            raise SystemExit(f"{outil} introuvable : installe ffmpeg (Windows : winget install ffmpeg).")
    dossier = Path(dossier)
    dossier.mkdir(parents=True, exist_ok=True)
    sdr = filtre_sdr(video)
    return [image_nette(video, t, dossier / f"{n:02d}.jpg", sdr) for n, t in enumerate(instants, 1)]


def lire_sous_titres(f):
    """Fichier .srt ou .vtt -> [(texte, début, fin)] en secondes."""
    out = []
    for bloc in re.split(r"\n\s*\n", Path(f).read_text(encoding="utf-8-sig").replace("\r", "")):
        m = re.search(r"(?:(\d+):)?(\d+):(\d+)[.,](\d+)\s*-->\s*(?:(\d+):)?(\d+):(\d+)[.,](\d+)", bloc)
        if not m:
            continue
        g = [int(x or 0) for x in m.groups()]
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        texte = re.sub(r"<[^>]+>", "", " ".join(bloc[m.end():].split())).strip()
        if texte:
            out.append((texte, a, b))
    return out


def mots_srt(f, debut, fin):
    """Les mots entre début et fin, chacun avec un temps réparti dans son sous-titre."""
    out = []
    for texte, a, b in lire_sous_titres(f):
        if b <= debut or a >= fin:
            continue
        ws = texte.split()
        out += [(" " + w, a + (b - a) * k / len(ws), a + (b - a) * (k + 1) / len(ws)) for k, w in enumerate(ws)]
    if not out:
        raise SystemExit("aucun sous-titre entre début et fin")
    return out


def morceaux(liste, mini=8, maxi=10):
    """Phrases (fin sur . ? ! …), puis mini à maxi morceaux : fusion des voisines les plus courtes,
    ou coupe d'une phrase longue à sa virgule la plus centrale."""
    phrases, cur = [], []
    for w in liste:
        cur.append(w)
        if w[0].strip().endswith((".", "?", "!", "…")):
            phrases.append(cur)
            cur = []
    if cur:
        phrases.append(cur)
    while len(phrases) > maxi:
        k = min(range(len(phrases) - 1), key=lambda j: len(phrases[j]) + len(phrases[j + 1]))
        phrases[k:k + 2] = [phrases[k] + phrases[k + 1]]
    while len(phrases) < mini:
        k = max(range(len(phrases)), key=lambda j: len(phrases[j]))
        virg = [j for j, w in enumerate(phrases[k][:-1]) if w[0].strip().endswith(",")]
        if not virg:
            break
        c = min(virg, key=lambda j: abs(j - len(phrases[k]) / 2))
        phrases[k:k + 1] = [phrases[k][:c + 1], phrases[k][c + 1:]]
    return [("".join(w[0] for w in ph).strip(), ph[0][1], ph[-1][2]) for ph in phrases]


def brouillon(style, video, srt, debut, fin, dossier):
    """reel : 8 à 10 morceaux, une image chacun. split : 12 à 20 morceaux rangés par paires (une slide = deux phrases).
    Le texte est la transcription brute : à réécrire avant le rendu (couverture, appel final compris)."""
    dossier = Path(dossier)
    parts = morceaux(mots_srt(srt, debut, fin), *((8, 10) if style == "reel" else (12, 20)))
    if style == "split" and len(parts) % 2:  # nombre impair : les deux derniers morceaux n'en font qu'un
        (a, d, _), (b, _, f) = parts[-2:]
        parts[-2:] = [(f"{a} {b}", d, f)]
    imgs = extraire(video, [(a + b) / 2 for _, a, b in parts], dossier / "img")
    morc = [{"image": f"img/{p.name}", "t": [round(a, 2), round(b, 2)], "texte": txt} for (txt, a, b), p in zip(parts, imgs)]
    if style == "reel":
        slides = [{"image": m["image"], "t": m["t"], "boites": [{"texte": m["texte"]}]} for m in morc]
    else:
        slides = [{"haut": h, "bas": b} for h, b in zip(morc[::2], morc[1::2])]
    spec = {"style": style, "source": Path(video).name, "slides": slides}
    (dossier / "slides.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1), encoding="utf-8")
    print(dossier / "slides.json")
    return dossier / "slides.json"


# ----------------------------------------------------------------------------------------- auto-test
def _png_test(f, w=320, h=180):
    """Une petite photo en dégradé, écrite sans bibliothèque."""
    lignes = b"".join(b"\x00" + bytes(v for x in range(w) for v in (60 + x * 150 // w, 90 + y * 100 // h, 120)) for y in range(h))
    bloc = lambda t, d: struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)
    Path(f).write_bytes(b"\x89PNG\r\n\x1a\n" + bloc(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                        + bloc(b"IDAT", zlib.compress(lignes)) + bloc(b"IEND", b""))


def _charte_kit():
    ici = Path(__file__).resolve().parent
    for f in (ici / "charte.py", ici.parent / "scripts" / "charte.py", ici.parents[1] / "charte-graphique" / "outils" / "charte.py"):
        if f.exists():
            import importlib.util
            s = importlib.util.spec_from_file_location("charte", f)
            mod = importlib.util.module_from_spec(s)
            s.loader.exec_module(mod)
            return mod
    return None


def auto_test():
    assert "\u00a0?" in fmt("Vraiment ?") and "<em>mot</em>" in fmt("un *mot*") and "<br>" in fmt("a\nb")
    assert GLISSER.search("Glisse pour voir la suite") and GLISSER.search("Swipe") and not GLISSER.search("Le vélo glisse sur la route.")
    assert textes({"titre": "a", "image": "x.jpg", "messages": [{"de": "moi", "texte": "b"}], "haut": {"image": "y", "texte": "c"}}) == ["a", "b", "c"]
    mots = []
    for i in range(14):  # 14 phrases de 4 mots, une virgule au milieu
        mots += [(" Mot", i, i + .2), (" deux,", i + .2, i + .4), (" trois", i + .4, i + .6), (" fin.", i + .6, i + .8)]
    assert 8 <= len(morceaux(mots)) <= 10 and len(morceaux(mots[:16])) == 8
    ch = _charte_kit()
    if ch:  # le repli doit rester la charte « simple » de charte.py
        j = ch.jetons(ch.PROPOSITIONS["simple"])
        assert j == SIMPLE_JETONS, "SIMPLE_JETONS diffère de charte.py"
        assert ch.css(j).split("\n", 1)[1] == SIMPLE_CSS, "SIMPLE_CSS diffère de charte.py"
    for nom, css in [("base", BASE_CSS + COCHE + FLECHE + JS), *CSS.items()]:  # aucune couleur écrite en dur
        assert not re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|\b(?:white|black)\b(?!-)", css), nom
    nav = navigateur()
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "img").mkdir()
        _png_test(d / "img" / "01.jpg")
        _png_test(d / "img" / "02.jpg")
        srt = d / "v.vtt"
        srt.write_text("WEBVTT\n\n00:01.000 --> 00:03.000\nJ'arrosais le soir.\n\n00:03.000 --> 00:05.500\nPuis, un jour, j'ai <b>changé</b>.\n",
                       encoding="utf-8")
        assert lire_sous_titres(srt)[1] == ("Puis, un jour, j'ai changé.", 3.0, 5.5)
        marque = d / "vault" / "bibliotheque" / "marque"
        marque.mkdir(parents=True)
        jt = json.loads(json.dumps(SIMPLE_JETONS))
        jt.update({"nom": "Atelier Test", "logo": "bibliotheque/marque/logo.png"})
        (marque / "charte-jetons.json").write_text(json.dumps(jt), encoding="utf-8")
        (marque / "charte.css").write_text(SIMPLE_CSS, encoding="utf-8")
        _png_test(marque / "logo.png", 96, 48)
        for st, ex in EXEMPLES.items():
            assert verifier(ex, d) == [], (st, verifier(ex, d))
            h = page(ex, d, *charger_charte(marque / "charte-jetons.json", d))
            assert "var(--texte)" in h and f"st-{st}" in h and 'class="logo"' in h, st
        assert any("forte" in e for e in verifier({"style": "reel", "slides": [
            {"image": "img/01.jpg", "boites": [{"texte": "A", "forte": True}, {"texte": "B", "forte": True}]}]}, d))
        assert any("mots" in e for e in verifier({"style": "uni", "slides": [{"titre": "mot " * 40}]}, d))
        assert any("introuvable" in e for e in verifier({"style": "reel", "slides": [{"image": "nulle.jpg", "boites": [{"texte": "a"}]}]}, d))
        assert any("glisse" in e for e in verifier({"style": "uni", "slides": [{"titre": "Glisse pour voir"}]}, d))
        assert any("tiret" in e for e in verifier({"style": "uni", "slides": [{"titre": "a \u2014 b"}]}, d))
        if not nav:
            print("navigateur absent : rendu PNG non testé (HTML et contrôles testés)")
        else:
            for st, ex in EXEMPLES.items():
                f = d / f"{st}.json"
                f.write_text(json.dumps(ex, ensure_ascii=False), encoding="utf-8")
                pngs = rendre(f, d / st, marque / "charte-jetons.json")
                assert len(pngs) == len(ex["slides"]) and all(taille_png(p) == (1080, 1350) for p in pngs), st
            pub = {"style": "edito", "taille": [1080, 1080], "slides": [EXEMPLES["edito"]["slides"][0]]}
            (d / "pub.json").write_text(json.dumps(pub, ensure_ascii=False), encoding="utf-8")
            assert taille_png(rendre(d / "pub.json", d / "pub")[0]) == (1080, 1080)
            (d / "long.json").write_text(json.dumps({"style": "uni", "max_mots": 99, "slides": [
                {"titre": "Une phrase bien trop longue pour tenir dans une seule slide de carrousel. " * 6}]}), encoding="utf-8")
            try:
                rendre(d / "long.json", d / "long")
                raise AssertionError("le texte trop long aurait dû être refusé")
            except Refus as e:
                assert "trop long" in str(e) or "zone sûre" in str(e), e
            mauvaise = d / "mauvaise" / "bibliotheque" / "marque"  # accent illisible : le texte de la boîte forte est refusé
            mauvaise.mkdir(parents=True)
            (mauvaise / "charte-jetons.json").write_text(json.dumps(SIMPLE_JETONS), encoding="utf-8")
            (mauvaise / "charte.css").write_text(SIMPLE_CSS.replace("--accent-texte:#ffffff", "--accent-texte:#3a63d8"), encoding="utf-8")
            (d / "reel2.json").write_text(json.dumps(EXEMPLES["reel"], ensure_ascii=False), encoding="utf-8")
            try:
                rendre(d / "reel2.json", d / "reel2", mauvaise / "charte-jetons.json")
                raise AssertionError("le contraste trop bas aurait dû être refusé")
            except Refus as e:
                assert "contraste" in str(e), e
        if shutil.which("ffmpeg") and shutil.which("ffprobe"):
            video = d / "v.mp4"
            ffmpeg("-f", "lavfi", "-i", "testsrc=size=640x360:rate=25:duration=6", "-pix_fmt", "yuv420p", str(video))
            sj = brouillon("reel", video, srt, 0, 6, d / "brouillon")
            spec = json.loads(sj.read_text(encoding="utf-8"))
            assert spec["slides"] and all((d / "brouillon" / s["image"]).exists() for s in spec["slides"])
        else:
            print("ffmpeg absent : images de vidéo non testées")
    print("AUTO-TEST OK")


def main():
    if sys.argv[1:] == ["--test"]:
        return auto_test()
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("rendre"); r.add_argument("json"); r.add_argument("-o", "--sortie"); r.add_argument("--charte")
    e = sub.add_parser("exemple"); e.add_argument("style", choices=STYLES)
    im = sub.add_parser("images"); im.add_argument("video"); im.add_argument("--at", required=True); im.add_argument("-o", "--sortie", required=True)
    for nom in ("reel", "split"):
        b = sub.add_parser(nom); b.add_argument("video"); b.add_argument("--srt", required=True)
        b.add_argument("--debut", type=float, default=0.0); b.add_argument("--fin", type=float, required=True); b.add_argument("-o", "--sortie", required=True)
    a = ap.parse_args()
    if a.cmd == "rendre":
        rendre(a.json, a.sortie, a.charte)
    elif a.cmd == "exemple":
        print(json.dumps(EXEMPLES[a.style], ensure_ascii=False, indent=2))
    elif a.cmd == "images":
        for f in extraire(a.video, [float(x) for x in a.at.split(",")], a.sortie):
            print(f)
    else:
        brouillon(a.cmd, a.video, a.srt, a.debut, a.fin, a.sortie)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
