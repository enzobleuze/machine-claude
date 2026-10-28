---
name: passation-reprise
description: "Installe et règle la continuité entre conversations : quand faire une passation, comment la reprise lit l'état, le mémo de compactage, les gestes de session (revenir en arrière, compacter avec consigne). Utiliser quand l'utilisateur dit « je dois tout réexpliquer à chaque fois », « Claude a oublié ce qu'on avait décidé », « la conversation est trop longue », « comment je reprends demain ». Pas pour faire une passation tout de suite (lancer /passation) ni pour reprendre (lancer /reprise)."
---
# Passation et reprise

## Pourquoi
Dans le système d'origine, la première plainte relevée en relisant des dizaines de sessions était de devoir réexpliquer où on en était à chaque ouverture. La commande de reprise a inversé la charge : c'est Claude qui dit l'état, ce qui a tourné seul, et la prochaine action. La passation fige un chantier dans un fichier court quand on change de sujet. Un essai de passation forcée au-delà d'une certaine taille de conversation a ensuite été retiré : l'entrepreneur préférait de longues conversations autonomes, et les rappels le coupaient. La règle finale : outil à la demande, proposé en une ligne seulement au changement de chantier.

## Prérequis
- Le socle : commandes `/passation`, `/reprise` et `/fin` dans `.claude/commands/`.
- format-et-autonomie (le format TL;DR, AUTO, TOI, ALERTE).
- taches-source-unique conseillé (la reprise lit les tâches), sinon la reprise lit seulement le log.
- Aucun coût.

## Interview
Lis d'abord : les trois commandes du socle, `log.md` (existe-t-il, est-il tenu ?), `outputs/passation/`, le plan (`wiki/strategie/plan.md` si le bloc D est fait), la mémoire.

Puis demande :
1. « Tu préfères de longues conversations, ou une conversation neuve par sujet ? » (décide si Claude propose la passation au changement de chantier seulement, ou plus tôt).
2. « Quand tu reviens, tu veux voir quoi en premier ? » (ajuste l'ordre de la reprise).
3. « Combien de chantiers en même temps, au maximum ? » (par défaut 2, voir taches-source-unique).
4. « Tes conversations deviennent-elles assez longues pour que Claude Code les résume tout seul ? » (si oui : le mémo de compactage).

Range les réponses dans le fichier mémoire `feedback_continuite.md` et dans les commandes si l'ordre change.

## Construire

1. **Le log tenu (5 min).** La reprise lit les 20 dernières entrées de `log.md`. Claude vérifie que `/fin` y écrit une entrée par session (format : `## [AAAA-MM-JJ] <type> | <titre>` puis 2 à 4 lignes). Sans log, pas de reprise fiable.

2. **Régler la reprise (10 min).** Claude adapte les sources de `/reprise` aux briques installées : outil de tâches réel, chemin réel du plan, passations. Il ajoute une ligne : « Si un document contredit l'état réel (un fichier, une tâche, un service), crois l'état réel et signale l'écart. »

3. **Régler la passation (5 min).** Claude ajoute au cœur, selon la réponse 1 : « Propose `/passation` en une ligne seulement quand la personne change vraiment de chantier. Jamais d'interruption en plein travail pour cause de taille. » Le fichier de passation suffit à reprendre sans relire la conversation : s'il manque une décision, c'est un défaut du fichier, on l'ajoute.

4. **Le mémo de compactage (10 min, si réponse 4 oui).** Quand la conversation devient très longue, Claude Code la résume tout seul et perd des détails (demandes exactes, fichiers touchés). Claude branche `memo-compactage.js` (fourni par la brique hooks-ecrire) : il écrit un mémo fidèle dans `outputs/passation/auto/` juste avant le résumé et le réinjecte juste après.

5. **Les gestes de session (5 min).** Claude écrit dans `wiki/maps/continuite.md`, pour la personne :
   - Un essai raté : revenir en arrière (double Échap ou `/rewind`) et relancer avec ce qu'on a appris, plutôt qu'empiler les corrections.
   - Compacter soi-même avec une consigne : `/compact garde les décisions et les fichiers, oublie les essais`.
   - Une question à côté sans couper le travail : `/btw <question>` (si ta version le propose).
   - Reprendre une conversation passée : `claude --continue` (la dernière) ou `claude --resume` (au choix).
   Trois [[liens]] : [[routage]], [[parcours]], [[log]].

6. **Le routage (2 min).** Les phrases de la personne pour `/reprise` et `/passation` sont dans `wiki/maps/routage.md` (la table du socle les a déjà ; ajoute ses mots à elle).

## Test
Les deux sont vrais :
- Claude fait `/passation` sur le chantier en cours. Dans une conversation neuve, la personne tape seulement `/reprise` : la réponse donne le bon chantier, la dernière action faite et la bonne prochaine action, sans aucune question.
- Si le mémo de compactage est branché : `node .claude/hooks/memo-compactage.js --test` affiche `ok`.

## Pièges vécus
- **Trop de « je continue ? » après les passations.** Juste après l'arrivée des passations, Claude s'est mis à demander la permission à chaque étape. Une passation ne remet pas en cause le plan : un plan validé reste un feu vert (format-et-autonomie).
- **La passation imposée par la taille.** Un rappel automatique à partir d'une certaine taille coupait la personne en plein élan. Débranché. La taille n'est jamais une raison d'interrompre.
- **Les dates relatives.** « Hier » dans un fichier de passation ne veut plus rien dire une semaine plus tard. Toujours des dates absolues.
- **La reprise qui croit un vieux document.** Une page disait « file pleine » alors que la file réelle était vide. La reprise vérifie l'état réel et signale l'écart.
- **Rediscuter une décision.** Sans la liste des décisions prises, une conversation neuve rouvrait des débats clos. La passation les liste, la reprise pointe le fichier.

## Entretien dans le temps
- Chaque `/fin` écrit le log : c'est ce qui nourrit la reprise.
- Une fois par mois, Claude relit les 5 dernières passations : une rubrique toujours vide sort du format, une information souvent réexpliquée y entre.

## Après
Coche la ligne `passation-reprise` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : taches-source-unique.
