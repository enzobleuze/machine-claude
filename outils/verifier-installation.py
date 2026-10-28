"""verifier-installation.py : contrôle unique de l'installation Machine Claude (PASS ou ÉCHEC).

Usage, depuis la racine du vault (marche dans PowerShell, Git Bash, Terminal Mac) :
    python scripts/verifier-installation.py
    python scripts/verifier-installation.py --test     (auto-test sur un faux vault)
Sortie 0 si tout passe, 1 sinon. Ne modifie rien dans le vault.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def hook(vault: Path, nom: str, payload: dict | None) -> subprocess.CompletedProcess:
    entree = json.dumps(payload) if payload is not None else ""
    return subprocess.run(["node", str(vault / ".claude" / "hooks" / nom)], input=entree, text=True,
                          capture_output=True, timeout=20, cwd=vault, env={**__import__("os").environ, "CLAUDE_PROJECT_DIR": str(vault)})


def controles(vault: Path) -> list[tuple[str, bool, str]]:
    r: list[tuple[str, bool, str]] = []
    node = shutil.which("node") is not None
    r.append(("Node installé", node, "installe Node LTS (winget install OpenJS.NodeJS.LTS, ou nodejs.org)"))
    claude_md = vault / "CLAUDE.md"
    txt = claude_md.read_text(encoding="utf-8") if claude_md.exists() else ""
    r.append(("CLAUDE.md présent, sous 260 lignes, sans {{...}}", bool(txt) and txt.count("\n") < 260 and "{{" not in txt,
              "refais l'étape « Installer le cœur »"))
    r.append(("index.md présent", (vault / "index.md").exists(), "lance scripts/creer-vault.py"))
    parcours = vault / "wiki" / "maps" / "parcours.md"
    p = parcours.read_text(encoding="utf-8") if parcours.exists() else ""
    r.append(("parcours.md présent et daté", bool(p) and "AAAA-MM-JJ" not in p, "copie parcours-modele.md et remplace les dates"))
    try:
        s = json.loads((vault / ".claude" / "settings.json").read_text(encoding="utf-8"))
        cmds = json.dumps(s.get("hooks", {}))
        ok = all(h in cmds for h in ("bibliothecaire-activate.js", "anti-suppression.js", "liens-wiki-check.js"))
    except (OSError, ValueError):
        ok = False
    r.append(("settings.json valide avec les 3 hooks", ok, "fusionne .claude/settings.hooks.json dans .claude/settings.json"))
    if node:
        rm = "r" + "m -rf wiki"
        r.append(("hook anti-suppression bloque", hook(vault, "anti-suppression.js", {"tool_input": {"command": rm}}).returncode == 2, "recopie le hook"))
        r.append(("hook anti-suppression laisse passer", hook(vault, "anti-suppression.js", {"tool_input": {"command": "ls"}}).returncode == 0, "recopie le hook"))
        b = hook(vault, "bibliothecaire-activate.js", None)
        r.append(("hook bibliothécaire injecte le mode", "BIBLIOTH" in b.stdout.upper(), "copie .claude/skills/bibliothecaire/"))
        with tempfile.TemporaryDirectory() as t:
            page = Path(t) / "wiki" / "essai.md"
            page.parent.mkdir()
            page.write_text("# essai\n", encoding="utf-8")
            res = hook(vault, "liens-wiki-check.js", {"tool_name": "Write", "tool_input": {"file_path": str(page)}})
            r.append(("hook des 3 liens bloque une page sans lien", res.returncode == 2, "recopie le hook"))
    cerveau = vault / "scripts" / "cerveau.py"
    ok = cerveau.exists() and subprocess.run([sys.executable, str(cerveau), "test", "--top", "1"], capture_output=True,
                                             text=True, timeout=600, cwd=vault).returncode in (0, 1)
    r.append(("recherche (scripts/cerveau.py) répond", ok, "copie outils/cerveau.py vers scripts/"))
    return r


def afficher(r: list[tuple[str, bool, str]]) -> int:
    for nom, ok, aide in r:
        print(("OK     " if ok else "ÉCHEC  ") + nom + ("" if ok else f"  -> {aide}"))
    echecs = sum(not ok for _, ok, _ in r)
    print("PASS" if not echecs else f"ÉCHEC : {echecs} contrôle(s)")
    return 0 if not echecs else 1


def auto_test() -> int:
    kit = Path(__file__).resolve().parent.parent
    if not (kit / ".claude" / "hooks").exists():
        print("auto-test : à lancer depuis le kit (outils/)")
        return 1
    with tempfile.TemporaryDirectory() as t:
        v = Path(t)
        assert afficher(controles(v)) == 1  # vault vide : échec attendu
        shutil.copytree(kit / ".claude", v / ".claude")
        (v / ".claude" / "settings.json").write_text((kit / ".claude" / "settings.hooks.json").read_text(encoding="utf-8"), encoding="utf-8")
        (v / "scripts").mkdir()
        shutil.copy(kit / "outils" / "cerveau.py", v / "scripts" / "cerveau.py")
        (v / "wiki" / "maps").mkdir(parents=True)
        (v / "wiki" / "maps" / "parcours.md").write_text("# Parcours 2026-01-01\n", encoding="utf-8")
        (v / "index.md").write_text("# Index\n", encoding="utf-8")
        (v / "CLAUDE.md").write_text("# Règles\n", encoding="utf-8")
        assert afficher(controles(v)) == 0, "le vault complet devrait passer"
    print("auto-test OK")
    return 0


if __name__ == "__main__":
    if "--test" in sys.argv:
        sys.exit(auto_test())
    sys.exit(afficher(controles(Path.cwd())))
