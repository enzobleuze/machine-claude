"""revue.py : l'app locale de revue des montages. La personne regarde chaque vidéo, pose une note à l'instant précis
(touche N), approuve (touche A), puis Claude lit toutes les notes d'un coup dans notes_a_traiter.md.
Aux couleurs de la charte (bibliotheque/marque/charte.css), sans rien envoyer sur Internet.

  python revue.py [dossier] [--port 8790] [--reseau]
  python revue.py --test

Le dossier est fouillé (sous-dossiers compris) : chaque .mp4, .mov ou .webm est une vidéo à revoir.
À côté d'une vidéo, facultatif :
  <nom>_sans_musique.mp4   bouton « Sans musique » (même vidéo, sans la musique)
  <nom>.evenements.json    frise des éléments (sous-titres, cartes, sons) : [{"type", "t0", "t1", "texte"}]
Écrit : <nom>.notes.json à côté de chaque vidéo, et notes_a_traiter.md à la racine du dossier.
--reseau : ouvre l'app aux appareils du même Wi-Fi (pour regarder sur le téléphone). Sinon, seul ce PC y accède.
Une vidéo approuvée sort de la liste (case « Tout voir » pour la revoir).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import socket
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ICI = Path(__file__).resolve().parent
sys.path.insert(0, str(ICI))
import commun as C  # noqa: E402

EXT = {".mp4", ".mov", ".webm", ".m4v"}
TYPES = {".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm"}

PAGE = r"""<!doctype html><html lang="fr" data-theme="sombre"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>Revue des montages</title>
<link rel="stylesheet" href="/charte.css"><style>
*{box-sizing:border-box}body{margin:0;background:var(--fond);color:var(--texte);font-family:var(--police-texte);
display:grid;grid-template-columns:minmax(220px,280px) 1fr minmax(260px,340px);height:100vh}
@media(max-width:900px){body{grid-template-columns:1fr;height:auto}}
aside,section{padding:16px;overflow:auto}aside{border-right:1px solid var(--ligne)}#droite{border-left:1px solid var(--ligne)}
h1,h2{font-family:var(--police-titres);font-size:18px;margin:0 0 12px}
.v{padding:10px;border-radius:var(--rayon);cursor:pointer;margin-bottom:6px;background:var(--surface)}
.v.actif{outline:2px solid var(--accent)}.v small{color:var(--texte-doux);display:block}
.ok{color:var(--ok)}main{padding:16px;display:flex;flex-direction:column;gap:10px;min-width:0}
#cadre{position:relative;align-self:center;max-height:70vh}video{max-height:70vh;max-width:100%;display:block;background:#000;border-radius:var(--rayon)}
#zones{position:absolute;inset:0;pointer-events:none;display:none}
#zones div{position:absolute;background:var(--erreur);opacity:.28}
#frise{position:relative;height:56px;background:var(--surface);border-radius:var(--rayon);cursor:pointer}
#frise i{position:absolute;height:12px;border-radius:3px;opacity:.85}#frise b{position:absolute;top:0;bottom:0;width:2px;background:var(--texte)}
#frise u{position:absolute;bottom:0;width:3px;height:18px;background:var(--alerte)}
.barre{display:flex;gap:8px;flex-wrap:wrap;align-items:center}
button{font:inherit;border:1px solid var(--ligne);background:var(--surface-2);color:var(--texte);padding:6px 10px;border-radius:var(--rayon);cursor:pointer}
button.p{background:var(--accent);color:var(--accent-texte);border-color:var(--accent)}button:focus-visible,textarea:focus-visible{outline:2px solid var(--accent)}
textarea{width:100%;min-height:64px;font:inherit;background:var(--surface);color:var(--texte);border:1px solid var(--ligne);border-radius:var(--rayon);padding:8px}
.n{background:var(--surface);border-radius:var(--rayon);padding:8px;margin-bottom:6px;cursor:pointer}.n em{color:var(--accent);font-style:normal;margin-right:6px}
.n button{float:right;padding:0 6px}kbd{background:var(--surface-2);border-radius:4px;padding:0 4px;font-size:12px}
#aide{color:var(--texte-doux);font-size:13px;line-height:1.7}
@media(prefers-reduced-motion:reduce){*{transition:none!important}}
</style></head><body>
<aside><h1>Vidéos</h1><label><input type="checkbox" id="tout"> Tout voir</label><div id="liste" style="margin-top:10px"></div>
<p><button id="theme">Thème clair ou sombre</button></p></aside>
<main><div id="cadre"><video id="vid" controls playsinline></video><div id="zones"><div style="top:0;left:0;right:0;height:13%"></div>
<div style="bottom:0;left:0;right:0;height:14%"></div><div style="top:40%;bottom:14%;right:0;width:13%"></div></div></div>
<div id="frise" title="Cliquer pour aller à cet instant"></div>
<div class="barre"><button id="sm" hidden>Sans musique</button><button id="appr" class="p">Approuver (A)</button>
<button id="cop">Copier les notes pour Claude (C)</button><span id="etat"></span></div>
<div id="aide"><kbd>Espace</kbd> lecture <kbd>J</kbd>/<kbd>L</kbd> 5 s <kbd>←</kbd>/<kbd>→</kbd> image par image
<kbd>N</kbd> note à cet instant <kbd>A</kbd> approuver <kbd>C</kbd> copier <kbd>S</kbd> zones cachées par les réseaux
<kbd>↑</kbd>/<kbd>↓</kbd> vidéo précédente ou suivante</div></main>
<section id="droite"><h2>Notes</h2><textarea id="txt" placeholder="Ta note à cet instant (Entrée pour enregistrer)"></textarea>
<div id="notes" style="margin-top:10px"></div></section>
<script>
const $=s=>document.querySelector(s),vid=$('#vid');let L=[],cur=null,N={notes:[]},EV=[];
const fmt=t=>{t=Math.max(0,t||0);return String(Math.floor(t/60)).padStart(2,'0')+':'+(t%60).toFixed(1).padStart(4,'0')};
const el=(tag,txt,cls)=>{const e=document.createElement(tag);if(txt!=null)e.textContent=txt;if(cls)e.className=cls;return e};
const COUL={'sous-titre':'--accent-2','chapitre':'--accent','citation':'--accent','liste':'--accent','texte':'--ok','plan':'--alerte','son':'--erreur','musique':'--texte-doux'};
try{document.documentElement.dataset.theme=localStorage.getItem('theme')||'sombre'}catch(e){}
$('#theme').onclick=()=>{const t=document.documentElement.dataset.theme==='sombre'?'clair':'sombre';document.documentElement.dataset.theme=t;try{localStorage.setItem('theme',t)}catch(e){}};
async function liste(){L=await (await fetch('/api/videos'+($('#tout').checked?'?tout=1':''))).json();const d=$('#liste');d.replaceChildren();
L.forEach((v,i)=>{const x=el('div',v.nom,'v'+(cur&&cur.id===v.id?' actif':''));x.append(el('small',(v.approuve?'approuvée · ':'')+v.notes+' note(s)',v.approuve?'ok':''));x.onclick=()=>ouvrir(i);d.append(x)});
if(!cur&&L.length)ouvrir(0)}
async function ouvrir(i){cur=L[i];vid.src='/video/'+cur.id;$('#sm').hidden=!cur.sans_musique;$('#sm').textContent='Sans musique';
N=await (await fetch('/api/notes/'+cur.id)).json();EV=cur.evenements||[];notes();liste();vid.onloadedmetadata=frise}
function frise(){const f=$('#frise'),d=vid.duration||1;f.replaceChildren();const types=[...new Set(EV.map(e=>e.type))];
EV.forEach(e=>{const b=el('i');b.style.left=(e.t0/d*100)+'%';b.style.width=Math.max(.3,(e.t1-e.t0)/d*100)+'%';b.style.top=(4+types.indexOf(e.type)%3*14)+'px';
b.style.background='var('+(COUL[e.type]||'--texte-doux')+')';b.title=e.type+' '+fmt(e.t0)+' : '+(e.texte||'');f.append(b)});
N.notes.forEach(n=>{const u=el('u');u.style.left=(n.t/d*100)+'%';u.title=n.texte;f.append(u)});const c=el('b');c.id='cur';f.append(c)}
vid.ontimeupdate=()=>{const c=$('#cur');if(c)c.style.left=(vid.currentTime/(vid.duration||1)*100)+'%'};
$('#frise').onclick=e=>{const r=e.currentTarget.getBoundingClientRect();vid.currentTime=(e.clientX-r.left)/r.width*(vid.duration||0)};
function notes(){const d=$('#notes');d.replaceChildren();$('#appr').textContent=N.approuve?'Approuvée (A pour annuler)':'Approuver (A)';
N.notes.forEach((n,k)=>{const x=el('div',null,'n');x.append(el('em',fmt(n.t)),el('span',n.texte));const s=el('button','×');s.title='Supprimer';
s.onclick=async ev=>{ev.stopPropagation();N=await post('/api/supprimer/'+cur.id,{index:k});notes();frise()};x.prepend(s);x.onclick=()=>{vid.currentTime=n.t};d.append(x)})}
async function post(u,b){const r=await fetch(u,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(b)});
if(!r.ok){$('#etat').textContent='Le serveur ne répond plus';throw r}$('#etat').textContent='';return r.json()}
async function noter(){const t=$('#txt').value.trim();if(!t||!cur)return;const at=vid.currentTime;
const e=EV.find(x=>x.t0<=at&&at<=x.t1&&x.type!=='sous-titre')||EV.find(x=>x.t0<=at&&at<=x.t1);
N=await post('/api/notes/'+cur.id,{t:at,texte:t,el:e?e.type+' « '+(e.texte||'').slice(0,40)+' »':''});$('#txt').value='';vid.focus();notes();frise();liste()}
async function approuver(){N=await post('/api/approuver/'+cur.id,{approuve:!N.approuve});notes();liste()}
async function copier(){const lignes=[];for(const v of L){const n=v.id===cur.id?N:await (await fetch('/api/notes/'+v.id)).json();
n.notes.forEach(x=>lignes.push('['+v.nom+'] '+fmt(x.t)+' '+x.texte+(x.el?' (élément : '+x.el+')':'')))}
try{await navigator.clipboard.writeText(lignes.join('\n'));$('#etat').textContent=lignes.length+' note(s) copiée(s)'}catch(e){$('#etat').textContent='Copie refusée : lis notes_a_traiter.md'}}
$('#appr').onclick=approuver;$('#cop').onclick=copier;$('#tout').onchange=liste;
$('#sm').onclick=()=>{const t=vid.currentTime,p=!vid.paused,s=vid.src.includes('sans=1');vid.src='/video/'+cur.id+(s?'':'?sans=1');
vid.currentTime=t;if(p)vid.play();$('#sm').textContent=s?'Sans musique':'Avec musique'};
$('#txt').onkeydown=e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();noter()}if(e.key==='Escape')vid.focus()};
addEventListener('keydown',e=>{if(e.target.tagName==='TEXTAREA'||!cur)return;const k=e.key.toLowerCase();
if(k===' '){e.preventDefault();vid.paused?vid.play():vid.pause()}else if(k==='j')vid.currentTime-=5;else if(k==='l')vid.currentTime+=5;
else if(k==='arrowleft'){e.preventDefault();vid.pause();vid.currentTime-=1/30}else if(k==='arrowright'){e.preventDefault();vid.pause();vid.currentTime+=1/30}
else if(k==='n'){e.preventDefault();vid.pause();$('#txt').focus()}else if(k==='a')approuver();else if(k==='c')copier();
else if(k==='s'){const z=$('#zones');z.style.display=z.style.display==='block'?'none':'block'}
else if(k==='arrowdown'||k==='arrowup'){e.preventDefault();const i=L.findIndex(v=>v.id===cur.id)+(k==='arrowdown'?1:-1);if(L[i])ouvrir(i)}});
liste();
</script></body></html>"""


class Revue:
    def __init__(self, racine: Path):
        self.racine = racine.resolve()
        self.verrou = threading.Lock()

    def videos(self) -> list[Path]:
        out = []
        for p in sorted(self.racine.rglob("*")):
            rel = p.relative_to(self.racine).parts
            if (p.suffix.lower() in EXT and p.is_file() and not p.stem.endswith("_sans_musique") and len(rel) <= 4
                    and not any(x.startswith(("_anciennes", ".")) for x in rel)):
                out.append(p)
        return out

    def notes_de(self, v: Path) -> dict:
        f = v.with_suffix(".notes.json")
        return json.loads(f.read_text(encoding="utf-8")) if f.exists() else {"approuve": False, "notes": []}

    def ecrire(self, v: Path, n: dict) -> dict:
        with self.verrou:
            v.with_suffix(".notes.json").write_text(json.dumps(n, ensure_ascii=False, indent=1), encoding="utf-8")
            l = ["# Notes à traiter", "", "Une section par vidéo non approuvée. Chaque note devient une règle écrite avant "
                 "la vidéo suivante.", ""]
            for x in self.videos():
                nx = self.notes_de(x)
                if nx["notes"] and not nx["approuve"]:
                    l.append(f"## {x.relative_to(self.racine).as_posix()}")
                    l += [f"- {int(k['t'] // 60):02d}:{k['t'] % 60:04.1f} : {k['texte']}" + (f" (élément : {k['el']})" if k.get("el") else "")
                          for k in sorted(nx["notes"], key=lambda k: k["t"])]
                    l.append("")
            (self.racine / "notes_a_traiter.md").write_text("\n".join(l), encoding="utf-8")
        return n

    def liste(self, tout: bool) -> list[dict]:
        out = []
        for i, v in enumerate(self.videos()):
            n = self.notes_de(v)
            if n["approuve"] and not tout:
                continue
            evf = v.with_suffix(".evenements.json")
            out.append({"id": i, "nom": v.relative_to(self.racine).as_posix(), "notes": len(n["notes"]), "approuve": n["approuve"],
                        "sans_musique": v.with_name(v.stem + "_sans_musique" + v.suffix).exists(),
                        "evenements": json.loads(evf.read_text(encoding="utf-8")) if evf.exists() else []})
        return out


def fabrique(app: Revue):
    class H(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def envoyer(self, code, corps: bytes, type_="application/json; charset=utf-8", extra=None):
            self.send_response(code)
            self.send_header("Content-Type", type_)
            self.send_header("Content-Length", str(len(corps)))
            self.send_header("Cache-Control", "no-store")
            for k, v in (extra or {}).items():
                self.send_header(k, v)
            self.end_headers()
            if self.command != "HEAD":
                self.wfile.write(corps)

        def video(self, chemin) -> Path | None:
            m = re.fullmatch(r"/(?:video|api/notes|api/approuver|api/supprimer)/(\d+)", chemin)
            vs = app.videos()
            return vs[int(m.group(1))] if m and int(m.group(1)) < len(vs) else None  # rien hors de la liste scannée

        def do_GET(self):
            u = urlparse(self.path)
            if u.path == "/":
                return self.envoyer(200, PAGE.encode(), "text/html; charset=utf-8")
            if u.path == "/charte.css":
                f = C.trouver("bibliotheque/marque/charte.css", app.racine) or C.trouver("bibliotheque/marque/charte.css")
                return self.envoyer(200, f.read_bytes() if f else C.css(C.SIMPLE).encode(), "text/css; charset=utf-8")
            if u.path == "/api/videos":
                return self.envoyer(200, json.dumps(app.liste("tout" in parse_qs(u.query))).encode())
            v = self.video(u.path)
            if not v:
                return self.envoyer(404, b"{}")
            if u.path.startswith("/api/notes/"):
                return self.envoyer(200, json.dumps(app.notes_de(v)).encode())
            if "sans=1" in u.query:
                v2 = v.with_name(v.stem + "_sans_musique" + v.suffix)
                v = v2 if v2.exists() else v
            taille = v.stat().st_size
            m = re.match(r"bytes=(\d*)-(\d*)", self.headers.get("Range", ""))
            a, b = (int(m.group(1) or 0), int(m.group(2) or taille - 1)) if m else (0, taille - 1)
            b = min(b, taille - 1, a + 8 * 1024 * 1024 - 1)  # morceaux de 8 Mo : le navigateur redemande la suite
            with open(v, "rb") as f:
                f.seek(a)
                corps = f.read(b - a + 1)
            extra = {"Accept-Ranges": "bytes"} | ({"Content-Range": f"bytes {a}-{b}/{taille}"} if m else {})
            self.envoyer(206 if m else 200, corps, TYPES.get(v.suffix.lower(), "video/mp4"), extra)

        def do_POST(self):
            v = self.video(urlparse(self.path).path)
            if not v:
                return self.envoyer(404, b"{}")
            try:
                d = json.loads(self.rfile.read(min(int(self.headers.get("Content-Length", 0)), 20000)) or b"{}")
            except ValueError:
                return self.envoyer(400, b"{}")
            n = app.notes_de(v)
            if self.path.startswith("/api/notes/"):
                texte = str(d.get("texte", "")).strip()[:2000]
                if not texte:
                    return self.envoyer(400, b"{}")
                n["notes"].append({"t": round(float(d.get("t", 0)), 2), "texte": texte, "el": str(d.get("el", ""))[:120],
                                   "date": time.strftime("%Y-%m-%d %H:%M")})
            elif self.path.startswith("/api/supprimer/"):
                k = int(d.get("index", -1))
                if 0 <= k < len(n["notes"]):
                    n["notes"].pop(k)
            else:
                n["approuve"] = bool(d.get("approuve"))
            self.envoyer(200, json.dumps(app.ecrire(v, n)).encode())
    return H


def lancer(dossier, port=8790, reseau=False, ouvrir=True):
    app = Revue(Path(dossier))
    srv = ThreadingHTTPServer(("0.0.0.0" if reseau else "127.0.0.1", port), fabrique(app))
    url = f"http://127.0.0.1:{srv.server_address[1]}/"
    if reseau:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
                s.connect(("10.255.255.255", 1))
                print(f"Sur le téléphone (même Wi-Fi) : http://{s.getsockname()[0]}:{srv.server_address[1]}/")
        except OSError:
            pass
    print(f"Revue : {url}  ({len(app.videos())} vidéos dans {app.racine}). Ctrl+C pour arrêter.")
    if ouvrir:
        webbrowser.open(url)
    return srv


def auto_test():
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "01-essai").mkdir()
        (d / "01-essai" / "reel.mp4").write_bytes(os.urandom(30000))
        (d / "01-essai" / "reel_sans_musique.mp4").write_bytes(b"x" * 100)
        (d / "01-essai" / "reel.evenements.json").write_text('[{"type":"texte","t0":1,"t1":2,"texte":"Un mot"}]', encoding="utf-8")
        (d / "_anciennes").mkdir()
        (d / "_anciennes" / "vieux.mp4").write_bytes(b"x")
        srv = lancer(d, 0, ouvrir=False)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        base = f"http://127.0.0.1:{srv.server_address[1]}"

        def get(u, h=None):
            with urllib.request.urlopen(urllib.request.Request(base + u, headers=h or {})) as r:
                return r.status, r.read()

        def post(u, b):
            q = urllib.request.Request(base + u, json.dumps(b).encode(), {"Content-Type": "application/json"})
            with urllib.request.urlopen(q) as r:
                return json.loads(r.read())
        try:
            assert b"--accent" in get("/charte.css")[1] and b"Revue des montages" in get("/")[1]
            l = json.loads(get("/api/videos")[1])
            assert [v["nom"] for v in l] == ["01-essai/reel.mp4"] and l[0]["sans_musique"] and l[0]["evenements"], l
            st, corps = get("/video/0", {"Range": "bytes=100-199"})
            assert st == 206 and len(corps) == 100
            assert get("/video/0?sans=1")[1] == b"x" * 100
            post("/api/notes/0", {"t": 12.34, "texte": "Le sous-titre cache la bouche", "el": "texte « Un mot »"})
            n = post("/api/notes/0", {"t": 3, "texte": "<b>coupe trop tôt</b>"})
            assert len(n["notes"]) == 2
            md = (d / "notes_a_traiter.md").read_text(encoding="utf-8")
            assert "## 01-essai/reel.mp4" in md and "00:12.3 : Le sous-titre" in md and md.index("00:03.0") < md.index("00:12.3")
            assert post("/api/supprimer/0", {"index": 1})["notes"][0]["t"] == 12.34
            post("/api/approuver/0", {"approuve": True})
            assert json.loads(get("/api/videos")[1]) == [] and len(json.loads(get("/api/videos?tout=1")[1])) == 1
            assert "## 01-essai" not in (d / "notes_a_traiter.md").read_text(encoding="utf-8")
            for mauvais in ("/video/9", "/video/../../x", "/api/notes/abc"):
                try:
                    get(mauvais)
                    raise AssertionError(mauvais)
                except urllib.error.HTTPError as e:
                    assert e.code == 404
        finally:
            srv.shutdown()
            srv.server_close()
    print("AUTO-TEST OK")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="App locale de revue des montages (notes horodatées).")
    ap.add_argument("dossier", nargs="?", default=".")
    ap.add_argument("--port", type=int, default=8790)
    ap.add_argument("--reseau", action="store_true")
    ap.add_argument("--test", action="store_true")
    a = ap.parse_args()
    if a.test:
        auto_test()
    else:
        s = lancer(a.dossier, a.port, a.reseau)
        try:
            s.serve_forever()
        except KeyboardInterrupt:
            s.server_close()
