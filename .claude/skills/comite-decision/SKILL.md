---
name: comite-decision
description: "Installe et fait tourner un comité de 5 conseillers indépendants (sous-agents) qui analysent une décision, se relisent en anonyme, puis une synthèse tranche. Utiliser quand l'utilisateur dit « passe ça au comité », « j'hésite entre A et B », « pressure-test cette idée », « qu'est-ce que tu ferais à ma place ». Pas pour une question à réponse unique, pas pour écrire un texte (utiliser board-textes pour juger un texte rédigé), pas pour un avis ancré sur les carnets (utiliser comite-roast-ancre)."
---
# Le comité de décision

## Pourquoi
Une seule réponse de Claude peut être bonne ou moyenne, et rien ne permet de le savoir. Le comité fait réfléchir cinq angles qui se contredisent, puis chacun relit les autres sans savoir qui a écrit quoi, et une synthèse dit où ils s'accordent, où ils se heurtent et quoi faire. Dans le système d'origine, c'est l'outil des décisions difficiles (prix, offre, choix d'un chantier), et la relecture anonyme est l'étape qui fait la différence : elle trouve l'angle mort que les cinq avis isolés avaient tous.

## Prérequis
- Claude Code avec l'outil Agent (sous-agents).
- Bloc B fait (cœur `CLAUDE.md`, mémoire) : le comité lit le contexte réel avant de cadrer.
- Coût : une séance lance environ 10 sous-agents. Annonce-le avant (une ligne).

## Interview
Lis d'abord : `CLAUDE.md`, l'index MEMORY, le plan du trimestre s'il existe (bloc D), et les séances passées dans `outputs/comite/` pour ne pas rejouer la même question.

Puis demande, une seule fois, à l'installation :
1. « Quand tu hésites, quels angles te manquent le plus souvent : le risque, la vision large, le concret du lundi matin, l'œil d'un inconnu ? » (Claude garde les cinq angles par défaut et ajuste la description de chacun au métier de l'utilisateur.)
2. « Qui doit décider à la fin : toi toujours, ou Claude peut trancher seul les petites décisions ? » (va dans `CLAUDE.md`, ligne autonomie.)

À chaque séance, si la décision ou les options manquent : UNE question précise, puis on lance.

## Construire
1. **Écrire le skill du comité** (Claude) dans `.claude/skills/comite/SKILL.md` du vault, avec ce protocole :
   - **Cadrer.** Lire 2 ou 3 fichiers de contexte (30 secondes, pas plus). Écrire la question cadrée : la décision, les options, le contexte chiffré (hypothèses marquées « supposé »), l'enjeu. Neutre : aucun avis de Claude dedans.
   - **Cinq conseillers en parallèle**, un sous-agent chacun, dans UN seul message. Les angles : le Contradicteur (cherche ce qui va casser), le Retour aux principes (quel est le vrai problème), l'Expansionniste (ce qui pourrait être bien plus grand), l'Inconnu (aucun contexte, il voit ce que l'expertise cache), l'Exécutant (que fait-on lundi matin). Consigne commune : « Défends ton angle à fond, pas d'équilibre, 150 à 300 mots, va droit au but. »
   - **Relecture anonyme.** Mélanger les cinq réponses, les nommer Réponse A à E (correspondance gardée dans le fichier de séance). Cinq nouveaux sous-agents lisent tout et répondent : laquelle est la plus forte et pourquoi ; laquelle a le plus gros angle mort ; ce que TOUTES ont raté.
   - **Synthèse** (la session, en président) : où ils s'accordent, où ils se heurtent, les angles morts trouvés à la relecture, la recommandation, LA première action. Avant d'écrire, essayer de casser sa propre recommandation.
   - **Archive** : `outputs/comite/<date>-<sujet>.md` (question cadrée, les cinq avis, les relectures, la synthèse).
2. **Gabarit de prompt d'un conseiller** (à mettre dans le skill) :
   ```
   Tu es [nom du conseiller] dans un comité de décision.
   Ta façon de penser : [description adaptée au métier de l'utilisateur].
   La question posée au comité :
   ---
   [question cadrée]
   ---
   Réponds depuis ton angle. Sois direct et précis. N'équilibre pas : les autres couvrent les autres angles.
   150 à 300 mots. Pas d'introduction.
   ```
3. **Gabarit de relecture** : la question cadrée, les cinq réponses anonymes, puis les trois questions de l'étape 1. 200 mots au plus.
4. **Déclencheurs** (Claude) : ajouter au routage des intentions du vault les phrases de l'utilisateur (« j'hésite », « passe ça au comité »). Exclure les questions à réponse unique et les demandes d'écriture.
5. **Format de réponse** dans le chat : trois lignes de résumé, la décision recommandée, le seul bémol qui compte, le chemin du fichier.

## Test
Lance une vraie séance sur une décision réelle de l'utilisateur. Réussi si : les cinq avis existent et défendent des positions différentes, la relecture nomme au moins un angle mort absent des cinq avis, et l'utilisateur dit que la synthèse l'aide à décider.

## Pièges vécus
- **Sans contexte, des avis génériques.** Le cadrage lit les vrais fichiers (chiffres, contraintes, essais passés) avant de lancer, sinon les cinq conseillers donnent des conseils de livre.
- **Le président qui prend parti.** La synthèse pèse les arguments, pas les voix. Un dissident mieux argumenté peut l'emporter sur quatre avis faibles : le dire.
- **Tout le monde d'accord.** Une unanimité rapide cache souvent une option non défendue. Demander alors à un conseiller de défendre à fond la meilleure option écartée.
- **Le coût d'un sous-agent.** Chaque sous-agent recharge tout le contexte de Claude Code. Pour des séances fréquentes, la variante `comite-roast-ancre` lance ses sièges sans outils, ce qui coûte bien moins.
- **Une décision d'écriture n'est pas une décision.** « Écris-moi un post » n'a rien à faire au comité. Un texte rédigé à juger va au `board-textes`.

## Entretien dans le temps
- Chaque séance s'archive. Une fois par trimestre, relire les décisions passées et noter dans la mémoire celles qui ont marché ou pas : le cadrage s'améliore avec ces leçons.
- Si l'utilisateur ignore souvent un angle, demander s'il faut le remplacer par un angle plus utile à son métier.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. Si une préférence de décision apparaît (« je veux toujours le coût en premier »), la noter en mémoire. Propose ensuite `comite-roast-ancre`.
