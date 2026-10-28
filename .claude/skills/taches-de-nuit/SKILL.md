---
name: taches-de-nuit
description: "Organise le travail de nuit de la machine : une seule session, peu d'agents, économe en jetons, une file d'attente traitée dans l'ordre, et un board de nuit qui valide les textes sans jamais publier ce qui n'est pas validé. Utiliser quand l'utilisateur dit « travaille pendant que je dors », « lance le board de nuit », « fais avancer la file cette nuit ». Pas pour une tâche courte et mécanique (utiliser wrapper-de-tache directement)."
---
# Tâches de nuit

## Pourquoi
Le système d'origine fait avancer beaucoup de choses la nuit : textes passés au board, idées classées, brouillons préparés. Deux erreurs l'ont façonné. Un soir, deux sessions lancées avant de dormir ont fait le même travail en parallèle : fichiers en double, jetons perdus, limite de la semaine atteinte au réveil. Et une nuit trop gourmande en sous-agents coûtait beaucoup pour le même résultat. Depuis : une seule session, presque pas d'agents, des scripts quand c'est possible, et rien de public sans validation.

## Prérequis
- wrapper-de-tache, taches-planifiees, gardien, notifications-telegram.
- La brique « Claude sans fenêtre et jeton longue durée » du bloc B.
- Pour le board de nuit : board-textes (bloc C) et sa porte de vérification.
- Coût : chaque texte traité est un appel `claude -p`. Compte ce que ça prend sur ta limite avant d'augmenter le nombre par nuit.

## Interview
Lis d'abord : `wiki/maps/automatisations.md`, la fin de `log.md`, `outputs/brief-matin/` (le dernier rapport), et la liste des files d'attente existantes (brouillons sans validation, idées à classer).
Puis demande :
1. « Qu'est-ce qui s'accumule et que tu aimerais retrouver avancé le matin ? »
2. « Combien d'éléments par nuit au minimum ? » (le système d'origine en traite une dizaine ; commence plus bas et monte.)
3. « Qu'est-ce que la nuit n'a jamais le droit de faire ? » Propose : publier, envoyer un message à quelqu'un, dépenser, trancher un désaccord de fond.
Range tout dans `wiki/maps/automatisations.md` (section « Nuit »).

## Construire
1. **Définir la file (Claude, 10 min).** Une file = un dossier et une règle d'ordre. Exemple : tout fichier `outputs/brouillons/*.md` sans fichier `<nom>.board.md` dont le verdict est VERT, du plus ancien au plus récent. Écris la règle en tête du script.
2. **Écrire le script de nuit (Claude, 20 min).** `scripts/nuit.py` prend la file, traite au plus N éléments, un `claude -p` par élément (modèle économique, délai par élément), puis relance la porte de vérification lui-même : un VERT que la porte refuse redevient INCOMPLET. Il écrit `outputs/nuit/<date>.md` (une ligne par élément : nom, verdict, durée) et sort avec la convention : `0` fini, `2` l'humain doit agir (un service à reconnecter), `3` quota ou limite d'usage, reprise la nuit suivante.
3. **Prompt d'un élément (Claude, 10 min).** Gabarit à adapter :
   ```
   Tu travailles seul, de nuit, sans humain. Applique le skill <nom-du-skill> au fichier <chemin>.
   Écris le résultat dans <chemin>.board.md avec une ligne « ## Verdict : VERT | À TRANCHER | INCOMPLET ».
   Interdits : publier, envoyer, supprimer, lancer des sous-agents.
   Si deux experts se contredisent sur le fond, écris « À TRANCHER » et la question en une phrase : l'humain choisira.
   ```
4. **Une seule session (Claude, 5 min).** En tête du script : si un autre travail de nuit tourne (verrou de `run-tache.sh`) ou si une session a déjà écrit le rapport du jour, ne pas recommencer le même élément. Le verrou de l'enveloppe empêche déjà deux nuits en même temps.
5. **Publication séparée (Claude, 10 min).** La tâche qui publie est une autre tâche. Elle ne prend que les éléments dont le verdict est VERT, avec la même empreinte du texte que celle validée (un hachage du fichier noté dans le board). Tout le reste reste en brouillon marqué « board non passé ».
6. **Planifier (Claude, 2 min).** Après la sauvegarde de nuit : `planifier-tache.ps1 -Nom nuit -Commande "python scripts/nuit.py" -Heure 05:00 -DureeMaxMinutes 300` (Mac et Linux : `planifier-tache.sh --nom nuit ...`). Mets `TACHE_TIMEOUT_MIN` assez haut pour toute la file. Ajoute la ligne au gardien avec `outputs/nuit/{date}.md` comme preuve.

## Test
Après une nuit, `outputs/nuit/<date>.md` liste au moins un élément traité ; aucun fichier publié ou envoyé n'a un verdict autre que VERT ; un second lancement le même soir écrit « doublon ignoré » dans le journal.

## Pièges vécus
- **Deux sessions de nuit en parallèle** : travail en double et limite de la semaine épuisée. Une seule session, et elle lit `log.md` et le rapport du matin avant de commencer.
- **Trop d'agents** : la nuit a le temps. Le travail seul et séquentiel coûte beaucoup moins pour le même résultat.
- **Un service externe qui refuse (quota, connexion)** : la nuit s'arrête proprement (code 3 ou 2) et reprend la suivante. Jamais de boucle d'essais qui brûle la limite.
- **Désaccord tranché la nuit** : un choix de fond appartient à l'humain. La nuit pose la question, elle ne répond pas.
- **Retouche après validation** : un texte modifié après son VERT doit repasser. L'empreinte du texte le garantit.
- **Une seule tâche lourde à la fois** : un rendu vidéo et un gros appel en même temps peuvent geler le PC.

## Entretien dans le temps
Le rapport du matin résume `outputs/nuit/<date>.md`. Quand une mesure montre qu'un réglage marche mieux, la nuit peut l'appliquer seule aux générateurs, à trois conditions : un seuil de preuve écrit, une ligne visible dans le rapport, un moyen simple d'annuler. Jamais sur les règles dures ni sur la porte du board.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Note en mémoire ce que la nuit n'a jamais le droit de faire, dans les mots de l'utilisateur. Propose ensuite rapport-du-matin.
