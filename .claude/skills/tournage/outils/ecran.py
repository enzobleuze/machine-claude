"""ecran.py : un script texte ou Markdown devient une page de lecture plein écran pour le tournage.

Fond sombre, texte blanc en grand, lignes courtes. Les lignes entre crochets [comme ceci] sont des notes
(affichées en bleu, plus petites) : repères de slide, gestes, rappels. Aucune bibliothèque à installer.

  python ecran.py script.md [-o ecran.html] [--taille 46]
  python ecran.py --test

Dans le navigateur : F11 pour le plein écran, Espace ou flèche bas pour avancer, flèche haut pour revenir,
+ et - pour la taille du texte. Place la fenêtre juste sous l'objectif de la caméra pour garder le regard.
"""
import argparse, html, os, re, sys, tempfile

PAGE = """<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>Écran de tournage</title><style>
html,body{{margin:0;background:#0d0d0d;color:#fff}}
main{{max-width:28em;margin:0 auto;padding:30vh 1.5em 70vh;font:{taille}px/1.45 Arial,sans-serif}}
p{{margin:0 0 1.1em}} .note{{color:#6fa8ff;font-size:.62em}} h2{{color:#e8c46a;font-size:.8em;margin:2em 0 .6em}}
</style></head><body><main>
{corps}
</main><script>
let t={taille};const m=document.querySelector('main');
addEventListener('keydown',e=>{{
 if(e.key===' '||e.key==='ArrowDown'){{e.preventDefault();scrollBy({{top:innerHeight*0.3,behavior:'smooth'}})}}
 if(e.key==='ArrowUp'){{e.preventDefault();scrollBy({{top:-innerHeight*0.3,behavior:'smooth'}})}}
 if(e.key==='+'){{t+=4;m.style.fontSize=t+'px'}} if(e.key==='-'){{t=Math.max(20,t-4);m.style.fontSize=t+'px'}}
}});
</script></body></html>"""


def convertir(texte):
    blocs = []
    for bloc in re.split(r"\n\s*\n", texte.strip()):
        b = bloc.strip()
        if not b or b.startswith("---"):
            continue
        if b.startswith("#"):
            blocs.append(f"<h2>{html.escape(b.lstrip('#').strip())}</h2>")
        elif b.startswith("[") and b.endswith("]"):
            blocs.append(f'<p class="note">{html.escape(b[1:-1])}</p>')
        else:
            lignes = [html.escape(l.strip()) for l in b.splitlines() if l.strip()]
            blocs.append("<p>" + "<br>".join(lignes) + "</p>")
    return "\n".join(blocs)


def ecrire(source, sortie=None, taille=46):
    with open(source, encoding="utf-8") as f:
        corps = convertir(f.read())
    if not corps:
        raise SystemExit("Script vide.")
    sortie = sortie or os.path.splitext(source)[0] + "-ecran.html"
    with open(sortie, "w", encoding="utf-8") as f:
        f.write(PAGE.format(taille=taille, corps=corps))
    print(f"Écran écrit : {sortie}")
    return sortie


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        s = os.path.join(tmp, "script.md")
        with open(s, "w", encoding="utf-8") as f:
            f.write("# Accroche\n\nPhrase une.\nPhrase deux <ok>.\n\n[Slide 2 : le schéma]\n\nFin.")
        out = open(ecrire(s), encoding="utf-8").read()
        assert "<h2>Accroche</h2>" in out and 'class="note">Slide 2' in out and "&lt;ok&gt;" in out
    print("AUTO-TEST OK")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Script -> page de lecture plein écran pour le tournage.")
    p.add_argument("script", nargs="?")
    p.add_argument("-o", "--sortie")
    p.add_argument("--taille", type=int, default=46)
    p.add_argument("--test", action="store_true")
    a = p.parse_args()
    if a.test:
        auto_test()
    elif a.script:
        ecrire(a.script, a.sortie, a.taille)
    else:
        p.print_help()
