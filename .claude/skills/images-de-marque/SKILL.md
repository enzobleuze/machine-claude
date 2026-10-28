---
name: images-de-marque
description: "Construit le style maison des images (palette, lumière, recettes de prompt, modèles choisis) et une librairie d'images réutilisables (portraits, objets, fonds), plus les miniatures et visuels d'article. Utiliser quand l'utilisateur dit « mon style visuel », « fais une librairie d'images », « une image pour mon article ». Pas pour un carrousel complet (utiliser carrousel-image-ia)."
---
# Images de marque

## Pourquoi
Les images du système d'origine changeaient de style d'une pièce à l'autre et se repéraient comme générées. La solution : un style maison écrit (une bible courte), un banc d'essai où plusieurs modèles passent sur les mêmes sujets, et une librairie d'images déjà validées qu'on réutilise au lieu de tout régénérer. Le goût de l'entrepreneur a tranché à chaque fois : certains modèles pour les visages, d'autres pour les scènes, et des recettes à la mode écartées quand elles sonnaient faux.

## Prérequis
- Bloc D (marque, client idéal). Un générateur d'image (payant, au choix : GPT Image, Gemini, Higgsfield, Midjourney ou autre).
- Outil partagé : `outils/planche.py` (juger 16 images pour le prix d'une).
- Option : quelques photos réelles de l'utilisateur s'il veut apparaître (miniatures).

## Interview
Lis d'abord : `wiki/maps/style-maison.md` s'il existe, le logo et les couleurs du bloc D, les images qu'il a déjà publiées. Puis demande :
1. « Dépose 10 à 30 images que tu aimes (n'importe où) dans un dossier. » Range le chemin dans `wiki/maps/style-maison.md`, section « Moodboard ». Ces images servent de référence, jamais publiées.
2. « Tu veux apparaître sur tes visuels ? » Si oui, demande des photos nettes de face et de trois quarts. Range dans « Visage ».
3. « Quels sujets reviennent dans ton domaine ? » (un objet, un lieu, des personnes). Range 4 sujets dans « Banc ».
4. « Quel budget d'images par mois ? » Range dans « Modèles ».

## Construire
1. **Lire le moodboard** (Claude, 10 min). `python outils/planche.py "<dossier>/*" -o planche-moodboard.jpg`. Décris en mots la lumière, la palette, le grain, le cadrage. Écris la bible : 10 règles courtes, une palette en codes couleur, deux registres de lumière au plus.
2. **Le banc** (Claude, 20 min). Mêmes 4 sujets, plusieurs modèles, une génération par case. Planche par modèle. L'utilisateur choisit sur planche. Chaque verdict va dans « Modèles » (quel modèle pour quel usage).
3. **La recette de prompt** (Claude, 10 min). Un gabarit de prompt par usage (scène, portrait, objet, fond) avec les interdits (texte déformé, mains abîmées, logos de tiers). Range dans `wiki/maps/style-maison.md`.
4. **La librairie** (Claude, 20 min). Génère ou choisis 20 à 40 images validées, rangées par sujet et par humeur dans `bibliotheque/images/` avec un `catalogue.json` (fichier, sujet, humeur, modèle, date, droits). Les carrousels, articles et montages piochent ici d'abord.
5. **Miniatures et articles** (Claude, au besoin). Miniatures : règles de `youtube-systeme`, le visage réel de l'utilisateur, notées sur une grille avant de les montrer. Image d'article : une image de la librairie ou une génération au style maison, avec un texte alternatif qui décrit l'image.

## Test
La bible du style tient sur une page, le banc a désigné un modèle par usage, et la librairie contient au moins 20 images cataloguées avec leurs droits.

## Pièges vécus
- Une recette « film ancien » chargée (rayures, poussière, aberration) qui sortait en couche uniforme à pleine taille : signature visible de l'IA. Teste au banc avant d'adopter.
- Un générateur choisi par défaut pour les images d'article, dont le style ne collait pas au goût de l'entrepreneur : c'est son œil qui décide, sur planche.
- Un filigrane de logo sur les miniatures, jugé moche : retiré. Le visage fait office de marque.
- Des images de référence publiées par erreur : elles appartiennent à d'autres. Le catalogue marque leurs droits « référence seulement ».
- Ouvrir chaque image une par une : coûteux. Toujours la planche d'abord.

## Entretien dans le temps
Chaque note de l'utilisateur sur une image devient une règle de la bible. La librairie grandit à chaque bonne image. Refais le banc quand un nouveau modèle sort et que le budget le permet.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (goût visuel, modèles choisis). Propose ensuite `sons-et-musique`.
