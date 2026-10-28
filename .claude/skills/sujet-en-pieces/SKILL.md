---
name: sujet-en-pieces
description: "Transforme un seul sujet en plusieurs pièces (vidéo longue, Shorts, posts, carrousel, email, article) par une chaîne fixe. Utiliser quand l'utilisateur dit « sujet complet sur X », « décline ce sujet partout », « le package de la semaine ». Pas pour une pièce seule (utiliser le skill de la pièce)."
---
# Un sujet en plusieurs pièces

## Pourquoi
Seul et pressé, l'entrepreneur d'origine ne pouvait pas inventer un sujet par réseau. La chaîne part d'un seul sujet par semaine et le décline partout : la pièce mère d'abord, les autres en dérivent. Le système a aussi appris l'ordre. Au début, la pièce mère était un article généré, et presque personne ne l'a lu. Elle est devenue la vidéo longue, dont la transcription nourrit tout le reste avec les vrais mots de la personne.

## Prérequis
- `banque-idees` (le sujet en sort), bloc C (`board-textes`), bloc D (voix, offre, ressource gratuite ou mot-clé).
- Les skills des pièces voulues : `youtube-systeme`, `decoupe-shorts`, `posts-reseaux`, `carrousel-html`, `article-lettre-seo`, l'email du bloc D, `distribution-api`.

## Interview
Lis d'abord : `wiki/maps/machine-contenu.md` (cadence, réseaux), la banque, la fiche voix. Puis demande :
1. « Quelle est ta pièce mère : une vidéo, un podcast, une lettre écrite ? » Choisis ce qu'il aime faire, il le tiendra. Range dans `machine-contenu.md`, section « Chaîne ».
2. « Sur quels réseaux publies-tu vraiment ? » Garde seulement ceux-là.
3. « Quelle action veux-tu après chaque pièce ? » (un mot-clé en commentaire, un lien, une réponse). Une seule action par pièce.

## Construire
1. **Le cœur du sujet** (Claude, 15 min). Écris `outputs/sujets/<slug>/coeur.md` : la question mot à mot de la banque, la situation précise du client, le principe unique en une phrase, la preuve (une scène vécue, le principe, la source), l'action du soir. Toutes les pièces partent de ce fichier, aucune n'invente un autre principe.
2. **La pièce mère** (Claude puis l'utilisateur). Lance le skill de la pièce mère. Si c'est une vidéo, aucune dérivée ne s'écrit avant la transcription du tournage : les meilleures phrases sont celles qu'il a dites devant la caméra.
3. **Les dérivées** (Claude, 20 min chacune). Dans cet ordre : Shorts (`decoupe-shorts`), carrousel (`carrousel-html`, le passage qui se tient seul), posts courts (`posts-reseaux`, les phrases qu'on voudrait garder), email (la lettre au client), article (`article-lettre-seo`, la transcription remise en lettre). Chaque pièce prend la forme de son réseau et garde les mots réels de la pièce mère.
4. **La porte** (Claude). Chaque pièce passe par le board des textes (`board-textes`, bloc C) avant toute publication. Une pièce sans verdict vert reste dans `outputs/sujets/<slug>/` avec la mention « board non passé ».
5. **Le calendrier** (Claude, 10 min). Écris `outputs/sujets/<slug>/calendrier.md` : quelle pièce part où et quand. La publication passe par `distribution-api`.

## Test
Pour un sujet, le dossier contient `coeur.md`, la pièce mère et au moins 3 dérivées, chacune avec son verdict vert du board, et toutes portent le même principe.

## Pièges vécus
- Des dérivées écrites avant le tournage : elles disaient autre chose que la vidéo. Attends la transcription.
- Un package complet chaque jour : trop pour une personne seule, plus rien n'était relu. Un sujet par semaine suffit au départ.
- Une action finale qui change d'un réseau à l'autre sans raison : le lecteur ne sait plus quoi faire.

## Entretien dans le temps
Chaque semaine, `mesure-et-apprentissage` dit quelle dérivée a le mieux marché. Une dérivée qui ne rapporte rien pendant un mois sort de la chaîne.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la ligne du sujet dans la banque (« Pièces faites »). Propose ensuite le skill de la pièce mère choisie.
