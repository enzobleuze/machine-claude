"""charte.py : la charte graphique de la marque, lue par le cockpit, les carrousels et le montage.

Usage : python scripts/charte.py valider [bibliotheque/marque/charte.json]
        python scripts/charte.py construire [charte.json]     (écrit charte.css et charte-jetons.json à côté)
        python scripts/charte.py apercu [charte.json] [-o apercu.html]
        python scripts/charte.py proposer [-o bibliotheque/marque/propositions] [fichiers.json en plus]
        python scripts/charte.py --test
On choisit trois couleurs (fond, texte, accent), deux polices et un thème principal (clair ou sombre).
Le script déduit le reste : surfaces, lignes, texte doux, texte posé sur l'accent, couleurs d'état,
et le thème inverse. Il garantit les contrastes : texte 4,5 au moins, accent 3,5, couleurs d'état 3.
Bibliothèque standard seulement.
"""
from __future__ import annotations

import colorsys
import html
import json
import re
import sys
import tempfile
from pathlib import Path

DEFAUT = Path("bibliotheque/marque/charte.json")
HEX = re.compile(r"^#[0-9a-fA-F]{6}$")
SERIF = {"fraunces", "lora", "playfair display", "merriweather", "dm serif display", "cormorant garamond",
         "libre baskerville", "eb garamond", "source serif 4", "besley", "crimson pro", "spectral", "georgia"}
PROPOSITIONS = {
    "simple": {"nom": "Simple", "theme": "clair", "polices": {"titres": "Inter", "texte": "Inter"},
               "couleurs": {"fond": "#fafaf8", "texte": "#1d1d1b", "accent": "#2f5bd3"}, "mots": ["net", "lisible", "sobre"]},
    "lumineux": {"nom": "Lumineux", "theme": "clair", "polices": {"titres": "Fraunces", "texte": "Inter"},
                 "couleurs": {"fond": "#fbf6ef", "texte": "#2a211b", "accent": "#c4572e", "accent_2": "#3d7a6f"},
                 "mots": ["chaleureux", "solaire", "accueillant"]},
    "doux": {"nom": "Doux naturel", "theme": "clair", "polices": {"titres": "Lora", "texte": "Nunito Sans"},
             "couleurs": {"fond": "#f4f1ea", "texte": "#26302b", "accent": "#5b7f5f", "accent_2": "#b07d62"},
             "mots": ["apaisant", "naturel", "doux"]},
    "sombre": {"nom": "Sombre élégant", "theme": "sombre", "polices": {"titres": "Playfair Display", "texte": "Inter"},
               "couleurs": {"fond": "#16151a", "texte": "#eceae6", "accent": "#e3a08a", "accent_2": "#9fb7d9"},
               "mots": ["élégant", "intime", "profond"]},
}


def rgb(h: str) -> tuple[float, float, float]:
    return tuple(int(h[i:i + 2], 16) / 255 for i in (1, 3, 5))


def hexa(c) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, x)) * 255):02x}" for x in c)


def luminance(h: str) -> float:
    f = lambda c: c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (f(x) for x in rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def melange(a: str, b: str, t: float) -> str:
    return hexa(x + (y - x) * t for x, y in zip(rgb(a), rgb(b)))


def est_clair(fond: str) -> bool:
    return contraste(fond, "#000000") > contraste(fond, "#ffffff")


def ajuster(couleur: str, fond: str, mini: float) -> str:
    """Fonce (fond clair) ou éclaircit (fond sombre) la couleur jusqu'au contraste voulu."""
    h, l, s = colorsys.rgb_to_hls(*rgb(couleur))
    clair, c = est_clair(fond), couleur
    for _ in range(60):
        if contraste(c, fond) >= mini:
            break
        l = max(0.0, l - 0.02) if clair else min(1.0, l + 0.02)
        c = hexa(colorsys.hls_to_rgb(h, l, s))
    return c


def theme(fond: str, texte: str, accent: str, accent_2: str | None) -> dict:
    texte = ajuster(texte, fond, 4.5)
    acc = ajuster(accent, fond, 3.5)  # 3 suffit en norme, 3,5 évite l'accent terne sur fond sombre
    return {
        "fond": fond, "surface": melange(fond, texte, 0.04), "surface_2": melange(fond, texte, 0.08),
        "ligne": melange(fond, texte, 0.16), "texte": texte,
        "texte_doux": ajuster(melange(texte, fond, 0.35), fond, 4.5),
        "accent": acc, "accent_texte": max(("#ffffff", "#141414"), key=lambda c: contraste(c, acc)),
        "accent_2": ajuster(accent_2 or melange(acc, texte, 0.4), fond, 3.0),
        "ok": ajuster("#2e8b57", fond, 3.0), "alerte": ajuster("#d98a1f", fond, 3.0),
        "erreur": ajuster("#c8374d", fond, 3.0),
    }


def valider(ch: dict, base: Path) -> list[str]:
    pb, c = [], ch.get("couleurs", {})
    for k in ("fond", "texte", "accent", "accent_2"):
        if (k != "accent_2" or c.get(k)) and not HEX.match(str(c.get(k, ""))):
            pb.append(f"couleur {k} absente ou pas au format #rrggbb")
    if not pb and contraste(c["texte"], c["fond"]) < 4.5:
        pb.append(f"texte trop pâle sur le fond : contraste {contraste(c['texte'], c['fond']):.1f}, il faut 4,5")
    for k in ("titres", "texte"):
        if not ch.get("polices", {}).get(k):
            pb.append(f"police {k} absente")
    if ch.get("theme", "clair") not in ("clair", "sombre"):
        pb.append("theme doit valoir clair ou sombre")
    if ch.get("logo") and not (base / ch["logo"]).exists():
        pb.append(f"logo introuvable : {ch['logo']}")
    return pb


def jetons(ch: dict) -> dict:
    c, principal = ch["couleurs"], ch.get("theme", "clair")
    t1 = theme(c["fond"], c["texte"], c["accent"], c.get("accent_2"))
    vers = "#000000" if principal == "clair" else "#ffffff"
    t2 = theme(melange(c["texte"], vers, 0.3 if principal == "clair" else 0.6), c["fond"], c["accent"], c.get("accent_2"))
    autre = "sombre" if principal == "clair" else "clair"
    return {"nom": ch.get("nom", "Ma marque"), "principal": principal, principal: t1, autre: t2,
            "polices": ch["polices"], "rayon": int(ch.get("rayon", 10)), "logo": ch.get("logo", ""),
            "mots": ch.get("mots", [])}


def pile(nom: str) -> str:
    # police de secours si la police n'est pas chargée (hors ligne)
    return f"'{nom}', " + ("Georgia, serif" if nom.lower() in SERIF else "system-ui, 'Segoe UI', sans-serif")


def import_polices(liste: list[dict]) -> str:
    noms = sorted({p for j in liste for p in j["polices"].values()})
    fam = "&".join(f"family={n.replace(' ', '+')}:wght@400;500;600;700" for n in noms)
    return f'@import url("https://fonts.googleapis.com/css2?{fam}&display=swap");'


def variables(j: dict, t: str) -> str:
    v = [f"--{k.replace('_', '-')}:{x}" for k, x in j[t].items()]
    v += [f"--police-titres:{pile(j['polices']['titres'])}", f"--police-texte:{pile(j['polices']['texte'])}",
          f"--rayon:{j['rayon']}px", f"color-scheme:{'light' if t == 'clair' else 'dark'}"]
    return ";".join(v)


def css(j: dict) -> str:
    return (f"/* charte.css : généré par charte.py depuis charte.json, ne pas modifier à la main */\n"
            f"{import_polices([j])}\n:root{{{variables(j, j['principal'])}}}\n"
            f'[data-theme="clair"]{{{variables(j, "clair")}}}\n[data-theme="sombre"]{{{variables(j, "sombre")}}}\n')


def carte(j: dict, t: str) -> str:
    e, n = html.escape, html.escape(j["nom"])
    nuancier = "".join(f'<div class="pastille"><span style="background:{x}"></span>{e(k)}<code>{x}</code></div>'
                       for k, x in j[t].items())
    return f"""<section class="charte" style="{variables(j, t)}">
<header><h2>{n}</h2><p>Thème {t}{' (principal)' if t == j['principal'] else ''} · {e(', '.join(j['mots']))}</p></header>
<div class="grille"><div class="kpi"><small>Encaissé ce mois</small><b>1 240 €</b><em>3 ventes</em></div>
<div class="slide"><small>{n}</small><h3>Le titre qui arrête le pouce, avec un <mark>mot</mark> en couleur</h3><p>Une phrase de texte courant, lisible d'un coup d'œil.</p></div>
<div class="sous-titre"><span>Et là, tu te dis</span> <span class="fort">encore une fois</span></div></div>
<div class="nuancier">{nuancier}</div></section>"""


def page(liste: list[dict], titre: str) -> str:
    sections = "".join(carte(j, t) for j in liste for t in (j["principal"], "sombre" if j["principal"] == "clair" else "clair"))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(titre)}</title><style>{import_polices(liste)}
body{{margin:0;padding:24px 16px;background:#e9e9e7;font-family:system-ui,sans-serif;display:grid;gap:20px;
grid-template-columns:repeat(auto-fit,minmax(min(100%,520px),1fr))}}
.charte{{background:var(--fond);color:var(--texte);font-family:var(--police-texte);border-radius:var(--rayon);padding:20px;border:1px solid var(--ligne)}}
.charte h2,.charte h3{{font-family:var(--police-titres);margin:0}} header p{{color:var(--texte-doux);margin:4px 0 14px}}
.grille{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}
.kpi{{background:var(--surface);border:1px solid var(--ligne);border-radius:var(--rayon);padding:14px;display:grid;gap:4px}}
.kpi small,.kpi em{{color:var(--texte-doux);font-style:normal}} .kpi b{{font-size:26px;color:var(--accent)}}
.slide{{grid-row:span 2;aspect-ratio:4/5;background:var(--surface-2);border-radius:var(--rayon);padding:18px;display:flex;flex-direction:column;justify-content:center;gap:10px}}
.slide small{{color:var(--texte-doux)}} .slide h3{{font-size:22px;line-height:1.2}} mark{{background:none;color:var(--accent)}}
.sous-titre{{background:#000;border-radius:var(--rayon);padding:18px;text-align:center;font:700 20px var(--police-texte);color:#fff}}
.fort{{background:var(--accent);color:var(--accent-texte);padding:0 6px;border-radius:4px}}
.nuancier{{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:6px;margin-top:14px;font-size:12px}}
.pastille{{display:flex;align-items:center;gap:6px}} .pastille span{{width:18px;height:18px;border-radius:4px;border:1px solid var(--ligne)}}
.pastille code{{color:var(--texte-doux);margin-left:auto}}</style></head><body>{sections}</body></html>"""


def lire(chemin: Path) -> dict:
    return json.loads(chemin.read_text(encoding="utf-8"))


def auto_test() -> int:
    for nom, ch in PROPOSITIONS.items():
        assert valider(ch, Path(".")) == [], (nom, valider(ch, Path(".")))
        j = jetons(ch)
        for t in ("clair", "sombre"):
            assert contraste(j[t]["texte"], j[t]["fond"]) >= 4.5, (nom, t)
            assert contraste(j[t]["texte_doux"], j[t]["fond"]) >= 4.5, (nom, t)
            for k in ("accent", "accent_2", "ok", "alerte", "erreur"):
                assert contraste(j[t][k], j[t]["fond"]) >= 3, (nom, t, k)
            assert contraste(j[t]["accent_texte"], j[t]["accent"]) >= 3, (nom, t)
    mauvais = {"couleurs": {"fond": "#ffffff", "texte": "#dddddd", "accent": "rouge"}, "polices": {"titres": "Inter"},
               "logo": "absent.png"}
    pb = valider(mauvais, Path("."))
    for attendu in ("accent", "police texte", "logo"):
        assert any(attendu in p for p in pb), (attendu, pb)
    pb = valider({**mauvais, "couleurs": {"fond": "#ffffff", "texte": "#dddddd", "accent": "#336699"}}, Path("."))
    assert any("trop pâle" in p for p in pb), pb
    with tempfile.TemporaryDirectory() as tmp:
        f = Path(tmp) / "charte.json"
        f.write_text(json.dumps(PROPOSITIONS["lumineux"]), encoding="utf-8")
        assert main(["construire", str(f)]) == 0
        texte_css = (Path(tmp) / "charte.css").read_text(encoding="utf-8")
        assert "--accent:" in texte_css and '[data-theme="sombre"]' in texte_css and "Fraunces" in texte_css
        assert json.loads((Path(tmp) / "charte-jetons.json").read_text(encoding="utf-8"))["sombre"]["fond"]
        assert main(["proposer", "-o", str(Path(tmp) / "props")]) == 0
        assert "Doux naturel" in (Path(tmp) / "props" / "apercu.html").read_text(encoding="utf-8")
    print("AUTO-TEST OK")
    return 0


def main(args: list[str]) -> int:
    if not args or args[0] in ("-h", "--help"):
        print(__doc__)
        return 2
    if args[0] == "--test":
        return auto_test()
    cmd, reste = args[0], args[1:]
    sortie = Path(reste[reste.index("-o") + 1]) if "-o" in reste else None
    fichiers = [Path(a) for i, a in enumerate(reste) if a != "-o" and (i == 0 or reste[i - 1] != "-o")]
    if cmd == "proposer":
        dossier = sortie or DEFAUT.parent / "propositions"
        dossier.mkdir(parents=True, exist_ok=True)
        liste = []
        for nom, ch in PROPOSITIONS.items():
            (dossier / f"{nom}.json").write_text(json.dumps(ch, ensure_ascii=False, indent=2), encoding="utf-8")
            liste.append(jetons(ch))
        liste += [jetons(lire(f)) for f in fichiers]  # une proposition sur mesure écrite par Claude
        (dossier / "apercu.html").write_text(page(liste, "Propositions de charte"), encoding="utf-8")
        print(f"{len(liste)} propositions : {dossier / 'apercu.html'}")
        return 0
    chemin = fichiers[0] if fichiers else DEFAUT
    if not chemin.exists():
        print(f"introuvable : {chemin} (lance d'abord « proposer » ou écris charte.json)")
        return 1
    ch = lire(chemin)
    pb = valider(ch, Path.cwd())
    for p in pb:
        print("  ", p)
    if pb:
        print(f"CHARTE À CORRIGER : {len(pb)} point(s)")
        return 1
    j = jetons(ch)
    if cmd == "valider":
        if j[j["principal"]]["accent"].lower() != ch["couleurs"]["accent"].lower():
            print(f"   accent ajusté pour rester lisible : {ch['couleurs']['accent']} devient {j[j['principal']]['accent']}")
        print("CHARTE OK")
        return 0
    if cmd == "construire":
        (chemin.parent / "charte.css").write_text(css(j), encoding="utf-8")
        (chemin.parent / "charte-jetons.json").write_text(json.dumps(j, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"écrit : {chemin.parent / 'charte.css'} et charte-jetons.json")
        return 0
    if cmd == "apercu":
        out = sortie or chemin.parent / "apercu.html"
        out.write_text(page([j], f"Charte {j['nom']}"), encoding="utf-8")
        print(f"aperçu : {out}")
        return 0
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
