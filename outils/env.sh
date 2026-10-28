#!/usr/bin/env bash
# env.sh : environnement commun de toutes les tâches planifiées (modèle).
# A copier dans <vault>/scripts/env.sh. Chaque wrapper le source en premier :
#   . "$(dirname "${BASH_SOURCE[0]}")/env.sh"
# Il n'affiche jamais un secret. Il ne lance rien : il prépare seulement.
#
# Ce qu'il règle :
#   VAULT, SECRETS_DIR, JOURNAUX  : les chemins (déduits de l'emplacement du fichier)
#   PATH sûr                      : une tâche planifiée démarre avec un PATH presque vide
#   PYTHON                        : un vrai Python 3 (le faux python3 du Microsoft Store est écarté)
#   CLAUDE_BIN, MODELE_TACHE      : le binaire claude et le modèle économique des tâches
#   CLAUDE_CODE_OAUTH_TOKEN       : le jeton longue durée lu dans ~/.claude/secrets/claude-oauth-token.env
#   notifier                      : la fonction de notification (scripts/notify.sh)
#   claude_tache                  : un appel `claude -p` prêt pour une tâche sans fenêtre

VAULT="${VAULT:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
export VAULT
export SECRETS_DIR="${SECRETS_DIR:-$HOME/.claude/secrets}"
export JOURNAUX="${JOURNAUX:-$VAULT/outputs/cron-logs}"
mkdir -p "$JOURNAUX" 2>/dev/null || true

export PYTHONUTF8=1
export PYTHONIOENCODING=utf-8

# --- PATH sûr -------------------------------------------------------------
_env_ajoute_path() {
    [ -d "$1" ] || return 0
    case ":$PATH:" in *":$1:"*) ;; *) PATH="$1:$PATH" ;; esac
}
for _env_d in /usr/bin /bin /usr/local/bin /opt/homebrew/bin \
              "$HOME/bin" "$HOME/.local/bin" "$HOME/AppData/Roaming/npm" \
              "$HOME/AppData/Local/Microsoft/WinGet/Links" \
              "$HOME/AppData/Local/Programs/Python/Launcher" \
              "/c/Program Files/nodejs" "/c/Program Files/Git/usr/bin"; do
    _env_ajoute_path "$_env_d"
done
unset _env_d
export PATH

# --- Python ---------------------------------------------------------------
if [ -z "${PYTHON:-}" ]; then
    for _env_c in python3 python py; do
        if command -v "$_env_c" >/dev/null 2>&1 \
           && "$_env_c" -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)" >/dev/null 2>&1; then
            PYTHON="$_env_c"
            break
        fi
    done
    unset _env_c
fi
export PYTHON="${PYTHON:-python3}"

# --- Claude Code sans fenêtre ---------------------------------------------
if [ -z "${CLAUDE_BIN:-}" ]; then
    CLAUDE_BIN="$(command -v claude 2>/dev/null || true)"
fi
if [ -z "$CLAUDE_BIN" ]; then
    for _env_c in "$HOME"/AppData/Local/Microsoft/WinGet/Packages/Anthropic.ClaudeCode_*/claude.exe \
                  "$HOME/.local/bin/claude.exe" "$HOME/.local/bin/claude" \
                  /opt/homebrew/bin/claude /usr/local/bin/claude; do
        if [ -f "$_env_c" ]; then CLAUDE_BIN="$_env_c"; break; fi
    done
    unset _env_c
fi
export CLAUDE_BIN

# Modèle économique par défaut pour toutes les tâches. Une tâche précise peut le changer :
#   MODELE_TACHE=opus bash scripts/run-tache.sh relecture ...
export MODELE_TACHE="${MODELE_TACHE:-sonnet}"

# Jeton longue durée (créé une fois avec `claude setup-token` dans un terminal normal).
# Sans lui, `claude -p` lancé par une tâche planifiée finit en 401 quand le jeton court expire.
_env_jeton="$SECRETS_DIR/claude-oauth-token.env"
if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -f "$_env_jeton" ]; then
    CLAUDE_CODE_OAUTH_TOKEN="$(grep -m1 '^CLAUDE_CODE_OAUTH_TOKEN=' "$_env_jeton" | cut -d= -f2- | tr -d '\r"')"
    if [ -n "$CLAUDE_CODE_OAUTH_TOKEN" ]; then export CLAUDE_CODE_OAUTH_TOKEN; else unset CLAUDE_CODE_OAUTH_TOKEN; fi
fi
unset _env_jeton

# claude_tache "<consigne>" [options claude en plus]
# Exemple : claude_tache "Lis outputs/x.md et écris outputs/y.md" --allowedTools "Read,Write"
# Réglages allégés pour les tâches (plugins interactifs coupés) : scripts/reglages-tache.json s'il existe.
claude_tache() {
    if [ -z "$CLAUDE_BIN" ]; then
        echo "[env] claude introuvable : installe Claude Code ou règle CLAUDE_BIN" >&2
        return 127
    fi
    local consigne="$1"; shift
    local args=(-p "$consigne" --model "$MODELE_TACHE")
    if [ -f "$VAULT/scripts/reglages-tache.json" ]; then
        args+=(--settings "$VAULT/scripts/reglages-tache.json")
    fi
    ( cd "$VAULT" && "$CLAUDE_BIN" "${args[@]}" "$@" )
}

# Interrupteur général : un fichier .machine-en-pause à la racine du vault arrête toutes les tâches.
machine_en_pause() { [ -f "$VAULT/.machine-en-pause" ]; }

# --- Notifications ----------------------------------------------------------
if [ -f "$VAULT/scripts/notify.sh" ]; then
    . "$VAULT/scripts/notify.sh"
else
    notifier() { printf '%s [%s] %s | %s\n' "$(date +%T)" "$1" "$2" "${3:-}" >> "$JOURNAUX/resume-$(date +%F).log"; }
fi
