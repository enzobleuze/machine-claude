---
name: plan-unique
description: "Pose LE plan unique de l'utilisateur dans wiki/strategie/plan.md : objectif chiffré long terme, jalons, trimestre avec cible et actuel, mois, semaine, feuille de route avec une seule ligne PROCHAINE, plan du lundi, et une ligne de situation au début de chaque conversation. Utiliser quand l'utilisateur dit « fais mon plan », « où on en est », « plan du lundi », « c'est quoi la prochaine tâche », « mets le plan à jour ». Pas pour l'écran visuel (utiliser cockpit-app)."
---
# Plan unique

## Pourquoi
Dans le système d'origine, il y avait plusieurs plans en même temps, près de deux cents tâches ouvertes et plus d'une centaine d'idées. Le fondateur oubliait le cap, et Claude perdait le fil au point de devoir faire des passations sans arrêt. Un seul fichier a remplacé tous les plans : un bloc lisible par script en haut, une feuille de route en dessous, et une seule ligne marquée **PROCHAINE**. Claude la lit au début de chaque conversation et situe l'utilisateur en une phrase.

## Prérequis
- `entretien-fondateur` (chiffres et temps disponible).
- `regle-des-4-pourcent` conseillée juste après, pour filtrer les tâches.
- Outil joint : `outils/plan.modele.md`. Le Cockpit (`cockpit-app`) lit ce format.

## Interview
**Lis d'abord** : `wiki/business/fondateur.md`, `wiki/business/chiffres.md`, tout fichier de plan existant (cherche « plan », « objectif », « roadmap » dans `wiki/` et `raw/`), la liste de tâches (Linear ou autre) si elle est branchée.

Puis demande, une question à la fois :
1. Dans 3 à 5 ans, combien veux-tu gagner par mois, et à quelle date ? (C'est le cap.)
2. Où en es-tu aujourd'hui, par mois ? (Le chiffre de `chiffres.md` si tu l'as déjà.)
3. Pour chaque fin d'année d'ici là, quel revenu mensuel serait un bon point de passage ? Propose une montée régulière et laisse-le corriger.
4. Ce trimestre, quels 2 ou 3 chiffres disent que tu avances ? (Ventes, appels, inscrits.) Combien pour chacun, et combien aujourd'hui ?
5. Ce mois-ci, combien veux-tu encaisser ?
6. Quelles grandes étapes faut-il franchir, dans quel ordre ? Pour chacune : comment sais-tu qu'elle est finie ?
7. Quelle est LA chose de cette semaine, celle qui compte plus que tout le reste ?

Range tout dans `wiki/strategie/plan.md`.

## Construire
1. **Archiver l'ancien (Claude, 10 min).** Déplace tout ancien plan dans `wiki/strategie/archive/` avec une ligne en tête : « Remplacé par plan.md le JJ/MM. » Demande l'accord avant de déplacer.
2. **Remplir le modèle (Claude, 20 min).** Copie `outils/plan.modele.md` vers `wiki/strategie/plan.md`. Remplace chaque `{{…}}` par les réponses. Un chiffre inconnu s'écrit `null`, jamais 0. Garde les dates au format `AAAA-MM-JJ` dans le bloc du haut.
3. **Feuille de route (ensemble, 20 min).** Écris les étapes avec leur « Preuve de fin » binaire. Sous chaque étape, des cases de tâches de 20 minutes à 2 heures. Marque **PROCHAINE** sur une seule case non cochée. Chaque case dit qui la fait (« toi 15 min », « Claude, sans ton temps »).
4. **Vérifier la lecture (Claude, 5 min).** Si le Cockpit est installé, lance `python scripts/cockpit/cockpit_build.py ligne`. Sinon lance le contrôle du modèle : `python .claude/skills/cockpit-app/outils/cockpit_build.py ligne --vault .` depuis le vault. La ligne doit citer la prochaine tâche.
5. **Ligne de situation en début de conversation (Claude, 10 min).** Si `scripts/cockpit/cockpit_build.py` n'existe pas encore, copie-le avec `cockpit_sources.py` (il en a besoin) depuis `.claude/skills/cockpit-app/outils/` (ils marchent seuls, sans le serveur). Ajoute ensuite un hook `SessionStart` dans `.claude/settings.json` qui affiche la ligne :
   ```json
   {"hooks": {"SessionStart": [{"hooks": [{"type": "command", "command": "python -X utf8 scripts/cockpit/cockpit_build.py ligne"}]}]}}
   ```
   Sur Mac ou Linux, remplace `python` par `python3`. Ajoute dans `CLAUDE.md` : « En début de conversation, situe l'utilisateur en une ligne à partir de la ligne de situation. S'il lance un travail hors de la priorité de la semaine, dis-le en une phrase et propose de le noter en idée. »
6. **Plan du lundi (Claude, 15 min chaque lundi).** Quand l'utilisateur dit « plan du lundi » (ou au premier échange du lundi) : relis la semaine passée, coche ce qui est fait, reporte ce qui reste s'il sert encore, mets à jour les `actuel` du trimestre, réécris la section « Semaine du … » avec 5 à 8 cases datées, change `semaine.debut` et `semaine.chose`, déplace **PROCHAINE** si besoin. Montre le résultat en 10 lignes et attends son « oui ».
7. **Revue de fin de trimestre (ensemble, 20 min).** Compare cible et actuel, écris trois lignes de leçons sous le trimestre clos, pose le trimestre suivant.

## Test
`cockpit_build.py ligne` affiche « Prochaine tâche : … » avec la vraie tâche, et une nouvelle conversation commence par cette ligne sans que l'utilisateur ait rien demandé.

## Pièges vécus
- **Plusieurs plans qui se contredisent.** Il en faut un seul. Les autres partent en archive le jour même.
- **Une PROCHAINE qui parle d'une date passée.** Le plan disait « lundi 19/10 » le 22/10. Le Cockpit signale maintenant toute case datée d'avant aujourd'hui. Corrige le plan dès que l'alerte sort.
- **Le plan maximaliste.** Un plan « à fond » fige la personne. Chaque semaine garde un plancher tenable (voir `regle-des-4-pourcent`).
- **Proposer un levier déjà refusé.** Le fondateur avait dit que son audience était froide et que l'ordre serait machine à contenu, aimant, vente, puis pubs. Claude reproposait « fais plus de conversations ». Quand l'utilisateur tranche un ordre, écris-le dans la section « Pourquoi ce cap » et ne le rediscute plus.
- **Le compteur à 0 qui ment.** Un objectif sans chiffre actuel s'écrit `null`. Le Cockpit l'affiche « inconnu » et lève une alerte.

## Entretien dans le temps
- Chaque lundi : plan du lundi (étape 6).
- Après chaque session de travail : coche les cases faites et déplace **PROCHAINE**.
- Si la tâche planifiée du bloc F existe, ajoute un rappel du lundi matin dans le rapport du matin.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (« le plan unique est wiki/strategie/plan.md, la PROCHAINE fait foi »). Propose ensuite `regle-des-4-pourcent`.
