---
name: accroches
description: "Écrit et vérifie les accroches des vidéos courtes et longues : texte à l'écran, phrase dite, image, avec la règle « phrase 1 = une scène ». Tient la banque des accroches gagnantes. Utiliser quand l'utilisateur dit « une accroche pour X », « vérifie mon hook », « pourquoi ma vidéo décroche au début ». Pas pour le script entier (utiliser script-video ou reels-et-shorts)."
---
# Accroches

## Pourquoi
Les mesures du système d'origine ont été nettes. Les vidéos courtes qui ouvraient sur une plainte résumée (du type « tu fais tout et rien ne change ») perdaient la majorité des gens avant 3 secondes, et la plateforme arrêtait la diffusion après le premier petit lot de test. La même prise, ouverte sur une scène précise que l'on voit (un geste, une phrase dite dans la cuisine), passait le lot et continuait. La règle : la phrase 1 montre un moment précis dans la seconde. Les accroches gagnantes vont dans une banque pour être remixées.

## Prérequis
- Bloc D (client idéal et ses mots), bloc C (`agent-client-ideal`, `board-textes`).
- `veille-et-tendances` aide à remplir la banque (accroches de gros comptes, transformées en formes).

## Interview
Lis d'abord : la fiche client idéal (ses situations concrètes), `wiki/maps/banque-accroches.md` s'il existe, les statistiques de rétention de ses dernières vidéos s'il les a. Puis demande :
1. « Dans quelles scènes ton client se reconnaît-il tout de suite ? Un lieu, un moment, une phrase. » Range 10 scènes dans `wiki/maps/banque-accroches.md`, section « Scènes ».
2. « Quelles accroches as-tu déjà essayées, et lesquelles ont marché ? » Range dans « Mesurées ».
3. « Y a-t-il des ouvertures que tu ne veux plus jamais voir ? » Range dans « Interdites ».

## Construire
1. **La banque** (Claude, 15 min). `wiki/maps/banque-accroches.md` contient : les scènes, les formes validées (une forme par ligne, avec un exemple à lui), les accroches mesurées (vues, saut avant 3 s), les interdites. Une forme vient de la veille quand on la voit gagner chez au moins deux gros comptes.
2. **L'accroche triple** (Claude, 10 min par vidéo). Pour chaque vidéo, écris 5 accroches de types différents. Chacune a trois couches : le texte à l'écran (5 mots au plus), la phrase dite (la scène), l'image (ce qu'on voit). Types qui ont servi : la scène, l'erreur qui coûte cher, la confession au passé, la question qu'il se pose, la curiosité (« je vais te faire gagner des semaines »).
3. **Les trois tests** (Claude, 5 min). Fuite : lue seule, on ne devine pas la leçon. Spécificité : elle ne pourrait ouvrir aucune autre vidéo. Désir : elle pointe vers ce qu'il veut ou ce qu'il veut éviter. Ajoute le refus automatique : pas de plainte résumée en phrase 1, pas deux vidéos de suite qui ouvrent pareil.
4. **Le client idéal** (Claude, 5 min). Passe les 5 à `agent-client-ideal` (bloc C) en mode test : où s'arrête-t-il de défiler ? Garde les 2 meilleures en tête.
5. **Écrire le contrôle en code** (Claude, 20 min, une seule fois). Mets les refus dans un petit script `outils/accroche_verifier.py` (liste de débuts interdits, longueur du texte à l'écran, comparaison avec les 10 dernières accroches). Une règle répétée deux fois à la main doit vivre dans le code.

## Test
Chaque vidéo de la semaine a 5 accroches triples, les 2 meilleures choisies par le client idéal, et aucune ne commence par une plainte résumée.

## Pièges vécus
- La plainte résumée en ouverture : forte chute avant 3 secondes, diffusion stoppée.
- Des accroches visuelles jouées (faux décor, mise en scène) que l'entrepreneur ne voulait pas tourner parce qu'il les trouvait irréalistes : propose des scènes qu'il peut dire face caméra.
- Une accroche qui donne déjà la leçon : plus aucune raison de rester.
- Des formes en antithèse (« ce n'est pas X, c'est Y ») tirées de listes virales : refusées par la voix.

## Entretien dans le temps
Chaque semaine, les accroches publiées reçoivent leurs chiffres (`mesure-et-apprentissage`). Une forme qui gagne trois fois monte en tête ; une forme qui perd trois fois sort. La banque se refait seule depuis les vidéos transcrites de la veille, une fois par semaine.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (ouvertures interdites). Propose ensuite `reels-et-shorts`.
