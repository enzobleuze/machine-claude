---
name: charte-graphique
description: "Pose la charte graphique de la marque (couleurs, polices, logo, ambiance) dans un fichier unique que lisent le cockpit, les carrousels, les vidéos et les images. Reprend une identité qui existe déjà, ou en propose trois à choisir sur un aperçu, ou part d'une charte simple. Utiliser quand l'utilisateur dit « mes couleurs », « ma charte », « je n'ai pas de logo ni de couleurs », « change mes couleurs partout ». Pas pour le style des photos générées (utiliser images-de-marque)."
---
# La charte graphique

## Pourquoi
Le cockpit, les carrousels et les vidéos sont trois outils écrits à des moments différents. Sans charte commune, chacun garde ses propres couleurs et la marque ne se reconnaît plus d'une pièce à l'autre. Dans le système d'origine, une charte écrite (une couleur d'accent, deux polices, des règles courtes) a rendu chaque pièce reconnaissable au premier coup d'œil. Ici, la charte vit dans un seul fichier : on la change à un endroit, et tous les outils suivent.

## Prérequis
- Bloc A fait (le vault existe). L'entretien fondateur aide (bloc D) : il dit pour qui on écrit et sur quel ton.
- Python 3.10 ou plus récent. Aucun coût.
- Facultatif : le logo (PNG à fond transparent ou SVG), et les codes couleur si une identité existe déjà (Canva, site, document d'un graphiste).

## Interview
Lis d'abord : `wiki/business/fondateur.md`, `wiki/maps/style-maison.md` s'il existe, `bibliotheque/marque/` s'il existe.

Puis demande, une question à la fois :
1. « Tu as déjà une identité visuelle : un logo, des couleurs, des polices ? Où sont-ils ? » Si oui : demande les codes couleur (dans Canva : Kit de marque ; sur un site : Claude lit la feuille de style), les noms des polices, et le fichier du logo. Range le logo dans `bibliotheque/marque/`.
2. Sinon : « Tu préfères que je te propose trois chartes à choisir sur un aperçu, ou qu'on parte sur une charte simple tout de suite ? Tu pourras la changer quand tu veux. »
3. Pour les propositions, trois questions de goût, une à la fois :
   - « Trois mots pour l'ambiance que tu veux faire ressentir ? » (exemple : chaleureux, posé, lumineux)
   - « Des couleurs que tu aimes, et des couleurs que tu ne supportes pas ? »
   - « Deux ou trois marques, comptes ou sites dont tu aimes le style ? » (Claude regarde leurs couleurs dominantes, sans rien copier)
4. « Plutôt clair (fond clair, texte foncé) ou plutôt sombre ? » C'est le thème principal ; l'autre est calculé tout seul.

Range les réponses dans `wiki/business/charte.md`, section « Interview ».

## Construire
1. **Copier l'outil (1 min).** Claude copie `outils/charte.py` dans `scripts/charte.py` du vault, puis `python scripts/charte.py --test` doit imprimer `AUTO-TEST OK`.
2. **Écrire la charte (10 min).** Trois cas :
   - Identité existante : Claude écrit `bibliotheque/marque/charte.json` avec ses codes (modèle ci-dessous).
   - Propositions : `python scripts/charte.py proposer -o bibliotheque/marque/propositions` écrit quatre chartes prêtes (simple, lumineux, doux naturel, sombre élégant). Claude en ajoute une sur mesure, tirée des trois mots et des couleurs aimées : `bibliotheque/marque/propositions/sur-mesure.json`, puis relance `proposer` avec ce fichier en plus. Il ouvre `apercu.html` dans le navigateur : chaque charte y montre une carte du cockpit, une diapo de carrousel et un sous-titre de vidéo, en clair et en sombre. La personne choisit ; Claude copie son choix en `charte.json`.
   - Simple tout de suite : Claude copie `propositions/simple.json` en `charte.json`.
   Le modèle :
   ```json
   {"nom": "Nom de la marque", "theme": "clair",
    "couleurs": {"fond": "#fbf6ef", "texte": "#2a211b", "accent": "#c4572e", "accent_2": "#3d7a6f"},
    "polices": {"titres": "Fraunces", "texte": "Inter"},
    "logo": "bibliotheque/marque/logo.png", "rayon": 10, "mots": ["chaleureux", "solaire", "accueillant"]}
   ```
   `accent_2`, `logo`, `rayon` et `mots` sont facultatifs. Les polices viennent de Google Fonts (gratuites) ou sont installées sur l'ordinateur.
3. **Vérifier (2 min).** `python scripts/charte.py valider` doit dire `CHARTE OK`. S'il annonce un accent ajusté, c'est normal : le script fonce ou éclaircit la couleur juste assez pour qu'elle reste lisible.
4. **Construire les fichiers partagés (1 min).** `python scripts/charte.py construire` écrit `bibliotheque/marque/charte.css` (variables pour les pages : cockpit, carrousels, sous-titres) et `bibliotheque/marque/charte-jetons.json` (les mêmes valeurs pour les scripts). Puis `python scripts/charte.py apercu` : Claude montre l'aperçu final et attend le oui.
5. **La fiche lisible (5 min).** Claude écrit `wiki/business/charte.md` : les trois mots, chaque couleur avec son usage (fond, texte, accent pour un mot fort ou un chiffre, accent 2 pour un détail), les polices, le logo, ce qu'on évite, la date, et trois [[liens]] (fondateur, style-maison, parcours).
6. **La règle dans le cœur (2 min).** Claude ajoute au `CLAUDE.md` : « Tout visuel (cockpit, carrousel, vidéo, image) lit `bibliotheque/marque/charte-jetons.json` ou `charte.css`. Aucune couleur ni police écrite en dur. Changer de charte : modifier `charte.json`, puis `python scripts/charte.py construire`. »

## Test
`python scripts/charte.py valider` sort 0, `charte.css` et `charte-jetons.json` existent, et la personne a dit oui en voyant l'aperçu.

## Pièges vécus
- **Une couleur vive hors charte sur des diapos de vidéo.** Elle a été jugée agressive et retirée : chaque couleur à l'écran sort de la charte, même pour une alerte.
- **Un accent illisible en thème clair.** La même couleur dorée tenait sur fond sombre et disparaissait sur fond clair : il a fallu une version plus foncée pour le texte. Le script la calcule seul (contraste 3,5 au moins pour l'accent, 4,5 pour le texte).
- **Une police qui ne se charge pas.** Hors connexion, la page retombait sur une police par défaut sans prévenir. Chaque police a une police de secours proche dans `charte.css`.
- **Des miniatures hors charte.** Un mot vide écrit en gros dans une couleur au hasard : refaites dans la charte, elles ont tout de suite eu l'air de la même marque.
- **Changer les couleurs à la main dans chaque outil.** Trois outils, trois oublis. Un seul fichier, et `construire`.

## Entretien dans le temps
- Chaque remarque de la personne sur une couleur ou une police devient une ligne de `wiki/business/charte.md`, puis une retouche de `charte.json` et un `construire`.
- Après un changement de charte, relancer les rendus en cours (carrousels de la file, vidéos pas encore publiées). Le cockpit suit au prochain rechargement.

## Après
Coche la brique dans `wiki/maps/parcours.md`, une ligne dans `log.md`. Propose ensuite `cockpit-app` (bloc D), puis `carrousel-html` et `montage-video-code` (bloc E), qui liront tous cette charte.
