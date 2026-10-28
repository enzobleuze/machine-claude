---
name: gardien
description: "Installe le gardien : un script quotidien qui vérifie que chaque tâche planifiée a vraiment tourné et que ses sorties existent, et qui signale celles qui manquent. Utiliser quand l'utilisateur dit « comment je sais que tout a tourné », « une tâche est morte sans que je le voie », « surveille la machine ». Pas pour réparer une tâche précise (ouvre son journal et répare-la en session)."
---
# Gardien

## Pourquoi
Dans le système d'origine, tout affichait vert alors qu'une sortie n'était pas partie, et c'est le fondateur qui le découvrait lui-même, plusieurs fois de suite. La leçon : le planificateur dit seulement qu'un programme s'est terminé. La preuve vient des fichiers produits (et, pour une publication, de la plateforme elle-même). Le gardien vérifie ces preuves chaque jour et parle une seule fois, avec la liste de ce qui manque.

## Prérequis
- wrapper-de-tache (les tâches écrivent `outputs/cron-logs/.etat/<nom>.json`).
- taches-planifiees (pour planifier le gardien lui-même).
- Python 3.8 ou plus, sans dépendance.

## Interview
Lis d'abord : la liste des tâches en place (Windows : `Get-ScheduledTask -TaskName "Machine *"` ; Mac et Linux : `crontab -l`), `wiki/maps/automatisations.md`, et pour chaque tâche son script, pour trouver le fichier qu'elle doit produire.
Puis demande seulement ce que tu ne peux pas déduire :
1. « Pour la tâche X, qu'est-ce qui prouve qu'elle a marché ? Un fichier, un post publié, un email parti ? »
2. « Si une tâche reste en panne plusieurs jours, au bout de combien de jours veux-tu être prévenu sur ton téléphone ? » (défaut 3).
Range les preuves dans `scripts/taches-attendues.json` et le délai dans `wiki/maps/automatisations.md`.

## Construire
1. **Copier (Claude, 2 min).** `outils/gardien.py` vers `scripts/gardien.py`, `outils/taches-attendues.exemple.json` vers `scripts/taches-attendues.json`.
2. **Remplir la liste (Claude, 15 min).** Une entrée par tâche : `nom` (celui passé à `run-tache.sh`), `toutes_les_heures` (26 pour une quotidienne, 170 pour une hebdomadaire : la fréquence plus une marge), `sorties` (chemins relatifs au vault, `{date}` = date de la dernière exécution, jokers permis). Une tâche mise de côté garde sa ligne avec `"active": false`.
3. **Auto-test (Claude, 1 min).** `python scripts/gardien.py --selftest` doit afficher « selftest gardien : OK ».
4. **Premier passage à la main (Claude, 3 min).** `python scripts/gardien.py`. Chaque ligne dit OK ou KO avec la raison. Répare ou corrige la liste jusqu'à ce que le résultat soit juste.
5. **Planifier (Claude, 2 min).** Après les tâches de nuit et avant le moment où l'utilisateur regarde son téléphone :
   - Windows : `powershell -ExecutionPolicy Bypass -File scripts\planifier-tache.ps1 -Nom gardien -Commande "python scripts/gardien.py --notifier" -Heure 11:00`
   - Mac et Linux : `bash scripts/planifier-tache.sh --nom gardien --commande "python3 scripts/gardien.py --notifier" --heure 11:00`
6. **Preuves en direct (Claude, 20 min, plus tard).** Pour ce qui sort de la machine (article publié, post programmé), ajoute à la tâche concernée un contrôle par l'API de la plateforme qui écrit un fichier preuve (`outputs/preuves/<nom>-{date}.json`). Le gardien vérifie ensuite ce fichier.

Ce que `--notifier` fait : une ligne `warn` au résumé du jour (lue par Claude en session et par le rapport du matin) ; un `urgent` sur le téléphone seulement quand une tâche est en panne depuis le nombre de jours choisi, car l'auto-réparation a échoué et personne n'a ouvert de session.

## Test
Renomme temporairement le fichier preuve d'une tâche. `python scripts/gardien.py` sort avec le code 1 et nomme cette tâche avec « introuvable ». Remets le fichier : code 0.

## Pièges vécus
- **Crier au loup** : une tâche longue encore en cours apparaissait en panne. Le gardien lit le verrou de `run-tache.sh` et la marque « en cours ». Planifie-le assez tard après les tâches de nuit.
- **Doublons d'alerte** : le gardien et une autre vérification signalaient la même panne. Une panne = un seul message, celui du gardien.
- **Tâche perdue lors d'un changement de PC** : le gardien la voit comme « trop vieille » dès le lendemain, à condition qu'elle soit dans la liste. D'où l'étape 6 de taches-planifiees.
- **Logs seuls** : un journal peut dire « fini » pour une publication refusée par la plateforme. Pour tout ce qui sort, la preuve vient de la plateforme.

## Entretien dans le temps
Chaque nouvelle tâche ajoute sa ligne dans `taches-attendues.json` le jour même. Le rapport du matin affiche le verdict du gardien. Une fois par mois, relis les tâches `"active": false` et supprime celles qui ne reviendront pas.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire le délai d'escalade choisi. Propose ensuite notifications-telegram si ce n'est pas fait, sinon rapport-du-matin.
