---
name: article-lettre-seo
description: "Écrit un article de blog comme une lettre à une vraie personne, puis le rend trouvable (SEO et citations par les IA). Utiliser quand l'utilisateur dit « écris un article sur X », « mon blog », « fais du SEO ». Pas pour produire des articles en masse (la leçon de cette brique le déconseille)."
---
# Article lettre et SEO

## Pourquoi
Le système d'origine a généré pendant des mois des dizaines d'articles optimisés, publiés seuls chaque jour. En trois mois, tous ensemble ont rapporté presque aucun clic venu de Google. Les articles qui comptaient avaient été écrits pour une vraie personne, avec une vraie scène. La production en masse a été arrêtée et les articles générés passés en brouillon. La leçon : une lettre écrite pour une personne précise bat l'article optimisé, et la source du texte doit être humaine (une transcription de vidéo, un vrai échange).

## Prérequis
- `banque-idees`, bloc D (voix, client idéal), bloc C (`board-textes`).
- Un site (WordPress, GoHighLevel, Ghost ou autre) avec un accès API, ou un brouillon à coller à la main.
- De préférence une vidéo déjà tournée sur le sujet (`youtube-systeme`) : sa transcription est la meilleure source.
- Option : skills SEO publics (audit, schéma) pour la partie technique.

## Interview
Lis d'abord : la fiche voix, la banque, la liste des pages existantes (sitemap ou export), les chiffres de recherche s'il y en a. Puis demande :
1. « À qui précisément écris-tu cette lettre ? Une personne, une situation. » Range dans `outputs/articles/<slug>/brief.md`.
2. « As-tu une vidéo, un appel ou un message sur ce sujet ? » C'est la source.
3. « Quel lien ou quelle ressource veux-tu offrir à la fin ? » Un seul, qui existe déjà.
4. « As-tu accès à Google Search Console ? » Si oui, guide la connexion pour mesurer. Range l'accès dans les secrets du bloc A, jamais dans le vault.

## Construire
1. **La source humaine** (Claude, 10 min). Prends la transcription de la vidéo ou l'échange réel. Sans source humaine, propose d'abord d'enregistrer un vocal de 10 minutes sur le sujet.
2. **La lettre** (Claude, 20 min). Écris à la personne du brief, dans la voix du bloc D. Ouvre sur sa scène précise, réponds à sa question dans les 150 premiers mots, donne le principe et l'action du soir, finis sur la ressource. Garde les phrases réelles de la source.
3. **Le squelette trouvable** (Claude, 15 min). Ajoute sans casser la lettre : un titre qui contient la question telle qu'on la tape, un encadré « En bref » de 3 à 5 points en tête, des intertitres qui sont de vraies questions, une FAQ de 4 à 6 questions réelles (les « autres questions posées » de Google), la vidéo intégrée, 2 ou 3 liens vers ses autres pages. Pour être cité par les IA : sous chaque intertitre, une réponse directe et complète en 2 à 4 phrases.
4. **La porte** (Claude). Board des textes (`board-textes`, bloc C). Rien ne part sans verdict vert.
5. **Publication en brouillon** (Claude, 10 min). Pousse l'article en brouillon par l'API du site. L'utilisateur relit et publie lui-même les premières fois. Si une vidéo plus récente couvre le même sujet, republie au même lien plutôt que d'en créer un nouveau.
6. **La mesure** (Claude, 5 min). Inscris l'article au registre de `mesure-et-apprentissage` : clics et impressions à 30 et 90 jours.

## Test
L'article publié a une source humaine citée dans son brief, un verdict vert du board, et la question tapée par le client apparaît dans le titre et dans la première réponse.

## Pièges vécus
- Le volume : un article par jour écrit par l'IA a donné presque zéro trafic. Commence par un article par vidéo, au plus.
- Un score d'outil SEO au vert sur un texte que personne ne lirait jusqu'au bout. Le vrai test reste : est-ce que ça change quelque chose pour la personne qui lit ce soir ?
- Des liens ajoutés automatiquement à l'intérieur du code d'une image ou d'un tableau ont cassé des blocs de l'éditeur. Relis le rendu final, pas seulement le texte.
- Un outil de « réécriture humaine » a inventé des études chiffrées. Aucun chiffre sans source vérifiée (`controle-verite`, bloc C).

## Entretien dans le temps
Tous les 3 mois : un article sans aucun clic est réécrit depuis une nouvelle source humaine ou passé en brouillon. Ne relance jamais une production automatique sans données qui la justifient.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la banque (« Pièces faites »). Propose ensuite `posts-reseaux`.
