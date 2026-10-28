---
name: routage-carnets
description: "Construit la table de routage sujet vers carnet (wiki/maps/routage-carnets.md) et la règle qui fait interroger le bon carnet AVANT de produire ou de trancher, avec des gabarits de questions denses. Utiliser quand l'utilisateur dit « quel carnet pour quoi ? », « Claude doit demander aux experts avant d'écrire », ou après avoir créé un carnet. Pas pour créer les carnets (utiliser carnets-experts)."
---
# La table de routage des carnets

## Pourquoi
Avoir des carnets ne sert à rien si Claude oublie de les ouvrir, ou ouvre le mauvais. Dans le système d'origine, une table dit, pour chaque sujet, quel carnet interroger, et chaque skill de contenu ou de décision la lit en « phase 0 », avant d'écrire une ligne. Résultat : des réponses sourcées au lieu de suppositions, et moins de jetons que relire les livres bruts.

## Prérequis
- `notebooklm-brancher` et `carnets-experts` faits (`carnets.json` rempli, `wiki/maps/carnets.md` à jour).
- Le cœur `CLAUDE.md` du vault (bloc B).

## Interview
Lis d'abord : `carnets.json`, `wiki/maps/carnets.md`, la liste des skills de l'utilisateur (`.claude/skills/`), et sa carte de routage des intentions si elle existe (bloc B).

Puis demande :
1. « Quelles sont les décisions que tu prends le plus souvent ? » (exemples : prix, offre, contenu de la semaine, réponse à un client difficile, recrutement).
2. « Quels textes produis-tu le plus ? » (posts, emails, pages, scripts vidéo, devis).
3. Pour chaque sujet donné : « Sur ce sujet, à qui ferais-tu confiance parmi tes carnets ? » (Claude propose d'abord, l'utilisateur corrige.)
4. « Y a-t-il des sujets où tu ne veux PAS que Claude consulte les carnets ? » (exemples : administration, journal personnel.)

Range tout dans `wiki/maps/routage-carnets.md`.

## Construire
1. **Écrire la table** (Claude) dans `wiki/maps/routage-carnets.md` :
   ```
   | Sujet ou déclencheur | Carnet principal | Carnet en appui | Gabarit de question |
   |:-|:-|:-|:-|
   | fond du métier (conseil donné au client) | expert-fond | ma-methode | AFFIRMATIONS |
   | prix, offre, garantie, priorités | expert-offre | | OPTIONS |
   | écriture d'une page ou d'un email de vente | expert-ecriture | expert-offre | RELECTURE |
   | réseaux sociaux (accroche, format) | expert-reseaux | | RELECTURE |
   | mots exacts des clients | voix-client | | MOTS |
   ```
   Les clés viennent de `carnets.json`. Ajoute une colonne « Ne juge pas » si un carnet a un angle mort connu.
2. **Écrire les gabarits** (Claude), dans le même fichier. Première ligne de chaque question, toujours : « Réponds UNIQUEMENT depuis les sources de ce carnet et cite la source de chaque point ; si tes sources ne disent rien sur un point, écris AUCUNE SOURCE. » (En anglais pour un carnet anglophone.) Puis :
   - **OPTIONS** (décision) : « Contexte en 80 mots. Décision : ... Options : A ..., B ..., C ... Quelle option recommandes-tu et pourquoi ? Trois principes avec le mécanisme derrière chacun, deux phrases de tes sources citées mot pour mot, le piège principal. 350 mots au plus. »
   - **AFFIRMATIONS** (vérifier un conseil) : la liste numérotée des affirmations ; pour CHAQUE point : D'ACCORD, NUANCE ou PAS D'ACCORD, une phrase pourquoi, la source. Puis la correction la plus importante.
   - **RELECTURE** (texte qui vend ou se publie) : « La ligne où un lecteur fatigué s'arrête et pourquoi ; toute ligne qui porte deux idées ; y a-t-il une seule action ; la réécriture qui a le plus d'effet, avec le principe. »
   - **MOTS** (voix du client) : « Donne dix phrases exactes de clients sur [situation], copiées mot pour mot, avec la source. »
3. **Brancher la règle** (Claude) dans `CLAUDE.md` du vault : « Avant de produire un texte ou de trancher une décision non triviale, lis `wiki/maps/routage-carnets.md`, interroge le ou les carnets de la ligne (via `scripts/nlm_ask.py`), et nomme le principe sourcé derrière chaque choix. Exceptions : la colonne des sujets exclus. »
4. **Ajouter la phase 0 aux skills de contenu** (Claude) : dans chaque skill qui écrit pour les clients, une étape « Phase 0 : routage des carnets » qui pointe vers ce fichier. Une ligne suffit, la table fait le reste.
5. **Ranger les réponses** : `outputs/carnets/<date>-<sujet>/`. Elles servent d'archive et évitent de reposer la même question.

## Test
Donne à Claude un sujet réel de l'utilisateur (« écris un email pour relancer un devis »). Il doit, sans qu'on le lui rappelle : nommer la ligne de la table, poser la question au bon carnet, et citer le principe sourcé dans sa proposition. Oui aux trois, sinon la règle n'est pas branchée.

## Pièges vécus
- **Une question vague donne une réponse vague.** Le carnet d'expert en offres répondait « va vendre » à tout ce qui n'était pas une décision à options. D'où le gabarit OPTIONS : on lui donne des options à classer.
- **« OK ou correction ? » ne trouve rien.** Une même copie déclarée « 100 % alignée » à cette question a été cassée, le même jour, par le format affirmation par affirmation. D'où le gabarit AFFIRMATIONS.
- **Une question dense vaut mieux que trois petites.** Chaque question prend de une à plusieurs minutes. Demander plusieurs principes dans une seule question tient la séance courte.
- **La réponse n'est pas le texte.** Elle se reformule dans la voix de l'utilisateur. Certains auteurs restent internes : on garde leur idée, jamais leur nom en public (voir la colonne `public` de `carnets.json`).
- **Une table jamais relue se périme.** Le système d'origine pointait un temps vers un ancien outil cassé. Chaque carnet ajouté ou retiré se reporte dans la table le jour même.

## Entretien dans le temps
- À chaque carnet ajouté (skill `carnets-experts`) : une ligne de table.
- Une fois par mois : compter dans `outputs/carnets/` quels carnets servent. Un carnet jamais interrogé est soit mal routé, soit inutile : le dire à l'utilisateur.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Propose ensuite `comite-decision` (décisions) ou `board-textes` (textes), selon ce que l'utilisateur fait le plus.
