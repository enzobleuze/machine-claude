---
name: mesure-et-apprentissage
description: "Branche la mesure du contenu (statistiques des réseaux, YouTube, site, tests A/B) et transforme les recettes gagnantes en règles écrites dans les skills et le code. Utiliser quand l'utilisateur dit « qu'est-ce qui marche », « bilan de la semaine », « pourquoi ma vidéo n'a pas marché », « fais un test A/B ». Pas pour les chiffres d'argent du business (utiliser le cockpit du bloc D)."
---
# Mesure et apprentissage

## Pourquoi
Sans mesure, le système d'origine a produit longtemps à l'aveugle : des articles par dizaines sans un clic, des posts au quota sans savoir lesquels comptaient. Ce qui a fait progresser : peu de chiffres, chacun lié à une décision, lus à date fixe, et chaque leçon écrite dans le code ou le skill concerné plutôt que répétée à la main. Une règle de terrain : un chiffre qui ne change aucune décision (abonnés seuls, likes seuls) ne se suit pas.

## Prérequis
- Au moins une brique de publication en marche (`posts-reseaux`, `essais-multiples`, `youtube-systeme` ou `article-lettre-seo`).
- Accès aux statistiques : YouTube Studio (ou l'API YouTube Analytics), Instagram (statistiques ou Graph API), Google Search Console pour le site, l'outil de publication.
- Bloc F pour la tâche planifiée du bilan, bloc C (`comite-decision`) pour les décisions à enjeu.

## Interview
Lis d'abord : `wiki/maps/machine-contenu.md`, les registres déjà en place (essais, YouTube, articles), l'objectif business du bloc D. Puis demande :
1. « Quel est le résultat qui compte pour toi : des appels, des inscrits, des ventes ? » Range dans `wiki/maps/mesure.md`, section « But ». Tout chiffre suivi doit y mener.
2. « Quand veux-tu ton bilan : le dimanche soir, le lundi matin ? » Range dans « Rythme ».
3. « Tu veux m'ouvrir l'accès aux statistiques par API, ou tu me colles des captures ? » Les deux marchent. Range dans « Accès ».

## Construire
1. **Les chiffres utiles** (Claude, 15 min). Dans `wiki/maps/mesure.md`, un tableau par format : vidéos courtes (saut avant 3 s, vues à 24 h et 72 h, partages pour 100 vues, commentaires longs d'au moins 15 mots), YouTube (taux de clic à 2 jours, rétention à 30 s, durée moyenne vue à 7 jours, part de recherche), posts (engagement moyen par gabarit), articles (clics et impressions à 30 et 90 jours), et pour tous les clics vers le but. Chaque ligne dit la décision qu'elle déclenche.
2. **Le registre** (Claude, 15 min). `outputs/mesure/registre.csv` : date, format, pièce, variable testée, chiffres, verdict. Pour les vidéos courtes, le registre de `essais-multiples` sert déjà. Un relevé se fait par API quand c'est possible, sinon depuis une capture que l'utilisateur colle (lis le texte d'abord).
3. **Le test A/B honnête** (Claude, 10 min par test). Une seule variable change. Assez de vues avant de conclure (au moins quelques centaines par version pour une vidéo courte). Écris l'hypothèse avant, le verdict après. Les miniatures YouTube passent par « Tester et comparer » de YouTube Studio.
4. **Le bilan** (Claude, 15 min, chaque semaine). Une tâche planifiée écrit `outputs/mesure/bilan-AAAA-MM-JJ.md` : les 3 pièces qui ont gagné et pourquoi, les 3 qui ont perdu, une seule recommandation. Ouvre par 3 lignes de résumé.
5. **De la recette à la règle** (Claude, 10 min). Une recette qui gagne trois fois devient une règle écrite là où elle agit : le skill concerné, le contrôle en code, la banque d'accroches, les gabarits de posts. Une règle répétée deux fois à la main doit vivre dans le code. Note la date et la preuve à côté de chaque règle.

## Test
Un bilan hebdomadaire existe avec ses 3 gagnants, ses 3 perdants et une recommandation, et au moins une règle d'un skill ou d'un script cite une preuve tirée du registre.

## Pièges vécus
- Suivre les abonnés et les likes sans lien avec le but : beaucoup d'énergie, aucune décision.
- Conclure sur un premier relevé trop petit : attends le relevé prévu (72 h, 7 jours, 90 jours).
- Changer plusieurs choses à la fois après un échec : on ne sait plus ce qui a joué. Trois changements au plus par série.
- Des règles notées dans un journal que personne ne relit : la règle va là où Claude la lira au moment d'agir.
- Un comité d'experts qui contredit les chiffres de l'utilisateur : note les deux, laisse l'utilisateur trancher, et mesure ensuite.

## Entretien dans le temps
Le bilan tourne seul chaque semaine (bloc F). Chaque trimestre, relis les règles : celles que les chiffres ne soutiennent plus sortent. Les grands virages (couper un format, en ouvrir un) passent par `comite-decision` (bloc C) avec les chiffres en main.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (but, rythme du bilan). Le bloc E est complet : propose le bloc F (automatisation et pilotage).
