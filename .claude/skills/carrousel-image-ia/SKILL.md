---
name: carrousel-image-ia
description: "Fabrique un carrousel aux images générées par une IA d'image (GPT Image, Gemini, Higgsfield ou autre) : un livre de règles du récit contrôlé par un outil, le texte validé par le board avant le premier crédit, des prompts aux couleurs de la charte, une couverture test, une banque d'images réutilisables et la finition en 1080x1350. Utiliser quand l'utilisateur dit « carrousel avec des images IA », « un carrousel plus beau », « des visuels générés ». Pas pour un carrousel gratuit en local (utiliser carrousel-html)."
---
# Carrousel aux images générées

## Pourquoi
Dans le système d'origine, les crédits partaient dans des images refaites parce que le texte changeait après coup, ou parce qu'une slide restait obscure une fois générée. La réponse a été un livre de règles écrit comme pour une vidéo (une destination, des boucles payées, une seule action, des plafonds de mots), rendu bloquant par un script avant le moindre crédit. Puis le board sur le texte exact et une couverture test ; les slides aimées vont dans une banque pour revenir plus tard. Le rendu est bien plus beau que le local, le coût aussi : on le garde pour les carrousels qui le méritent, en alternance avec les carrousels locaux.

## Prérequis
- `carrousel-html` fait : `outils/carrousel.py` (l'outil de ce skill s'en sert pour la charte) et `outils/file.py` (revue et file).
- `charte-graphique` (palette et polices du prompt) et `images-de-marque` : `wiki/maps/style-maison.md` avec ses sections « Modèles », « Recette » et « Goût », et les photos d'origine du visage si l'utilisateur apparaît.
- `board-textes` (bloc C).
- Un compte chez un générateur d'image (payant). L'utilisateur crée le compte et colle la clé dans les secrets du bloc A, ou branche le connecteur du générateur dans Claude Code (`connecteurs-mcp`).
- ffmpeg pour la finition. Python 3.8 ou plus récent.
- Outil joint : `outils/carrousel-ia.py` (testé : `python outils/carrousel-ia.py --test`).

## Interview
Lis d'abord : `wiki/maps/style-maison.md`, `wiki/maps/carrousels.md`, `bibliotheque/marque/charte-jetons.json`, et le budget s'il est noté. Puis demande, une question à la fois :
1. « Quel générateur as-tu déjà, ou lequel veux-tu essayer ? » S'il n'y en a pas encore, fais d'abord le banc de `images-de-marque`. Range dans `wiki/maps/style-maison.md`, section « Modèles ».
2. « Combien coûte une image chez lui, et quel budget par mois pour les images ? » Range dans « Modèles ». Claude s'arrête avant de dépasser.
3. « Tu veux apparaître sur la couverture et la dernière slide ? » Si oui, range des photos nettes de face et de trois quarts dans `bibliotheque/images/visage/`.
4. « Des carrousels générés que tu as aimés ou détestés ? » Range dans « Goût ».
5. « Plutôt une photo pleine page (modèle `affiche`) ou un fond sombre avec des cartes de verre (modèle `verre`) ? » Montre une couverture test de chaque. Un modèle entre dans la rotation quand l'utilisateur dit que le style est parfait.

## Construire
1. **Installer (Claude, 2 min).** Copie `outils/carrousel-ia.py` à côté de `outils/carrousel.py`. `python outils/carrousel-ia.py --test` doit écrire « AUTO-TEST OK ».
2. **Le script, avant toute image (Claude, 20 min).** `python outils/carrousel-ia.py exemple > outputs/carrousels/<slug>/slides.json`, puis remplis le bloc `script` :
   - `destination` : d'où part le lecteur (ce qu'il croit en ouvrant) et où il arrive (le geste qu'il fera en refermant), terminée par « Phrase prouvée : » et la phrase que tout le carrousel prouve sans la répéter.
   - `accroche` : ce qu'il désire, craint ou a déjà essayé. La couverture s'écrit en dernier, à partir du moment le plus fort du carrousel, en 6 mots au plus. Test : « que veut-il voir après ? » Si la réponse honnête est rien, c'est une étiquette. Jamais de sommaire du genre « 5 conseils pour ».
   - `boucles` : chaque question ouverte, la slide qui l'ouvre et celle qui la paie. La couverture en ouvre une, et tout se paie dans le carrousel.
   - `longueur` : de 6 à 15 slides, avec la raison (une slide par étape, un récit et sa bascule, la slide à garder, l'action). Au-delà de 10, la publication passe par l'application du réseau.
   - `sauvegarde` : au moins une slide à garder (liste, plan ou script réutilisable), sur une carte.
   - `commentaire` : le mot à écrire et ce que la personne reçoit, identiques en dernière slide et dans la légende.
   Puis chaque slide : `role` (couverture, reponse, contexte, etape, tension, bascule, payoff, garder, action), `titre`, `texte`, `repond` (la question de la slide d'avant), `ouvre` (celle qu'elle laisse), `scene` (ce que montre l'image), `fond` (sombre pour la tension, clair pour la relâche). La slide 2 répond à la couverture, avec le même gabarit à la même place ; si elle aurait du sens sous une autre couverture, elle ne tient rien. La réponse complète n'arrive jamais trop tôt. La bascule arrive vers les deux tiers. Vers les slides 4 et 5, l'attention baisse : mets-y une étape nommée ou une liste. La fin dit la croyance changée en une ligne, puis l'action en découle. La légende va dans `legende`.
3. **Vérifier (Claude, 5 min).** `python outils/carrousel-ia.py verifier outputs/carrousels/<slug>/slides.json` jusqu'à « Livre de règles : tout passe. » Il bloque : script incomplet, chaîne cassée, slide qui ouvre par « Et donc », action ailleurs qu'en dernière slide, titre de plus de 6 mots, texte de plus de 20 mots, 3 lignes ou 2 phrases, plus d'un mot en accent, phrase de plus de 16 mots, slide à garder de plus de 55 mots, couverture ou fin de plus de 26 mots, tiret long, « glisse ». Ensuite, deux lecteurs à froid (deux sous-agents neufs) lisent chaque slide seule, avec la couverture pour seul contexte : le client fatigué le soir, puis un ado de 14 ans. Chacun la lit deux fois et la redit en une phrase. Une slide qu'un même lecteur rate deux fois se réécrit. Feuillette aussi le texte très vite : la taille, le poids et la quantité de texte doivent changer d'une slide à l'autre, sinon rien ne se passe pour l'œil.
4. **La porte avant crédit (Claude).** `slides.json` passe par `board-textes`, chaque conseil affirmation par affirmation. Le `board.md` s'écrit à côté. Aucun crédit avant le verdict vert sur ce texte exact.
5. **Les prompts (Claude, 5 min).** `python outils/carrousel-ia.py prompts outputs/carrousels/<slug>/slides.json --credit <prix d'une image> --budget <reste du mois>`. Il refuse sans verdict vert, puis écrit `prompts/NN.txt` et `requests.json` : format 4:5, modèle, énergie du rôle, scène, palette et polices de la charte (selon le fond de la slide), ambiance tirée des mots de la charte, texte exact à écrire, recette de `style-maison.md`, interdits. Il annonce le coût et s'arrête si le budget ne suffit pas. Si le générateur écrit mal le texte, ajoute `--sans-texte` : l'image garde le haut libre, et le texte se pose ensuite en local avec `carrousel.py` (champ `image` des styles `podcast`, `reel` ou `edito`).
6. **Une couverture test (Claude puis l'utilisateur, 5 min).** Génère la couverture seule et montre-la. L'utilisateur dit oui ou corrige. Sa note devient une règle de « Goût » avant la suite.
7. **Le lot (Claude, 15 min).** Génère le reste et range chaque image dans `brut/NN.png` (ou `.jpg`, `.webp`). Un envoi refusé par le générateur n'est souvent pas facturé : vérifie l'historique des crédits avant de renvoyer. Puis `python outils/carrousel-ia.py finir outputs/carrousels/<slug>` sort `slide-NN.jpg` en 1080x1350. Regarde la planche, puis chaque bloc de texte au zoom, lettre par lettre, espaces avant « ? » et « : » compris. Relis ensuite toute la planche en directeur artistique : désigne les deux slides les plus faibles et refais seulement celles-là, deux reprises au plus. Une slide avec visage ne se reprend jamais à partir d'une image générée : régénère-la depuis la photo d'origine. Un défaut minuscule sur un fond uni se retouche en local, sans crédit.
8. **Revue, banque et publication (Claude puis l'utilisateur).** Le dossier passe par la même revue que les carrousels locaux (`python outils/file.py revue`, style `image-ia`), puis la file et `distribution-api`. Les slides que l'utilisateur aime entrent dans la banque : `python outils/carrousel-ia.py banque outputs/carrousels/<slug>/slides.json 2,3`. Pour la réutiliser avec un texte neuf, mets son nom dans le champ `image` d'une slide : elle part en référence du prompt. Sur TikTok, passe `--contenu-ia` à `tiktok-photo.py`. Note le coût réel du lot à côté du budget dans « Modèles ».
9. **La rotation (Claude, 1 min).** Un carrousel sur deux change de modèle (`affiche`, puis `verre`), et la file alterne les carrousels générés avec les styles locaux (rotation de `outputs/carrousels/reseaux.json`).

## Test
`python outils/carrousel-ia.py --test` écrit « AUTO-TEST OK ». Un vrai carrousel existe : `verifier` dit « tout passe », son `board.md` vert est daté avant la première image, ses slides sont en 1080x1350, et le coût réel du lot est noté à côté du budget.

## Pièges vécus
- **Le texte retouché après les images.** Tout le lot à refaire. Le board passe avant, et sa porte vérifie que le texte n'a pas bougé d'une virgule.
- **Un conseil qui n'était pas celui de l'entrepreneur.** Un exemple lu dans une fiche de vidéo a été recopié dans un carrousel, alors que sa méthode disait l'inverse. Chaque conseil trace vers sa source et vers sa méthode, et le board le vérifie.
- **Des slides obscures une fois générées.** Une belle image à décoder, ou un récapitulatif qui ajoutait un objet jamais annoncé : refusés par l'entrepreneur. D'où les plafonds de mots et les lecteurs à froid avant tout crédit.
- **Le visage qui « cuit ».** Une image générée du visage remise en entrée se dégrade un peu à chaque passage. Toujours la photo d'origine ; l'outil refuse une référence prise dans les images générées.
- **Des petites images qui sentent l'IA.** Les vignettes générées dans la slide faisaient faux. Génère-les à part, avec la recette de la marque, puis place-les.
- **Une icône au hasard.** Un symbole quelconque à la place de l'élément de marque, des puces différentes d'une slide à l'autre : seuls le logo et les éléments de la marque, rangés dans la bibliothèque pour être réutilisés.
- **Un modèle choisi sur une seule belle image.** Au banc, seuls quelques modèles ont plu à l'œil de l'entrepreneur, et pas les mêmes pour le visage et pour les scènes. Compare sur planche avant de choisir.
- **Une recette « film ancien » chargée.** Rayures et poussière sortaient en couche uniforme et se repéraient. Teste toute recette sur quatre sujets avant de l'adopter.
- **Un mot qui déclenche le filtre du générateur.** Le même prompt a été refusé plusieurs fois à cause d'un seul mot. Remplace le mot, et vérifie que les refus n'ont pas été facturés.
- **Les images des comptes d'inspiration.** Elles servent à regarder la lumière, jamais de référence de génération ni de publication.
- **Des lettres collées et un accent qui touche la ligne du dessus.** Deux petits défauts réparés en local, sans crédit, plutôt que de régénérer la slide.

## Entretien dans le temps
- Chaque note de l'utilisateur sur une image devient une ligne de « Goût » dans `style-maison.md`, et une règle de l'outil quand elle se mesure.
- La banque grandit avec les slides aimées ; l'outil empêche une image de revenir avant 5 autres carrousels, ou sous le même titre qu'avant.
- Chaque mois, `mesure-et-apprentissage` compare le coût et les résultats (enregistrements et partages pour 100 vues) aux carrousels locaux. Si les carrousels générés ne font pas mieux, réduis-les.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (générateur, coût, goût visuel, modèles retenus), et ajoute la ligne dans `wiki/maps/routage.md`. Propose ensuite `accroches`.
