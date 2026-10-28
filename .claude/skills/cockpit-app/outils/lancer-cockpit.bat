@echo off
rem Raccourci bureau Windows du Cockpit. Claude remplace CHEMIN_DU_VAULT par le chemin réel.
set COCKPIT_VAULT=CHEMIN_DU_VAULT
cd /d "%COCKPIT_VAULT%"
python -X utf8 scripts\cockpit\cockpit_serveur.py
if errorlevel 1 pause
