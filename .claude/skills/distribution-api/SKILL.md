---
name: distribution-api
description: "Publie et programme le contenu partout par API (un CRM multi-réseaux comme GoHighLevel, ou Buffer, Metricool, les API natives) au lieu de copier-coller à la main : brouillons, programmation, vidéo YouTube, podcast. Utiliser quand l'utilisateur dit « publie partout », « programme mes posts », « distribue ma vidéo ». Pas pour écrire le contenu (utiliser le skill de la pièce)."
---
# Distribution par API

## Pourquoi
Au début du système d'origine, chaque post demandait plusieurs clics par réseau et par jour : intenable, donc rien ne sortait. Le passage à un CRM qui publie sur plusieurs réseaux par une seule API a tout changé : Claude programme, l'entrepreneur garde un délai pour relire et supprimer, et sans action de sa part le post part seul. Les réseaux ont chacun leurs pièges (une vidéo refusée si elle vient d'un domaine inconnu, une limite d'images, un carrousel qui exige une vidéo) : ils sont notés une fois et gérés dans le code.

## Prérequis
- Des pièces validées par le board (`board-textes`, bloc C). Rien ne se programme sans verdict vert.
- Un outil de publication au choix : GoHighLevel (Social Planner), Buffer, Metricool, ou les API natives (YouTube Data API, Meta Graph API pour Instagram, Facebook et Threads).
- Bloc A : l'endroit des secrets (clé d'API hors du vault et hors de Git).
- Python 3.

## Interview
Lis d'abord : `wiki/maps/machine-contenu.md` (réseaux, cadence), les outils déjà payés dans `wiki/maps/moi.md`. Puis demande :
1. « As-tu déjà un outil qui publie sur plusieurs réseaux ? » Si non, présente les options et leurs coûts, il choisit. Range dans `wiki/maps/distribution.md`, section « Outil ».
2. « Quels comptes sont branchés dedans ? » Il les connecte lui-même (connexions OAuth). Guide-le clic par clic dans l'interface de l'outil.
3. « Tu veux un délai de relecture avant que ça parte ? Combien d'heures ? » Range dans « Règles ».
4. « Tu veux un podcast audio de tes vidéos ? » Si oui, l'étape 5 s'ajoute.

## Construire
1. **La clé** (l'utilisateur, 5 min). Il crée une clé d'API dans son outil (GoHighLevel : Paramètres, Clés API privées, avec les droits sur les réseaux sociaux). Il la colle dans le fichier de secrets du bloc A, jamais dans une conversation partagée ni dans le vault.
2. **Les comptes** (Claude, 10 min). Liste les comptes branchés par l'API (GoHighLevel : `GET https://services.leadconnectorhq.com/social-media-posting/<locationId>/accounts`, en-têtes `Authorization: Bearer <clé>` et `Version: 2021-07-28`). Écris la table réseau vers identifiant de compte dans `wiki/maps/distribution.md`.
3. **Le script de publication** (Claude, 20 min). `outils/publier.py` lit une file (`outputs/file-publication/AAAA-MM-JJ.json` : réseau, texte, médias, date), contrôle chaque entrée (verdict du board présent, longueur par réseau, lien en première réponse là où il pénalise), puis programme. Par défaut il tourne à blanc et affiche ce qu'il ferait ; `--live` envoie. Il écrit un journal (envoyé, refusé, raison) et ne renvoie jamais une entrée déjà envoyée.
4. **Le premier envoi** (Claude puis l'utilisateur). Un seul post, sur un seul réseau, en brouillon ou programmé à plus tard. L'utilisateur le voit dans l'outil. Ensuite seulement, la file complète.
5. **Vidéo longue et podcast** (Claude, 20 min, option). YouTube : envoi par l'API YouTube Data (titre, description, chapitres, miniature, programmé) ou par l'outil multi-réseaux. Podcast : extrais l'audio (`ffmpeg -i video.mp4 -vn -c:a libmp3lame -b:a 128k episode.mp3`), publie un flux RSS que tu possèdes (un stockage public plus un fichier XML), puis l'utilisateur soumet le flux une fois aux annuaires (Apple Podcasts, Spotify, Deezer, Amazon Music). L'épisode s'ouvre sur l'accroche, sans salutation.
6. **La tâche** (Claude, 10 min). Une tâche planifiée (bloc F) vide la file à heure fixe, avec un résumé au rapport du matin. Une alerte seulement si l'outil se déconnecte.

## Test
Un post programmé par le script apparaît dans l'outil sur le bon réseau à la bonne heure, et le journal montre la même entrée refusée au deuxième passage.

## Pièges vécus
- Les validations manuelles « en revue » sur chaque réseau : trop de clics, abandon. Programme avec un délai de relecture et laisse partir.
- Une vidéo refusée parce qu'elle était hébergée sur un domaine non vérifié : envoie d'abord le fichier dans la médiathèque de l'outil.
- Un réseau qui limite le nombre d'images, un autre qui refuse un carrousel sans vidéo : écris ces limites dans la table des comptes.
- Une tâche planifiée expirée qui a coupé la publication plusieurs jours sans bruit : le gardien du bloc F surveille la file.
- Les gestes qu'aucune API ne fait (épingler un commentaire, écran de fin YouTube, test de miniatures) : liste-les dans la feuille du jour J.

## Entretien dans le temps
Le journal de publication se lit chaque semaine avec `mesure-et-apprentissage`. Chaque nouveau refus d'un réseau devient une règle dans le script. Revois les connexions OAuth quand l'outil prévient d'une expiration.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (outil choisi, délai de relecture). Propose ensuite `images-de-marque`.
