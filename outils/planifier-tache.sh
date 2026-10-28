#!/usr/bin/env bash
# planifier-tache.sh : équivalent Mac et Linux de planifier-tache.ps1.
# Ajoute, met à jour ou retire une tâche qui lance scripts/run-tache.sh. Idempotent.
#
# Usage :
#   bash scripts/planifier-tache.sh --nom jardinier --commande "python3 scripts/jardinier.py" --heure 03:00 [--simuler]
#   bash scripts/planifier-tache.sh --nom scoreboard --commande "bash scripts/scoreboard.sh" --heure 18:00 --jours 0
#   bash scripts/planifier-tache.sh --nom veille-compte --commande "python3 scripts/veille.py" --toutes-les-minutes 20
#   bash scripts/planifier-tache.sh --nom jardinier --supprimer
# Options :
#   --jours      jours au format cron (0 ou 7 = dimanche, 1 = lundi ; liste « 1,4 »). Vide = tous les jours.
#   --launchd    sur Mac : agent launchd au lieu de cron (rattrape une exécution ratée pendant la veille).
#   --simuler    affiche la ligne cron ou le plist, n'installe rien.
set -euo pipefail

ICI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VAULT="${VAULT:-$(cd "$ICI/.." && pwd)}"
NOM="" COMMANDE="" HEURE="03:00" JOURS="*" MINUTES=0 SIMULER=0 SUPPRIMER=0 LAUNCHD=0

while [ $# -gt 0 ]; do
    case "$1" in
        --nom) NOM="$2"; shift 2 ;;
        --commande) COMMANDE="$2"; shift 2 ;;
        --heure) HEURE="$2"; shift 2 ;;
        --jours) JOURS="$2"; shift 2 ;;
        --toutes-les-minutes) MINUTES="$2"; shift 2 ;;
        --launchd) LAUNCHD=1; shift ;;
        --simuler) SIMULER=1; shift ;;
        --supprimer) SUPPRIMER=1; shift ;;
        *) echo "Option inconnue : $1" >&2; exit 64 ;;
    esac
done

case "$NOM" in ''|*[!a-z0-9-]*) echo "--nom obligatoire (a-z, 0-9, -)" >&2; exit 64 ;; esac
case "$HEURE" in [0-2][0-9]:[0-5][0-9]) ;; *) echo "--heure au format HH:MM" >&2; exit 64 ;; esac
case "$JOURS" in '*'|[0-7]|[0-7],*) ;; *) echo "--jours au format cron (ex. 0 ou 1,4)" >&2; exit 64 ;; esac
H=$((10#${HEURE%%:*})); M=$((10#${HEURE##*:}))
MARQUE="# machine-claude:$NOM"
LABEL="com.machine-claude.$NOM"
PLIST="$HOME/Library/LaunchAgents/$LABEL.plist"

if [ "$SUPPRIMER" = 1 ]; then
    if [ "$SIMULER" = 1 ]; then echo "[simulation] retirerait $NOM (cron et launchd)"; exit 0; fi
    ( crontab -l 2>/dev/null | grep -v -- "${MARQUE}$" ) | crontab - || true
    if [ -f "$PLIST" ]; then launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true; rm -f "$PLIST"; fi
    echo "Tâche $NOM retirée."
    exit 0
fi

[ -n "$COMMANDE" ] || { echo "--commande obligatoire" >&2; exit 64; }
case "$COMMANDE" in *\"*|*\'*) echo "Pas de guillemets dans --commande : mets la logique dans un script." >&2; exit 64 ;; esac
[ -f "$VAULT/scripts/run-tache.sh" ] || { echo "scripts/run-tache.sh absent dans $VAULT" >&2; exit 1; }
LANCE="cd '$VAULT' && /bin/bash scripts/run-tache.sh $NOM $COMMANDE"

if [ "$LAUNCHD" = 1 ]; then
    if [ "$MINUTES" -gt 0 ]; then
        QUAND="<key>StartInterval</key><integer>$((MINUTES * 60))</integer>"
    else
        QUAND="<key>StartCalendarInterval</key><array>"
        if [ "$JOURS" = "*" ]; then
            QUAND="$QUAND<dict><key>Hour</key><integer>$H</integer><key>Minute</key><integer>$M</integer></dict>"
        else
            IFS=',' read -r -a LISTE <<< "$JOURS"
            for j in "${LISTE[@]}"; do
                QUAND="$QUAND<dict><key>Weekday</key><integer>$j</integer><key>Hour</key><integer>$H</integer><key>Minute</key><integer>$M</integer></dict>"
            done
        fi
        QUAND="$QUAND</array>"
    fi
    CONTENU="<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\"><dict>
<key>Label</key><string>$LABEL</string>
<key>ProgramArguments</key><array><string>/bin/bash</string><string>-c</string><string>${LANCE//&/&amp;}</string></array>
$QUAND
<key>StandardErrorPath</key><string>$VAULT/outputs/cron-logs/launchd-$NOM.err</string>
</dict></plist>"
    if [ "$SIMULER" = 1 ]; then echo "[simulation] $PLIST :"; echo "$CONTENU"; exit 0; fi
    mkdir -p "$(dirname "$PLIST")" "$VAULT/outputs/cron-logs"
    printf '%s\n' "$CONTENU" > "$PLIST"
    launchctl bootout "gui/$(id -u)" "$PLIST" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$PLIST"
    echo "Agent launchd $LABEL installé. Test immédiat : launchctl kickstart gui/$(id -u)/$LABEL"
    exit 0
fi

if [ "$MINUTES" -gt 0 ]; then
    LIGNE="*/$MINUTES * * * * $LANCE $MARQUE"
else
    LIGNE="$M $H * * $JOURS $LANCE $MARQUE"
fi
if [ "$SIMULER" = 1 ]; then echo "[simulation] ligne cron :"; echo "$LIGNE"; exit 0; fi
( crontab -l 2>/dev/null | grep -v -- "${MARQUE}$"; echo "$LIGNE" ) | crontab -
echo "Tâche $NOM installée dans cron. Vérifie : crontab -l | grep machine-claude"
