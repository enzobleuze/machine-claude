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
<!-- hors-routage: bibliothecaire (mode toujours actif, pas une brique) -->
