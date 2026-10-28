---
name: essais-multiples
description: "Met en place les essais multiples d'une même vidéo (Trial Reels Instagram ou équivalent) : chaque essai change une seule chose, lecture des chiffres à 24 h et 72 h, gagnant republié. Fournit un registre testé. Utiliser quand l'utilisateur dit « teste plusieurs versions », « Trial Reels », « quelle version a gagné ». Pas pour les tests de miniatures YouTube (utiliser youtube-systeme)."
---
# Essais multiples

## Pourquoi
Instagram propose les Trial Reels : un essai part chez des non-abonnés sans toucher le profil. Le système d'origine s'en sert comme d'un labo. Ses chiffres ont montré que tout se joue sur le premier petit lot de test (de l'ordre d'une centaine de personnes) et sur le saut avant 3 secondes : sous environ 40 % de départs, la diffusion continue ; bien au-dessus, elle s'arrête vite. Une vidéo filmée donne donc plusieurs essais, chacun change une seule chose, et le gagnant est republié en Reel normal. Des essais trop proches les uns des autres ont aussi été bloqués : l'écart entre versions doit être réel.

## Prérequis
- `reels-et-shorts` ou `decoupe-shorts` (des vidéos montées), `accroches` (plusieurs ouvertures).
- Un compte Instagram professionnel avec Trial Reels (ou une plateforme qui permet un test équivalent).
- Python 3. Outil joint : `outils/essais.py` (testé : `python outils/essais.py --test`).
- Option : publication par API (`distribution-api`) et tâche planifiée (bloc F) pour lire seul.

## Interview
Lis d'abord : `wiki/maps/reels.md`, la banque d'accroches, `wiki/maps/machine-contenu.md`. Puis demande :
1. « Combien d'essais peux-tu publier par jour ? » Conseille 3 à 5 au plus : au-delà, des créateurs ont reçu des blocages des essais. Range dans `wiki/maps/essais.md`, section « Rythme ».
2. « Combien d'ouvertures filmes-tu par vidéo ? » Range dans « Rythme ».
3. « Tu publies toi-même ou tu veux que je le fasse par l'API ? » Range dans « Publication ».
4. « À partir de combien de vues une vidéo mérite ton profil ? » Propose le seuil automatique de l'outil (au moins 1 000 vues, et il monte avec le compte).

## Construire
1. **Installer le registre** (Claude, 5 min). Copie `outils/essais.py` dans `outils/` du vault, lance `python outils/essais.py --test` (« AUTO-TEST OK »). Pose `ESSAIS_REGISTRE` sur `outputs/essais/essais.json` si tu veux le registre ailleurs. Règles réglables en tête du fichier : `LIMITE_VUES_24H`, `ECART_SAUT`, `PLANCHER_PUBLIC`.
2. **Le plan d'essais** (Claude, 10 min par vidéo). Écris `outputs/essais/<video>.md` : un code par essai (A1, A2...), la seule chose qui change (accroche, texte à l'écran, fond, musique), le reste identique. Ordre conseillé des variables : l'accroche d'abord, puis le texte à l'écran, puis le reste. Les variantes qui ne changent que le fond restent en réserve et ne partent que si leur version de base gagne.
3. **Publier et inscrire** (l'utilisateur ou Claude). À chaque essai publié : `python outils/essais.py ajouter <video> A1 --change "accroche : la scène du dîner"`. Le registre refuse un doublon : un essai ne part jamais deux fois. Laisse au moins 2 h entre deux essais.
4. **Relever** (Claude, 5 min par passage). `python outils/essais.py a-lire` dit ce qui est dû. L'utilisateur colle ou lit les chiffres de l'application (vues, pourcentage parti avant 3 s, partages, commentaires) ; Claude fait `python outils/essais.py relever <video> A1 --a 24 --vues 410 --saut 38 --partages 9`. Avec l'API, une tâche planifiée le fait seule.
5. **Le verdict** (Claude, 2 min). `python outils/essais.py verdict <video>` : gagnant, essais limités par la plateforme (moins de 20 vues à 24 h, hors comparaison), gagnant net ou à confirmer, republier ou non. Le gagnant au-dessus du seuil est republié en Reel normal, une seule version par vidéo sur le profil. L'essai le plus vu peut partir sur les autres réseaux dès 24 h.
6. **Le livre de recettes** (Claude, 5 min). Chaque verdict ajoute une ligne à `wiki/maps/essais.md`, section « Ce qui gagne » : la chose changée et son effet. Après plusieurs vidéos, les recettes deviennent des règles (`mesure-et-apprentissage`).

## Test
`python outils/essais.py --test` écrit « AUTO-TEST OK », et une vraie vidéo a au moins 3 essais inscrits, relevés à 24 h et 72 h, avec un verdict écrit.

## Pièges vécus
- Le même essai publié deux fois par deux processus : le registre est la seule source de vérité, et il refuse les doublons.
- Des essais presque identiques (même corps, même son, seul le début change un peu) signalés « trop proches » et restés à zéro vue : les vraies variantes changent l'idée de l'ouverture.
- Les retouches légères (miroir, vitesse, fond seul) pour multiplier les essais : la plateforme lit le contenu, et ce spam mène au blocage.
- Conclure sur trop peu de vues : attends le relevé à 72 h pour décider de republier.
- Une vidéo sans aucune sortie pendant des jours parce qu'elle attendait un accord : écris la règle de sortie à l'avance.

## Entretien dans le temps
Une tâche planifiée (bloc F) lance `a-lire` toutes les heures ou deux fois par jour. Un gagnant fort peut être relancé deux semaines plus tard avec des accroches vraiment neuves, jamais le même essai. Deux essais limités en une semaine : baisse le rythme quelques jours.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (rythme, seuil). Propose ensuite `youtube-systeme`.
