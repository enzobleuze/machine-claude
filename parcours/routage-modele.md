---
title: "Routage : ce que je dis, ce que Claude lance"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [routage, commandes]
sources: ["[[blueprint]]"]
---
# Routage

Je ne me souviens pas des commandes, c'est normal. Claude lit cette table : intention claire, il lance ; intention floue, une seule question. Chaque nouveau skill ou outil s'ajoute ici. Liens : [[blueprint]], [[parcours]], [[index]].

| Ce que je dis | Ce que Claude lance |
|:-|:-|
| « on continue le parcours », « on reprend », « où on en est », « je suis perdue » | `/reprise` |
| « fais une passation », « on change de chantier » | `/passation` |
| « on arrête », « fin de session » | `/fin` |
| « cherche dans mes notes », « qu'est-ce que j'ai sur X » | `/cerveau X` |
| « note cette idée », « pour plus tard » | `/idee texte` |
| « j'ai vendu », « X m'a payé » | `/vente montant prénom` |
| « ingère », « j'ai déposé dans raw » | `/ingest` (skill `ingestion-fichiers`) |
| « audit du wiki » | `/lint` (skill `lint-wiki`) |
| « j'hésite », « aide-moi à décider » | skill `comite-decision` |
| « valide ce texte », « avant de publier » | skill `board-textes` |
| « approfondis mon client idéal », « qu'est-ce que mes clients ressentent vraiment ? », « mon contenu ne touche personne » | skill `dossier-client-ideal` |
| « NotebookLM se déconnecte », « répare la connexion NotebookLM » | skill `notebooklm-brancher` (connexion durable et maintien) |
| « branche Linear », « explique-moi Linear », « comment marchent mes tâches ? » | skill `taches-source-unique` (clé personnelle, visite guidée) |
| « mes couleurs », « ma charte », « je n'ai pas de logo ni de couleurs », « change mes couleurs partout » | skill `charte-graphique` |
| « ouvre le cockpit », « mode démo du cockpit », « branche mon agenda au cockpit », « branche Linear au cockpit », « relève mes réseaux », « dossier complet de X » | skill `cockpit-app` |
| « coupe les silences », « habille ma vidéo », « revois le montage » | skill `montage-video-code` |
| « fais un Reel avec cette vidéo », « gabarit rythme », « gabarit éditorial » | skill `reels-et-shorts` |
| « shorts <vidéo> OK » | skill `decoupe-shorts` |
| « ma caméra filme flou », « la vidéo saccade » | skill `tournage` |
| « la musique couvre ma voix », « trouve un son » | skill `sons-et-musique` |
| « fais un carrousel », « une pub statique », « revue des carrousels », « carrousel du jour », « oui 1, 4 » (après la revue) | skill `carrousel-html` (images IA : `carrousel-image-ia`) |
<!-- hors-routage: bibliothecaire (mode toujours actif, pas une brique) -->
