---
name: fin-de-session
description: "Installe l'auto-amélioration de fin de session : enrichir le wiki, relier, index et journal, mémoire, trous, proposition de skill quand une méthode revient, commit ; plus un registre mensuel des frictions tiré des conversations passées. Utiliser quand l'utilisateur dit « on arrête », « fin de session », « /fin », « le système doit apprendre de nos sessions ». Pas pour changer de chantier en gardant le fil (utiliser /passation)."
---
# Fin de session et auto-amélioration

## Pourquoi
Dans le système d'origine, chaque session apprenait quelque chose (une préférence, une règle, une scène) qui disparaissait avec la conversation. La fin de session en cinq gestes a fait du wiki une chose qui grossit à chaque échange. Un second mécanisme a payé encore plus : relire d'un coup des dizaines de conversations passées pour trouver les frictions qui reviennent. La première fois, il a fait ressortir une continuité cassée entre sessions, des pannes silencieuses et des rapports illisibles, chacun réglé ensuite par un skill ou une règle.

## Prérequis
- architecture-vault, memoire-fichiers, lint-wiki.
- Fichier du socle : `.claude/commands/fin.md` (déjà écrit, ne le réécris pas, adapte-le).
- Aucun coût.

## Interview
Lis d'abord : `.claude/commands/fin.md` du vault s'il existe, `wiki/maps/architecture.md`.

Puis demande :
1. « Tu penses à dire « on arrête » en fin de session, ou je dois te le proposer ? » Si elle oublie : Claude propose `/fin` quand le travail du jour est fini.
2. « Tu veux qu'une fois par mois je relise nos conversations pour trouver ce qui te fait perdre du temps ? »

Range les réponses dans `wiki/maps/fin-de-session.md`, avec 3 liens.

## Construire
1. **La commande (3 min).** Copie `.claude/commands/fin.md` du socle dans le vault. Adapte l'étape « Enrichir » aux tiroirs de `wiki/maps/architecture.md`.
2. **Ajouter la proposition de skill (3 min).** Insère avant l'étape « Commit » de `/fin` :
   ```markdown
   **Un geste à transformer en skill ?** Une méthode a émergé que la personne refera, ou une demande
   est revenue trois fois : propose un skill en 5 lignes (nom, déclencheur, étapes, ce qu'il remplace)
   et écris-le dans outputs/skills-en-attente/<nom>/SKILL.md. Installation seulement après son oui.
   Une demande répétée sans jugement devient plutôt un script ou une tâche planifiée : dis-le en une ligne.
   Rien d'émergé : écris « aucun skill à proposer ».
   ```
3. **Règle dans le cœur (2 min).** Ajoute au `CLAUDE.md` : « Fin de chaque session de travail : /fin. Le wiki ne reste jamais statique. »
4. **Registre des frictions (15 min, une fois par mois).** Les conversations de Claude Code sont des fichiers `.jsonl` dans `~/.claude/projects/<projet>/`. Lance un sous-agent avec cette consigne :
   ```text
   Lis les conversations .jsonl du mois dans ~/.claude/projects/<projet>/ (messages de la personne seulement,
   par lots). Regroupe les frictions qui reviennent (même problème dans plusieurs sessions). Pour chaque
   groupe : nombre de sessions, 2 ou 3 phrases exactes en preuve, cause racine, verdict parmi skill, script,
   règle du cœur, déjà réglé, rien. Rends un tableau trié par gain.
   ```
   Écris le résultat dans `wiki/maps/registre-frictions.md` (frontmatter, 3 liens). Rien ne se construit sans le oui de la personne sur chaque verdict.
5. **Route (1 min).** « on arrête », « fin de session » vers `/fin` dans `wiki/maps/routage.md`.

## Test
Après un `/fin` : `log.md` a l'entrée du jour, chaque page créée dans la session a 3 liens, une leçon donnée dans la session existe en fichier mémoire, et `git log -1` montre le commit de session. Pour le registre : la page existe avec au moins un groupe prouvé par des phrases exactes.

## Pièges vécus
- `/fin` oublié : la session suivante repartait de zéro. Claude le propose lui-même quand le travail est fini.
- Mémoire remplie de doublons du wiki : la mémoire garde les réflexes, le wiki garde le savoir.
- Skills installés automatiquement : comportement de Claude changé sans que la personne le sache. Toujours en attente, puis oui.
- Registre qui lit toutes les conversations dans la session principale : contexte saturé. Toujours un sous-agent, et la session ne reçoit que le tableau.
- Diagnostic sans suite : chaque verdict accepté devient une tâche avec une définition de « fini ».

## Entretien dans le temps
Le registre se refait chaque mois. Compare avec le précédent : une friction qui revient malgré un « réglé » veut dire que la solution ne marche pas.

## Après
Coche la ligne `fin-de-session` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose sauvegardes-3-lieux.
