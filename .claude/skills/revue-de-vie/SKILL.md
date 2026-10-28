---
name: revue-de-vie
description: "Crée la commande /revue-de-vie : un audit mensuel de toute la vie (piliers notés sur des faits, preuves d'abord, l'obstacle unique, plan de 90 jours à deux chantiers, récompense planifiée sans culpabilité, une action aujourd'hui). Utiliser quand l'utilisateur dit « je stagne », « fais le point sur ma vie », « revue du mois ». Pas pour le point du soir (utiliser journal-coach) ni pour le business seul (utiliser le cockpit du bloc D)."
---
# Revue de vie mensuelle

## Pourquoi
Le journal du soir regarde une journée. Le fondateur d'origine avait aussi besoin de la vue d'ensemble : il se sentait stagner alors que les faits de son vault montraient le contraire, et il bloquait sur ses récompenses par culpabilité. La revue mensuelle commence par les preuves, nomme un seul obstacle, limite le plan à deux chantiers et planifie une récompense. Elle s'appuie sur le journal et le scoreboard, donc elle juge sur les faits du mois.

## Prérequis
- journal-coach (les scores et insights), scoreboard-et-plan-semaine (les chiffres).
- Le plan unique et la mission du bloc D.
- Option : un rappel mensuel planifié.

## Interview
Lis d'abord : le profil de l'utilisateur, `wiki/journal/` du mois, `wiki/maps/scoreboard.md`, le plan unique, la dernière revue (`wiki/strategie/revue-de-vie-*.md`), la mémoire.
Puis demande :
1. « Quels sont les domaines de ta vie que tu veux noter chaque mois ? » Propose une base (paix intérieure, santé et énergie, relations, argent, objectifs, connaissance de soi, accomplissement) et laisse-le changer.
2. « Quels rêves concrets as-tu ? Un voyage, un objet, une expérience. » (sert aux récompenses.)
3. « Quel cadre de référence t'aide ? » (auteurs, tradition, philosophie : les siens, jamais ceux d'un autre.)
Range les domaines et la liste de rêves dans le profil, les auteurs dans la commande.

## Construire
1. **Commande (Claude, 20 min).** Écris `.claude/commands/revue-de-vie.md` avec ce déroulé, dans cet ordre :
   1. **Charger avant de parler** : profil, journal du mois, scoreboard, plan unique, dernière revue, tâches ouvertes.
   2. **Noter chaque domaine sur dix**, chaque note justifiée par des faits du journal ou du scoreboard. Comparer avec la revue précédente.
   3. **Preuves d'abord** : lister ce qui est déjà accompli avant de parler des manques. Quand le sentiment de stagnation contredit les faits, le montrer avec les faits.
   4. **Vision** : la personne visée, au présent, dans ses mots à lui.
   5. **L'obstacle unique** : un seul obstacle nommé, et l'excuse qui revient à chaque palier. Tester les hypothèses du type « pas encore prêt ».
   6. **Plan de 90 jours** : deux chantiers au plus, jalons datés, un plancher minimal par chantier, le reste reporté par écrit.
   7. **Récompense planifiée** : voir l'étape 2.
   8. **Une action aujourd'hui**, binaire, faisable avant de dormir.
   Règles : pas de complaisance, trois questions au plus à la fois, zéro chiffre inventé, contenu privé.
2. **Se récompenser sans culpabilité (Claude, 10 min).** Ajoute dans la commande une section dédiée :
   - Chaque palier atteint finance un rêve de sa liste, nommé à l'avance.
   - L'argent de la récompense est gagné exprès (une vente, une mission en plus), jamais pris sur l'épargne ou le budget de base. La culpabilité devient de la fierté.
   - Des petites récompenses sur le chemin, pas seulement à l'arrivée.
   - Le seul juge est l'utilisateur lui-même : ne pas attendre la permission de quelqu'un d'autre.
   - Garde-fou : la récompense vient après le travail fait, jamais à sa place.
3. **Sortie (Claude, 5 min).** Après chaque revue : `wiki/strategie/revue-de-vie-AAAA-MM-JJ.md` (notes, obstacle, plan, récompense, action) avec au moins trois liens vers d'autres pages ; une ligne dans `log.md`.
4. **Rappel mensuel (option, Claude, 3 min).** `scripts/rappel-revue.sh` qui appelle `notifier hebdo "Revue du mois" "Une heure pour faire le point : tape /revue-de-vie."`. Le planificateur Windows n'a pas de « premier dimanche du mois » simple : planifie-le chaque dimanche et fais sortir le script tout de suite (`exit 0`) si le jour du mois dépasse 7.

## Test
Une revue produit `wiki/strategie/revue-de-vie-<date>.md` avec une note justifiée par domaine, un seul obstacle, au plus deux chantiers et une récompense nommée.

## Pièges vécus
- **Juger l'humeur du jour** : un soir difficile faisait noter toute la vie en bas. Les notes s'appuient sur les faits du mois.
- **Se priver jusqu'à l'os** : la privation punitive a mené au burn-out dans le système d'origine. La récompense planifiée fait partie du plan.
- **Plan à cinq chantiers** : ramener à deux, et le dire franchement.
- **Plans en pics** : quelqu'un d'extrême construit des plans « à fond » puis se fige. Un plancher ridicule et tenable pour chaque chantier.
- **Une condition préalable qui bloque** (acheter du matériel, attendre le bon moment) : la première séance se fait avec ce qui est déjà là.

## Entretien dans le temps
Chaque revue compare avec la précédente. Un obstacle nommé deux mois de suite devient le chantier numéro un. Les rêves réalisés sortent de la liste, de nouveaux entrent.

## Après
Mets à jour `wiki/maps/parcours.md` et `log.md`. En mémoire : seulement un schéma durable ou une préférence nouvelle. Propose ensuite catalogue-automatisations.
