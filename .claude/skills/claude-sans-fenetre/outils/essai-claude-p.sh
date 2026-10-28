#!/usr/bin/env bash
# Essai d'un appel Claude sans fenêtre (claude -p), comme le ferait une tâche de nuit.
# Lit le jeton longue durée, appelle Claude avec une consigne minuscule, affiche le coût.
#
#   bash scripts/essai-claude-p.sh            appel normal (cœur, mémoire, connecteurs chargés)
#   bash scripts/essai-claude-p.sh leger      appel allégé (sans connecteurs, et sans CLAUDE.md si ta version a --safe-mode)
#
# Sort 0 si Claude a répondu, 1 sinon (avec la raison). Ne montre jamais le jeton.
# Windows : lance-le dans Git Bash. Mac et Linux : bash.
set -u

SECRET="${HOME}/.claude/secrets/claude-oauth-token.env"
MODE="${1:-normal}"

if [ -z "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] && [ -f "$SECRET" ]; then
  tok=$(grep '^CLAUDE_CODE_OAUTH_TOKEN=' "$SECRET" | cut -d= -f2- | tr -d '\r"')
  [ -n "$tok" ] && export CLAUDE_CODE_OAUTH_TOKEN="$tok"
fi
[ -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" ] || echo "ATTENTION : pas de jeton longue durée trouvé ($SECRET). L'appel utilisera la connexion de l'app, qui peut expirer la nuit."
if [ -n "${ANTHROPIC_API_KEY:-}" ]; then
  echo "ATTENTION : ANTHROPIC_API_KEY est définie. Claude peut la préférer à ton abonnement et te facturer au tarif public."
fi

command -v claude >/dev/null 2>&1 || { echo "ÉCHEC : la commande claude est introuvable dans le PATH."; exit 1; }

OPTS=(-p "Réponds seulement : ok" --output-format json --model "${MODELE_TACHE:-sonnet}")
if [ "$MODE" = "leger" ]; then
  OPTS+=(--strict-mcp-config)
  if claude --help 2>/dev/null | grep -q -- '--safe-mode'; then OPTS+=(--safe-mode); fi
fi

debut=$(date +%s)
sortie=$(claude "${OPTS[@]}" 2>&1)
code=$?
duree=$(( $(date +%s) - debut ))

if [ $code -ne 0 ] || ! printf '%s' "$sortie" | grep -q '"result"'; then
  echo "ÉCHEC (code $code, ${duree} s) :"
  printf '%s\n' "$sortie" | head -5
  printf '%s' "$sortie" | grep -qi -e 'not logged in' -e '401' -e 'authentication' \
    && echo "Piste : jeton absent, expiré ou refusé. Refais claude setup-token dans un terminal normal."
  printf '%s' "$sortie" | grep -qi 'limit' && echo "Piste : limite de l'abonnement atteinte. Réessaie après la remise à zéro."
  exit 1
fi

# Extraction sans dépendance : python s'il est là, sinon la sortie brute.
if command -v python >/dev/null 2>&1 || command -v python3 >/dev/null 2>&1; then
  PY=$(command -v python || command -v python3)
  printf '%s' "$sortie" | "$PY" -c '
import json, sys
d = json.loads(sys.stdin.read())
u = d.get("usage") or {}
print("OK :", str(d.get("result", "")).strip()[:40])
print("Jetons écrits en cache :", u.get("cache_creation_input_tokens"), "| relus :", u.get("cache_read_input_tokens"))
print("Équivalent tarif public (indicatif sur abonnement) :", d.get("total_cost_usd"), "$")
'
else
  echo "OK : $sortie" | head -c 300
fi
echo "Mode : $MODE | durée : ${duree} s"
