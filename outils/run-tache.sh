#!/usr/bin/env bash
# run-tache.sh : l'enveloppe de toute tâche planifiée.
#
# Usage   : bash scripts/run-tache.sh <nom-tache> <commande> [arguments...]
# Exemple : bash scripts/run-tache.sh jardinier python scripts/jardinier.py --nuit
#
# Ce qu'il fait, dans l'ordre :
#   1. charge scripts/env.sh (PATH sûr, Python, claude, jeton, notifier)
#   2. sort sans rien faire si .machine-en-pause existe à la racine du vault
#   3. pose un verrou : si la même tâche tourne déjà, le doublon s'arrête (un verrou périmé est repris)
#   4. journal daté : outputs/cron-logs/<nom>-AAAA-MM-JJ.log (tout stdout et stderr)
#   5. délai maximum : TACHE_TIMEOUT_MIN (60 par défaut)
#   6. état pour le gardien : outputs/cron-logs/.etat/<nom>.json (début, fin, code)
#   7. notification selon le code de sortie de la commande
#
# Convention des codes de sortie (à respecter dans tes scripts) :
#   0  fait
#   2  l'humain doit agir (reconnexion, mot de passe, paiement) : urgent sur Telegram
#   3  arrêt propre qui reprendra seul (quota, limite d'usage) : résumé seulement
#   124 délai dépassé ; autre code = panne : résumé seulement (Claude la répare en session)

set -uo pipefail
ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
# shellcheck source=/dev/null
. "$ICI/env.sh" || { echo "run-tache : env.sh introuvable à côté du script" >&2; exit 1; }

NOM="${1:-}"
[ $# -gt 0 ] && shift
if [ -z "$NOM" ] || [ $# -eq 0 ]; then
    echo "Usage : bash run-tache.sh <nom-tache> <commande> [arguments...]" >&2
    exit 64
fi
case "$NOM" in
    *[!a-z0-9-]*) echo "run-tache : nom « $NOM » invalide (lettres minuscules, chiffres, tirets)" >&2; exit 64 ;;
esac

JOUR="$(date +%F)"
LOG="$JOURNAUX/$NOM-$JOUR.log"
ETAT_DIR="$JOURNAUX/.etat"
VERROUS="$JOURNAUX/.verrous"
mkdir -p "$ETAT_DIR" "$VERROUS"
horodate() { date '+%F %T'; }
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null || echo 0; }

if machine_en_pause; then
    echo "[$(horodate)] $NOM : machine en pause (.machine-en-pause), rien lancé" >> "$LOG"
    exit 0
fi

# --- Verrou anti-doublon (mkdir est atomique sur tous les systèmes) ---
VERROU="$VERROUS/$NOM.lock"
if ! mkdir "$VERROU" 2>/dev/null; then
    ancien_pid="$(cat "$VERROU/pid" 2>/dev/null || true)"
    age_min=$(( ( $(date +%s) - $(mtime "$VERROU") ) / 60 ))
    if [ -n "$ancien_pid" ] && kill -0 "$ancien_pid" 2>/dev/null && [ "$age_min" -lt "${VERROU_MAX_MIN:-240}" ]; then
        echo "[$(horodate)] $NOM : déjà en cours (pid $ancien_pid depuis $age_min min), doublon ignoré" >> "$LOG"
        exit 0
    fi
    echo "[$(horodate)] $NOM : verrou périmé repris (pid ${ancien_pid:-?}, $age_min min)" >> "$LOG"
    rm -rf "$VERROU"
    mkdir "$VERROU" || { echo "run-tache : verrou impossible" >&2; exit 1; }
fi
echo $$ > "$VERROU/pid"
trap 'rm -rf "$VERROU"' EXIT

# --- Exécution ---
DEBUT="$(horodate)"
echo "=== $NOM début $DEBUT : $* ===" >> "$LOG"
LIMITE="${TACHE_TIMEOUT_MIN:-60}"
if command -v timeout >/dev/null 2>&1; then
    timeout "${LIMITE}m" "$@" >> "$LOG" 2>&1
elif command -v gtimeout >/dev/null 2>&1; then
    gtimeout "${LIMITE}m" "$@" >> "$LOG" 2>&1
else
    "$@" >> "$LOG" 2>&1
fi
RC=$?
FIN="$(horodate)"
[ "$RC" -eq 124 ] && echo "[$FIN] $NOM : délai de $LIMITE min dépassé, arrêt forcé" >> "$LOG"
echo "=== $NOM fin $FIN (code $RC) ===" >> "$LOG"

printf '{"nom": "%s", "debut": "%s", "fin": "%s", "code": %d, "journal": "%s"}\n' \
    "$NOM" "$DEBUT" "$FIN" "$RC" "outputs/cron-logs/$NOM-$JOUR.log" > "$ETAT_DIR/$NOM.json"

# --- Notification (la règle : urgent seulement si l'humain doit agir) ---
DERNIERES="$(grep -v '^===' "$LOG" | tail -3 | tr '\n' ' ' | cut -c1-300)"
case "$RC" in
    0) notifier ok "$NOM" "fait" ;;
    2) notifier urgent "$NOM : ton action est requise" "$DERNIERES" ;;
    3) notifier info "$NOM : arrêt propre, reprise au prochain passage" "$DERNIERES"; RC=0 ;;
    *) notifier warn "$NOM en échec (code $RC)" "Journal : outputs/cron-logs/$NOM-$JOUR.log. $DERNIERES" ;;
esac
exit "$RC"
