---
name: taches-planifiees
description: "Installe les tâches planifiées de la machine (Planificateur de tâches Windows avec le bash de Git, cron ou launchd sur Mac et Linux) et la règle pour en ajouter une. Utiliser quand l'utilisateur dit « fais tourner ça tout seul », « programme une tâche », « chaque nuit », « tous les lundis ». Pas pour écrire le script de la tâche lui-même (utiliser wrapper-de-tache) ni pour choisir quoi automatiser (utiliser catalogue-automatisations)."
---
# Tâches planifiées

## Pourquoi
Dans le système d'origine, des dizaines de tâches tournent seules : sauvegardes, jardinier, ingestion, rapport du matin. Au début, chaque tâche était créée à la main avec des réglages différents. Certaines ne rattrapaient pas une exécution ratée quand le PC dormait, d'autres tournaient en double, et une tâche a été perdue lors d'un changement de PC sans que personne ne le voie. Un seul script d'enregistrement, idempotent, avec les mêmes réglages pour tout, a réglé ça.

## Prérequis
- wrapper-de-tache (les outils `env.sh` et `run-tache.sh` copiés dans `scripts/`).
- Windows : Git for Windows installé (il fournit `bash.exe`). Mac : rien. Linux : `cron` actif.
- La brique « Claude sans fenêtre et jeton longue durée » du bloc B si la tâche appelle `claude -p`.
- Coût : zéro. Une tâche qui appelle `claude -p` consomme la limite de l'abonnement ou du crédit API.

## Interview
Lis d'abord : `wiki/maps/parcours.md` (ce qui marche déjà à la main), `scripts/taches-attendues.json` s'il existe, et la liste des tâches déjà en place (Windows : `Get-ScheduledTask -TaskName "Machine *"` ; Mac et Linux : `crontab -l | grep machine-claude`).
Puis demande, une question à la fois :
1. « Ton ordinateur reste-t-il allumé la nuit, ou il dort ou s'éteint ? » (décide `-Reveiller` et les heures).
2. « À quelle heure tu te lèves et tu te couches, à peu près ? » (les tâches lourdes tournent quand tu dors, le rapport du matin juste avant ton réveil).
3. « Quel préfixe veux-tu pour reconnaître tes tâches dans la liste ? » (défaut `Machine`).
Range les réponses dans `wiki/maps/automatisations.md` (section « Réglages »), crée la page si elle n'existe pas.

## Construire
1. **Copier les outils (Claude, 2 min).** Copie `outils/planifier-tache.ps1` et `outils/planifier-tache.sh` dans `<vault>/scripts/`. Fichier produit : les deux scripts.
2. **Choisir les heures (Claude, 5 min).** Écris dans `wiki/maps/automatisations.md` un tableau « heure, tâche, durée attendue ». Règle : une seule tâche lourde à la fois (un rendu, un gros appel `claude -p`), espacées d'au moins 20 minutes. La sauvegarde passe avant les tâches qui écrivent beaucoup.
3. **Simuler (Claude, 2 min).**
   - Windows : `powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom gardien -Commande "python scripts/gardien.py --notifier" -Heure 11:00 -Simuler`
   - Mac et Linux : `bash scripts/planifier-tache.sh --nom gardien --commande "python3 scripts/gardien.py --notifier" --heure 11:00 --simuler`
   Montre la sortie à l'utilisateur en une phrase.
4. **Enregistrer (Claude, 2 min).** Même commande sans `-Simuler`. Sur Mac, préfère `--launchd` : launchd rattrape une exécution ratée pendant la veille, cron non. Relancer la commande met la tâche à jour, sans doublon.
5. **Tester dans le vrai contexte (Claude, 5 min).** Windows : ajoute `-LancerMaintenant`. Mac : `launchctl kickstart gui/$(id -u)/com.machine-claude.<nom>`. Linux : attends la minute suivante avec `--heure` réglée sur maintenant plus 2 minutes. Puis lis `outputs/cron-logs/.etat/<nom>.json`.
6. **Déclarer la tâche au gardien (Claude, 2 min).** Ajoute une ligne dans `scripts/taches-attendues.json` (voir gardien). Une tâche que le gardien ne connaît pas peut mourir en silence.

Options utiles : `-Jours Sunday` (Mac et Linux `--jours 0`), `-ToutesLesMinutes 20`, `-DureeMaxMinutes 30`, `-Supprimer`.

## Test
`outputs/cron-logs/.etat/<nom>.json` existe, a été écrit par l'exécution lancée depuis le planificateur (pas depuis la session), et contient `"code": 0`.

## Pièges vécus
- **La session ment sur Windows.** L'app de bureau Claude est un paquet isolé : ce qu'elle installe dans `AppData` (navigateurs Playwright, config rclone) peut rester invisible des tâches planifiées. Le système d'origine a perdu deux semaines de sauvegardes externes comme ça. Toute installation destinée aux tâches se fait depuis une tâche planifiée lancée une fois (`-LancerMaintenant`), puis se vérifie depuis une tâche.
- **PC en veille = tâche ratée.** Code `0x800710E0` dans le planificateur. Le réglage « rattraper au réveil » (inclus par défaut) suffit souvent. Sinon `-Reveiller`, et autorise les minuteurs de réveil dans les options d'alimentation de Windows.
- **`schtasks /Change` ne change pas le type d'horaire** (quotidien vers hebdo). Relance `planifier-tache.ps1` avec les nouveaux réglages : il remplace la tâche.
- **Guillemets dans la commande** : source d'erreurs d'échappement sans fin. Le script les refuse. Mets la logique dans un script et appelle ce script.
- **Fichiers `.ps1` avec accents** : PowerShell 5.1 les lit mal sans BOM. Garde les `.ps1` en ASCII.
- **Session fermée** : la tâche tourne avec ta session Windows ouverte (verrouillée suffit). Si tu te déconnectes le soir, change le compte de la tâche dans l'interface du planificateur.
- **Changement de PC** : les tâches ne suivent pas le vault. Garde la liste des commandes d'enregistrement dans `wiki/maps/automatisations.md` pour tout recréer en une fois.

## Entretien dans le temps
Le gardien vérifie chaque jour que chaque tâche a tourné. Une fois par mois, compare la liste du planificateur avec `scripts/taches-attendues.json` : une tâche dans l'un et pas dans l'autre est soit morte, soit invisible.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Ajoute en mémoire les heures de sommeil de l'utilisateur si elles sont nouvelles. Propose ensuite wrapper-de-tache si ce n'est pas fait, sinon gardien.
