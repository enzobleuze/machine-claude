---
name: carrousel-html
description: "Fabrique des carrousels (Instagram, LinkedIn, Facebook, TikTok photo) rendus en local depuis un fichier JSON, sans crédit d'image. Utiliser quand l'utilisateur dit « fais un carrousel », « transforme ma vidéo en carrousel », « carrousel simple ». Pas pour un carrousel aux images générées par IA (utiliser carrousel-image-ia)."
---
# Carrousel HTML local

## Pourquoi
Les carrousels aux images générées coûtaient des crédits et demandaient beaucoup de reprises. Le système d'origine a ajouté un moteur local : le texte et la mise en page vivent dans un JSON, du code les rend en images, et il ne coûte rien. Il sert surtout à recycler la vidéo de la semaine (captures et phrases dites), à poser une conversation façon messages, ou un plan en étapes. Un carrousel par jour est devenu tenable.

## Prérequis
- Bloc D (voix, mot-clé ou ressource), bloc C (`board-textes`).
- Chrome, Chromium ou Edge installé (déjà là sur la plupart des ordinateurs). Python 3.
- Pour les captures de vidéo : ffmpeg (`outils/planche.py` et la commande ffmpeg de l'étape 2).
- Outil joint : `outils/carrousel.py` (testé : `python outils/carrousel.py --test`).

## Interview
Lis d'abord : la charte de marque s'il en a une (`images-de-marque`), la fiche voix, les carrousels qu'il a aimés. Puis demande :
1. « Montre-moi 2 ou 3 comptes dont tu aimes les carrousels. » Range dans `wiki/maps/carrousels.md`, section « Références ». Tu copieras la mise en page, jamais les textes.
2. « Tes couleurs et tes polices, si tu en as ? » Sinon propose deux thèmes (sombre, clair) et laisse-le choisir. Range dans le thème du JSON modèle.
3. « Quelle action en dernière slide ? » (enregistrer, écrire un mot en commentaire, un lien en bio). Une seule.
4. « Ton pseudo pour le pied de page ? »

## Construire
1. **Installer l'outil** (Claude, 5 min). Copie `outils/carrousel.py` dans `outils/` de son vault. Lance `python outils/carrousel.py --test`. Il doit écrire « AUTO-TEST OK ». Si le navigateur n'est pas trouvé, pose la variable `NAVIGATEUR` sur le chemin de Chrome ou Edge (Windows : `setx NAVIGATEUR "C:\Program Files\Google\Chrome\Application\chrome.exe"` ; Mac et Linux : `export NAVIGATEUR=...` dans le profil du terminal).
2. **Les images** (Claude, 10 min). Pour recycler une vidéo : `ffmpeg -ss 95.5 -i video.mp4 -frames:v 1 img/01.jpg` à chaque instant choisi dans la transcription, ou `python outils/planche.py video.mp4 --n 16 -o planche.jpg` pour choisir d'un coup d'œil. Choisis des images où la personne a les yeux ouverts.
3. **Le JSON** (Claude, 15 min). `python outils/carrousel.py exemple > outputs/carrousels/<slug>/slides.json`, puis remplis. Déroulé qui a marché : une couverture qui crée l'envie de savoir la suite, une slide 2 qui répond à la couverture, le problème, le mécanisme, ce qu'on fait ce soir, l'objection, l'appel final. La réponse complète n'arrive jamais trop tôt. `*mot*` met un mot en couleur, `\n` passe à la ligne.
4. **La porte** (Claude). Le texte du JSON passe par `board-textes` (bloc C) avant le rendu final.
5. **Rendre** (Claude, 2 min). `python outils/carrousel.py rendre outputs/carrousels/<slug>/slides.json`. L'outil refuse une slide trop longue (35 mots par défaut, `max_mots` dans le JSON) ou une image manquante. Vérifie le résultat avec une planche (`python outils/planche.py "outputs/carrousels/<slug>/png/*.png" -o planche.jpg`) avant de l'ouvrir en grand.
6. **Publier** (Claude). Par `distribution-api`. Le même carrousel peut partir sur plusieurs réseaux.

## Test
`python outils/carrousel.py --test` écrit « AUTO-TEST OK », et un vrai carrousel de 6 à 10 slides au format 1080x1350 existe avec son verdict vert du board.

## Pièges vécus
- Une phrase belle mais trop imagée ou une formule abstraite : le lecteur fatigué ne comprend pas. Fais lire le texte « à froid » à deux lecteurs simulés (le client fatigué le soir, un ado de 14 ans) ; une slide qu'ils ne comprennent pas se réécrit.
- Un récap qui parle d'une étape jamais annoncée : le récap ne fait que répéter ce qui a été dit.
- Des mentions inutiles sur une slide (« situation type », « mise en scène »), des noms, de fausses interfaces d'application : retirées pour toujours.
- Des carrousels faits de la transcription d'une vidéo en blocs : ennuyeux. Le texte d'un carrousel vend une idée, il ne recopie pas.
- Certains réseaux refusent un carrousel par une API qui attend une vidéo : garde une voie manuelle ou un outil de navigateur pour ceux-là.

## Entretien dans le temps
Chaque style de carrousel garde son exemple validé dans `wiki/maps/carrousels.md`. `mesure-et-apprentissage` compare les styles (enregistrements et partages pour 100 vues). Un style qui perd sort de la rotation.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (thème et références). Propose ensuite `carrousel-image-ia` s'il veut des visuels générés, sinon `accroches`.
