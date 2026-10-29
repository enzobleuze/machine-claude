---
title: "Bloc B : Méthode"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc B : la méthode et le moteur Claude Code

Le bloc B apprend à Claude à travailler comme un bras droit fiable : des règles courtes et toujours chargées, des rapports qu'on lit en une minute, une autonomie claire, des garde-fous qui ne s'oublient pas, des tâches qui ne se perdent plus, et un moteur qui tourne aussi sans fenêtre, la nuit, sans vider le forfait.

À avoir avant : le socle installé (`INSTALLER.md` : `CLAUDE.md` fusionné, hooks bibliothécaire, anti-suppression et liens wiki, commandes `/passation`, `/reprise`, `/fin`, `/cerveau`, `/idee`, `/vente`, `scripts/planche.py`) et un vault qui existe (bloc A, brique A2). Le bloc B se mène en parallèle du bloc A.

Règle de passage : une brique est cochée dans `wiki/maps/parcours.md` seulement quand son test binaire passe. Chaque skill commence par son interview. Ce que le socle fournit déjà ne se réécrit pas : les briques l'adaptent et l'approfondissent.

## Ordre d'installation

| # | Skill | Dépend de | Test qui prouve que c'est fait |
|:-|:-|:-|:-|
| 1 | `coeur-claude-md` | socle | `CLAUDE.md` sous 260 lignes, chaque map citée existe, une question touche une map et Claude dit la lire avant d'agir |
| 2 | `format-et-autonomie` | 1 | une tâche de 3 étapes validées s'enchaîne sans question et finit en TL;DR / AUTO / TOI / ALERTE ; une question simple reçoit 1 à 3 phrases |
| 3 | `passation-reprise` | 2, socle | après `/passation`, une conversation neuve avec `/reprise` seul donne le bon chantier et la bonne prochaine action |
| 4 | `taches-source-unique` | 2, 3 | « il faudra … un jour » crée une tâche ou une ligne de parking sans demande ; « on en est où ? » liste 5 vraies tâches |
| 5 | `routage-intentions` | 1 | `python scripts/verifier-routage.py` sort 0 ; 5 phrases habituelles sur 5 lancent la bonne chose |
| 6 | `hooks-ecrire` | 1 | chaque hook installé répond `ok` à `--test` ; l'action interdite est bloquée en vraie session |
| 7 | `settings-permissions` | 6 | le JSON se charge, une lecture et `git status` passent sans demande, la lecture d'un secret est refusée |
| 8 | `sous-agents-modeles` | 2, 7 | une question sur un gros dossier revient de l'agent `lecteur` en 3 lignes avec des chemins exacts |
| 9 | `creer-un-skill` | 1, 2 | `python scripts/verifier-skill.py <skill>` sort 0 ; la phrase habituelle déclenche le skill sans son nom |
| 10 | `ameliorer-les-skills` | 6, 9 | `lire-sessions.py usage` liste les usages ; un patch tiré d'une vraie correction est appliqué et la correction ne revient pas |
| 11 | `couts-et-limites` | 1, 8 | une planche contact annonce moins de jetons que les images séparées ; `wiki/maps/couts.md` daté |
| 12 | `claude-sans-fenetre` | 11 | `essai-claude-p` en mode `leger` affiche OK et sort 0, aussi lancé hors session |
| 13 | `connecteurs-mcp` | 7, 11 | chaque connecteur gardé a passé sa lecture d'essai ; `/mcp` ne montre rien hors de `wiki/maps/connecteurs.md` |
| 14 | `outils-locaux` | 11, 12 | `modele-local.py --dispo` sort 0 et la mesure de 20 cas est notée ; ou une ligne de commande refait un geste de navigateur en brouillon |
| 15 | `apps-locales-et-mods` | 11 | le moteur sort 0, le raccourci ouvre la page, une section cassée n'empêche pas les autres |

Raccourci pour un débutant : B1, B2, B3, B4, puis B11 et B12 le jour où une tâche doit tourner seule. B6 et B7 dès que Claude a fait une chose interdite ou que les demandes de permission agacent.

Liens avec les autres blocs : B12 prépare le jeton et l'appel que le bloc F enveloppe (`wrapper-de-tache`, `taches-planifiees`). B15 donne la méthode que le bloc D applique au cockpit (`cockpit-app`). B8 sert au bloc C (agents du comité, du board, du client idéal).

## Outils fournis (sans dépendance cachée, chacun avec son auto-test)

| Outil | Rôle | Commandes |
|:-|:-|:-|
| `hooks-ecrire/outils/gabarit-hook.js` | gabarit d'un hook de garde (bloque une écriture en zone protégée) | `--test`, sinon JSON sur l'entrée standard |
| `hooks-ecrire/outils/compteur-skills.js` | compte chaque lancement de skill ou commande dans `outputs/skill-usage/usage.jsonl` | `--test` |
| `hooks-ecrire/outils/memo-compactage.js` | mémo fidèle avant le résumé automatique, réinjecté après | `--test` |
| `settings-permissions/outils/settings.exemple.json` | exemple de permissions à fusionner | (fichier à adapter) |
| `sous-agents-modeles/outils/agent-modele.md` | agent `lecteur` en lecture seule | (fichier à copier dans `.claude/agents/`) |
| `creer-un-skill/outils/gabarit-SKILL.md` | gabarit d'un skill au format du repo | (fichier à copier) |
| `creer-un-skill/outils/verifier-skill.py` | vérifie le format d'un skill ou d'une commande | `<fichier ou dossier>`, `--test` |
| `ameliorer-les-skills/outils/lire-sessions.py` | bilan d'usage et extraits de transcriptions après chaque lancement | `usage`, `extraits <nom>`, `--test` |
| `routage-intentions/outils/verifier-routage.py` | liens morts et outils absents de la table de routage | `[routage.md]`, `--test` |
| `taches-source-unique/outils/gabarit-tache.md` | gabarit de tâche avec définition de fini | (texte à copier) |
| `taches-source-unique/outils/expliquer-linear.md` | visite guidée de Linear pour la personne : mots de l'écran, phrases à dire, exercice sur le téléphone | (texte à adapter) |
| `claude-sans-fenetre/outils/essai-claude-p.sh` et `.ps1` | essai d'un appel `claude -p` avec le jeton longue durée, coût affiché | `[leger]` |
| `outils-locaux/outils/modele-local.py` | appel d'un modèle local (Ollama) avec repli code 3 | `"consigne"`, `--dispo`, `--test` |
| `apps-locales-et-mods/outils/app-locale/` | moteur `construire-etat.py`, `serveur.py` (127.0.0.1), `index.html` | `--test`, `--state <fixture>` |
| `outils/planche.py` (socle) | planche contact d'images ou de vidéo | `<dossier|motif|vidéo> -o planche.jpg` |

## Test du bloc entier
Dans une conversation neuve, la personne dit seulement « on reprend ». Claude donne l'état en quatre cases, cite une vraie tâche, propose LA prochaine action, et l'enchaîne si elle est déjà décidée. Le soir, un appel `claude -p` lancé par une tâche d'essai répond sans erreur d'authentification.


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
