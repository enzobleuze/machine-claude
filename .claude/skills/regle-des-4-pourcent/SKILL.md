---
name: regle-des-4-pourcent
description: "Pose la règle des 4 % (les 3 seules activités que l'utilisateur garde, tout le reste va à Claude ou disparaît) et l'anti-surcharge (planchers de 20 minutes, 2 chantiers au plus). Utiliser quand l'utilisateur dit « je suis débordé », « je n'avance pas », « qu'est-ce que je délègue », « je veux tout faire », « anti-surcharge ». Pas pour écrire le plan lui-même (utiliser plan-unique)."
---
# Règle des 4 % et anti-surcharge

## Pourquoi
Un entrepreneur seul a peu d'heures. Dans le système d'origine, le fondateur avait une dizaine d'heures par semaine à côté d'un autre travail, et il avait tendance à faire des plans « à fond » qui finissaient en gel. Deux règles ont changé ça. La première : il ne garde que trois activités, celles que personne d'autre ne peut faire, et tout le reste devient un skill, une automatisation ou disparaît. La seconde : chaque engagement a un plancher ridicule et tenable de 20 minutes, et les grosses journées restent des bonus.

## Prérequis
- `entretien-fondateur` (question 17 : le temps réel par semaine).
- `plan-unique` pour y écrire les règles.

## Interview
**Lis d'abord** : `wiki/business/fondateur.md` (temps disponible), `wiki/strategie/plan.md`, la mémoire (préférences de travail, signes de surcharge déjà notés).

Puis demande :
1. Sur une semaine normale, qu'est-ce que tu fais pour ton business, heure par heure ? (Fais-lui lister, même en vrac.)
2. Dans cette liste, qu'est-ce que toi seul peux faire ? (Ta voix, ta présence, ton jugement.)
3. Qu'est-ce qui te vide le plus ?
4. Quand tu t'es arrêté par le passé, qu'est-ce qui s'est passé juste avant ?
5. Quel est le plus petit geste que tu tiendrais même une mauvaise semaine ?

Range dans `wiki/maps/regle-4-pourcent.md`.

## Construire
1. **Trier la semaine (ensemble, 20 min).** Mets chaque activité de la réponse 1 dans une des quatre colonnes : « toi seul », « Claude », « automatisé », « supprimé ». Écris le tableau dans `regle-4-pourcent.md`.
2. **Les 3 activités (ensemble, 10 min).** Choisis avec lui les trois activités « toi seul ». Pour un coach ou un consultant, c'est souvent : produire la matière brute dans sa voix (idées, angles, vécu), servir et vendre (séances, appels), valider ce que Claude prépare. Pour une boulangère, ce serait peut-être : faire le pain, accueillir, valider les commandes spéciales. Donne à chacune une limite de temps (par exemple 2 heures par brouillon, 15 minutes de validation par sujet).
3. **Les planchers (ensemble, 10 min).** Pour chaque engagement régulier, écris un plancher de 20 minutes au plus et une action visible (« 20 min de tournage », « répondre aux messages du jour »). Les pics restent des bonus, jamais la règle.
4. **Les garde-fous (Claude, 10 min).** Écris dans `CLAUDE.md` :
   - « Hors des 3 activités de l'utilisateur, tout passe par un skill, une automatisation ou disparaît. Ne lui délègue jamais une micro-étape que tu peux faire. »
   - « 2 chantiers en cours au plus. Un troisième attend qu'un des deux finisse. »
   - « Tout plan proposé a un plancher de 20 minutes. Ne valide jamais un plan à fond sans plancher de secours. »
   - « Une condition préalable (achat, réglage, outil) ne bloque jamais la première séance : elle se fait avec ce qu'il a. »
5. **Brancher le plan (Claude, 5 min).** Dans `plan.md`, chaque case de la semaine dit son temps et qui la fait. Une case de plus de 2 heures pour l'utilisateur se découpe.

## Test
Le tableau de `regle-4-pourcent.md` existe, chaque activité est dans une colonne, et la semaine du plan ne contient aucune case de l'utilisateur hors de ses 3 activités ni sans durée.

## Pièges vécus
- **Le plan héroïque.** Des plans maximalistes (entraînement intense chaque jour et travail sans pause) ont été posés trois fois et abandonnés trois fois. Le déblocage est venu d'un geste minuscule tenu.
- **Claude qui délègue par réflexe.** « Va dans les réglages et copie ceci » alors que Claude pouvait le faire par l'API. Avant chaque demande à l'utilisateur, vérifie s'il faut vraiment ses mains, ses accès ou son accord.
- **Trop de chantiers ouverts.** Avec cinq chantiers en parallèle, aucun ne finit. La limite de deux se vérifie à chaque nouvelle demande.
- **Le moteur qui s'éteint après une victoire.** Quand une grosse contrainte est réglée (une dette, une urgence), l'énergie peut tomber. Les engagements envers des gens réels (clients, rendez-vous) tiennent mieux que la volonté.

## Entretien dans le temps
- Au plan du lundi, vérifie la limite de deux chantiers et la présence d'un plancher par engagement.
- Quand l'utilisateur dit « je suis débordé », relis le tableau avec lui et déplace une activité de « toi seul » vers « Claude ».

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (les 3 activités et le plancher, une ligne chacun). Propose ensuite `fiches-clients`.
