#!/usr/bin/env bash
# notify.sh : notifications de la machine. Source unique du transport (aucun script n'appelle Telegram ailleurs).
#
# Usage dans un script : . scripts/notify.sh ; notifier <niveau> "<titre>" "<message>"
# Usage direct          : bash scripts/notify.sh <niveau> "<titre>" "<message>"
#
# Niveaux :
#   urgent : part sur Telegram, avec son. Seulement quand l'humain doit agir
#            et que Claude ne peut pas régler seul (reconnecter un compte, sauvegarde morte).
#   hebdo  : part sur Telegram, sans son. Seulement les messages demandés par l'humain
#            (scoreboard du dimanche, plan du lundi).
#   warn, info, ok : jamais envoyés. Une ligne dans le résumé du jour
#            outputs/cron-logs/resume-AAAA-MM-JJ.log, lu par Claude en session et par le rapport du matin.
#   silent : rien du tout.
#
# Secret : ~/.claude/secrets/telegram.env avec deux lignes
#   TELEGRAM_BOT_TOKEN=...
#   TELEGRAM_CHAT_ID=...
# Test sans envoi : NOTIFY_SIMULER=1 bash scripts/notify.sh urgent "Titre" "Message"
#
# Une notification ratée ne casse jamais la tâche : notifier rend toujours 0.
# Un envoi perdu après un nouvel essai laisse une ligne [SENDFAIL] dans le résumé.

NOTIFY_SECRET="${NOTIFY_SECRET:-$HOME/.claude/secrets/telegram.env}"
if [ -z "${JOURNAUX:-}" ]; then
    JOURNAUX="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." 2>/dev/null && pwd)/outputs/cron-logs"
fi

_notify_resume() {
    local niveau="$1" titre="$2" msg="$3"
    mkdir -p "$JOURNAUX" 2>/dev/null || true
    printf '%s [%s] %s | %s\n' "$(date +%T)" "$niveau" "$titre" "${msg//$'\n'/ / }" \
        >> "$JOURNAUX/resume-$(date +%F).log" 2>/dev/null || true
}

_notify_telegram() {
    local texte="$1" silence="$2" niveau="$3" titre="$4" token chat resp essai
    if [ "${NOTIFY_SIMULER:-0}" = "1" ]; then
        printf '[SIMULATION %s, silencieux=%s]\n%s\n' "$niveau" "$silence" "$texte"
        return 0
    fi
    if [ ! -f "$NOTIFY_SECRET" ]; then
        _notify_resume "SENDFAIL" "$niveau $titre" "secret Telegram absent"
        return 0
    fi
    token="$(grep -m1 '^TELEGRAM_BOT_TOKEN=' "$NOTIFY_SECRET" | cut -d= -f2- | tr -d '\r"')"
    chat="$(grep -m1 '^TELEGRAM_CHAT_ID=' "$NOTIFY_SECRET" | cut -d= -f2- | tr -d '\r"')"
    if [ -z "$token" ] || [ -z "$chat" ]; then
        _notify_resume "SENDFAIL" "$niveau $titre" "secret Telegram incomplet"
        return 0
    fi
    # Le texte passe par l'entrée standard (text@-), jamais en argument :
    # curl.exe sous Windows abîme les accents et les emojis passés en argument.
    for essai in 1 2; do
        resp="$(printf '%s' "$texte" | curl -s -m 15 \
            --data-urlencode "chat_id=${chat}" \
            --data-urlencode "text@-" \
            --data-urlencode "disable_notification=${silence}" \
            --data-urlencode "disable_web_page_preview=true" \
            "https://api.telegram.org/bot${token}/sendMessage" 2>/dev/null)" || true
        case "$resp" in *'"ok":true'*) return 0 ;; esac
        [ "$essai" = "1" ] && sleep 3
    done
    _notify_resume "SENDFAIL" "$niveau $titre" "${resp:0:200}"
    return 0
}

notifier() {
    local niveau="${1:-info}" titre="${2:-}" msg="${3:-}" texte
    case "$niveau" in
        silent) return 0 ;;
        urgent) texte="URGENT : ${titre}" ;;
        hebdo)  texte="${titre}" ;;
        *)      _notify_resume "$niveau" "$titre" "$msg"; return 0 ;;
    esac
    [ -n "$msg" ] && texte="${texte}
${msg}"
    _notify_resume "$niveau" "$titre" "$msg"
    if [ "$niveau" = "urgent" ]; then
        _notify_telegram "$texte" false "$niveau" "$titre"
    else
        _notify_telegram "$texte" true "$niveau" "$titre"
    fi
    return 0
}

# Appel direct : bash notify.sh <niveau> "<titre>" "<message>"
if [ "${BASH_SOURCE[0]}" = "$0" ]; then
    if [ $# -lt 2 ]; then
        echo "Usage : bash notify.sh <urgent|hebdo|warn|info|ok|silent> \"<titre>\" \"<message>\"" >&2
        exit 64
    fi
    notifier "$@"
fi
