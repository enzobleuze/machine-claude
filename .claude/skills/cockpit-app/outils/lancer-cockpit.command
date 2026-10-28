#!/bin/sh
# Raccourci Mac (double-clic) ou Linux du Cockpit. Claude remplace CHEMIN_DU_VAULT puis lance : chmod +x lancer-cockpit.command
export COCKPIT_VAULT="CHEMIN_DU_VAULT"
cd "$COCKPIT_VAULT" || exit 1
python3 -X utf8 scripts/cockpit/cockpit_serveur.py
