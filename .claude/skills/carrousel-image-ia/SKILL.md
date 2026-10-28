---
name: carrousel-image-ia
description: "Fabrique un carrousel dont les images sont générées par une IA d'image (GPT Image, Gemini, Higgsfield ou autre), avec le texte validé avant de dépenser un crédit. Utiliser quand l'utilisateur dit « carrousel avec des images IA », « un carrousel plus beau », « des visuels générés ». Pas pour un carrousel gratuit en local (utiliser carrousel-html)."
---
# Carrousel image IA

## Pourquoi
Dans le système d'origine, les crédits partaient dans des images refaites parce que le texte changeait après coup. La règle est devenue : le texte passe le board avant le premier crédit, et chaque image suit un livre de règles écrit (couverture, slide 2, colonne vertébrale, rythme). La qualité visuelle est bien plus haute que le local, le coût aussi, donc on la garde pour les carrousels qui le méritent.

## Prérequis
- `carrousel-html` (même déroulé de texte), `images-de-marque` (style maison, librairie d'images, visage si besoin).
- Un compte chez un générateur d'image (payant). L'utilisateur crée le compte et colle la clé dans les secrets du bloc A.
- Bloc C (`board-textes`).

## Interview
Lis d'abord : `wiki/maps/style-maison.md` (bloc E, `images-de-marque`), `wiki/maps/carrousels.md`, les crédits restants s'il l'a noté. Puis demande :
1. « Quel générateur as-tu déjà, ou lequel veux-tu essayer ? » Range dans `wiki/maps/style-maison.md`, section « Modèles ».
2. « Quel budget par mois pour les images ? » Range dans la même section. Claude s'arrête avant de le dépasser.
3. « Des carrousels générés que tu as aimés ou détestés ? » Range dans « Goût ».

## Construire
1. **Le texte d'abord** (Claude, 20 min). Écris le carrousel comme dans `carrousel-html` étape 3 : la couverture se juge au test « que veut-on après ? », la slide 2 répond à la couverture et n'aurait aucun sens sous une autre couverture, une phrase unique que tout le carrousel prouve.
2. **La porte avant crédit** (Claude). Le texte passe `board-textes` (bloc C). Aucun crédit n'est dépensé avant le verdict vert.
3. **Les prompts** (Claude, 15 min). Un prompt par slide, assemblé depuis le style maison : la scène, la lumière, le cadrage, la place du texte, les interdits (texte déformé, mains, logos). Écris-les dans `outputs/carrousels/<slug>/prompts.md`. Annonce le coût estimé du lot.
4. **Une slide test** (Claude puis l'utilisateur, 5 min). Génère la couverture seule. L'utilisateur dit oui ou corrige. Sa note devient une règle du style maison avant la suite.
5. **Le lot** (Claude, 15 min). Génère le reste, contrôle sur une planche (`outils/planche.py`), régénère seulement les slides ratées. Si le générateur écrit mal le texte, génère sans texte et pose le texte avec `carrousel-html` (champ `image`).
6. **Publier** par `distribution-api`.

## Test
Un carrousel complet existe avec son verdict vert daté avant la première image, et le coût réel du lot est noté à côté du budget.

## Pièges vécus
- Le texte retouché après les images : tout le lot à refaire. Le board passe avant.
- Une recette de style « film ancien » (rayures, poussière, aberration) qui, à pleine taille, sortait en couche uniforme et se repérait comme fausse : teste toute recette sur un banc de 4 sujets avant de l'adopter.
- Un modèle choisi sur une seule belle image : fais un banc (plusieurs modèles, mêmes sujets, une génération chacun) et note-les sur planche.
- Des images de référence trouvées en ligne : elles servent de référence de lumière, jamais publiées.

## Entretien dans le temps
Chaque note de l'utilisateur sur une image devient une ligne du style maison. Le coût du mois se relève avec `mesure-et-apprentissage` ; si les carrousels IA ne battent pas les carrousels locaux, réduis-les.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (goût visuel). Propose ensuite `accroches`.
