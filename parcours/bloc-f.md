---
title: "Bloc F : Automatisation"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc F : Automatisation et pilotage

Ce bloc fait tourner seul ce qui marche déjà à la main, prouve chaque matin que tout a tourné, et ne dérange l'utilisateur que quand il doit agir. Il installe aussi le rythme personnel : rapport du matin, scoreboard du dimanche, plan du lundi, journal du soir, revue du mois.

**Règle du bloc** : on automatise seulement une brique qui marche déjà à la main, une nouvelle automatisation par semaine, et rien ne part vers l'extérieur sans validation.

## Avant de commencer
- Bloc A fait au moins pour le vault, la mémoire et les sauvegardes (`sauvegardes-3-lieux`).
- Bloc B fait pour la brique « Claude sans fenêtre et jeton longue durée » et le format de sortie (TL;DR, AUTO, TOI, ALERTE).
- Windows : Git for Windows installé (`bash --version` dans PowerShell doit répondre). Mac : rien. Linux : `cron` actif.
- Python 3.8 ou plus (`python --version` ou `python3 --version`).

## Outils du bloc (dans `outils/`, à copier dans `<vault>/scripts/`)

| Fichier | Rôle |
|---|---|
| `env.sh` | environnement commun : PATH sûr, Python, claude, modèle économique, jeton, `notifier`, `claude_tache` |
| `run-tache.sh` | enveloppe de toute tâche : pause, verrou, journal daté, délai, état, notification selon le code |
| `planifier-tache.ps1` | enregistre une tâche Windows (Register-ScheduledTask, bash de Git), `-Simuler` pour voir sans créer |
| `planifier-tache.sh` | équivalent cron (Linux, Mac) ou launchd (Mac, `--launchd`), `--simuler` |
| `notify.sh`, `notify.py` | Telegram : `urgent` avec son, `hebdo` sans son, le reste au résumé du jour |
| `gardien.py` + `taches-attendues.exemple.json` | vérifie les preuves de chaque tâche, `--selftest` |
| `rapport-du-matin.py` | rassemble les faits de la nuit pour le rapport, `--selftest` |

## Ordre et dépendances

| # | Skill | Dépend de | Temps de l'utilisateur | Test binaire |
|---|---|---|---|---|
| 1 | `wrapper-de-tache` | blocs A et B | 3 min (créer le jeton) | `run-tache.sh essai bash -c 'exit 2'` écrit `"code": 2` et une ligne `[urgent]` |
| 2 | `taches-planifiees` | 1 | 2 min (répondre aux heures) | `.etat/<nom>.json` écrit depuis le planificateur avec `"code": 0` |
| 3 | `notifications-telegram` | 1 | 8 min (créer le bot) | l'essai `urgent` arrive sur le téléphone, un `warn` reste au résumé |
| 4 | `gardien` | 1, 2 (3 conseillé) | 5 min (dire les preuves) | une preuve retirée donne le code 1 et le nom de la tâche |
| 5 | `rapport-du-matin` | 1 à 4 | 2 min | le fichier du jour existe avant le réveil avec TL;DR, AUTO, TOI, ALERTE |
| 6 | `catalogue-automatisations` | 1 à 4 | 10 min par mois | la prochaine automatisation choisie marche déjà à la main |
| 7 | `taches-de-nuit` | 1 à 5, `board-textes` (bloc C) | 5 min | `outputs/nuit/<date>.md` existe et rien de non validé n'est publié |
| 8 | `scoreboard-et-plan-semaine` | 3, plan unique (bloc D) | 30 s le dimanche, 5 min le lundi | message du dimanche reçu, plan du lundi avec une action de vente |
| 9 | `journal-coach` | bloc A | 15 min le soir, quand il veut | nouvelle ligne datée au journal, une source du vault citée |
| 10 | `revue-de-vie` | 8, 9 | 1 h par mois | revue écrite avec un seul obstacle et une récompense nommée |

Les briques 9 et 10 ne demandent aucune tâche planifiée : elles peuvent commencer dès la première semaine, en parallèle du reste. Le catalogue (6) se relit chaque mois et choisit la suivante parmi : sauvegardes, jardinier, ingestion nocturne, idées, board de nuit, statistiques, publication, relances.

## Tests à sec (sans envoyer de message ni créer de vraie tâche)
Depuis la racine du vault, après avoir copié les outils :
```bash
python scripts/gardien.py --selftest
python scripts/rapport-du-matin.py --selftest
NOTIFY_SIMULER=1 bash scripts/run-tache.sh essai-ok echo bonjour
NOTIFY_SIMULER=1 bash scripts/run-tache.sh essai-humain bash -c 'exit 2'   # affiche le message urgent simulé
NOTIFY_SIMULER=1 bash scripts/notify.sh hebdo "Scoreboard" "3 chiffres ?"
bash scripts/planifier-tache.sh --nom gardien --commande "python3 scripts/gardien.py --notifier" --heure 11:00 --simuler
```
Windows, dans PowerShell :
```powershell
powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom gardien -Commande "python scripts/gardien.py --notifier" -Heure 11:00 -Simuler
```
Chaque commande doit finir sans erreur. Range ensuite les fichiers `essai-*` de `outputs/cron-logs/` dans une corbeille.

## Pièges du bloc (détail dans chaque skill)
- Sur Windows, l'app de bureau Claude est isolée : une installation faite depuis la session peut rester invisible des tâches. Installe et vérifie depuis une tâche planifiée lancée une fois.
- Un `claude -p` lancé par une tâche finit en 401 sans le jeton longue durée.
- Trop de notifications et plus personne ne lit, même les vraies pannes.
- Une tâche « réussie » peut n'avoir rien produit : le gardien vérifie les fichiers, pas les messages.

## Fin du bloc
Le bloc est fini quand le gardien prouve chaque jour toutes les tâches de `taches-attendues.json`, que le téléphone n'a sonné que pour des actions de l'utilisateur pendant une semaine, et que le rapport du matin est lu en début de session. Mets à jour `wiki/maps/parcours.md` et `log.md`.


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
