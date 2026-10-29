---
title: "Bloc E : Contenu"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc E : Machine à contenu

Ce bloc transforme les vraies questions des clients en contenu publié partout, mesuré, et qui s'améliore seul. Il vient d'un système réel qui a appris à ses dépens deux choses : la qualité écrite pour une vraie personne bat la masse optimisée, et ce qu'on ne mesure pas se répète à l'aveugle.

**Règle du bloc, sans exception** : chaque pièce de contenu (post, carrousel, script, accroche, légende, titre, article, email) passe par le board des textes (`board-textes`, bloc C) avant toute publication, tout envoi ou tout crédit d'image. Une pièce sans verdict vert reste en brouillon avec la mention « board non passé ».

**Avant d'écrire, toujours** : chaque skill du bloc lit le dossier du client idéal (`wiki/business/client-ideal.md`, `precision-emotionnelle.md` et le fichier de `pensees-client/` de la situation visée). Une accroche, une vidéo courte ou un email s'ouvre sur un niveau 3 ; un texte long en contient au moins deux.

## Avant de commencer
- Bloc A fait (vault, ingestion, recherche par le sens) : la banque d'idées se nourrit des appels et des messages.
- Bloc C fait (`board-textes`, `agent-client-ideal`, carnets experts, `controle-voix`, `controle-verite`).
- Bloc D fait au moins pour la voix, le dossier du client idéal (`dossier-client-ideal`), l'offre et la ressource gratuite.
- Outils de base : Python 3, ffmpeg (Windows : `winget install ffmpeg` ; Mac : `brew install ffmpeg` ; Linux : `sudo apt install ffmpeg`), Chrome ou Edge. Vérifie avec `ffmpeg -version` et `python --version`.

## Ordre conseillé

| # | Skill | Dépend de | Test binaire |
|---|---|---|---|
| 1 | `banque-idees` | blocs A, C, D | 20 questions réelles avec chemin de source |
| 2 | `veille-et-tendances` | 1 | 3 idées réécrites par l'angle, aucune suite de plus de 5 mots reprise |
| 3 | `accroches` | 1, 2 | 5 accroches triples par vidéo, aucune plainte résumée en phrase 1 |
| 4 | `sujet-en-pieces` | 1 | un dossier sujet avec cœur, pièce mère et 3 dérivées vertes |
| 5 | `posts-reseaux` | 4 | une semaine de posts en file, règle de cadence écrite |
| 6 | `carrousel-html` | 4 | `outils/carrousel.py --test` OK, un carrousel réel vert |
| 7 | `images-de-marque` | bloc D | bible d'une page, librairie de 20 images cataloguées |
| 8 | `carrousel-image-ia` | 6, 7 | verdict vert daté avant la première image |
| 9 | `script-video` | 1, 3 | un sous-agent neuf raconte la vidéo en 3 phrases |
| 10 | `tournage` | 9 | prise test à la bonne résolution (ffprobe), écran de lecture ouvert |
| 11 | `montage-video-code` | 10 | une prise réelle montée et validée |
| 12 | `sons-et-musique` | 11 | vidéo entre -15 et -13 LUFS, musique sous la voix |
| 13 | `youtube-systeme` | 9 à 12 | une vidéo sortie, chiffres à 2 et 7 jours au registre |
| 14 | `reels-et-shorts` | 3, 10, 11 | une prise déposée ressort en 1080x1920 |
| 15 | `decoupe-shorts` | 11, 13 | `outils/decoupe.py --test` OK, un lot réel de Shorts |
| 16 | `essais-multiples` | 14 ou 15 | `outils/essais.py --test` OK, 3 essais relevés à 24 h et 72 h |
| 17 | `distribution-api` | 5, 6, 13 | un post programmé par script, doublon refusé |
| 18 | `article-lettre-seo` | 13 (de préférence) | article vert avec source humaine citée |
| 19 | `mesure-et-apprentissage` | au moins une publication | un bilan hebdo et une règle qui cite une preuve |

Chemin court si l'utilisateur n'a que peu de temps : 1, 3, 4, 5, 6, 17, 19. La vidéo (9 à 16) s'ajoute quand il est prêt à tourner. L'article (18) vient en dernier : il dérive des vidéos.

## Outils joints (tous testés sur Windows, Python seul, sans bibliothèque à installer)
| Outil | Rôle | Test |
|---|---|---|
| `outils/planche.py` | planche contact d'images ou d'une vidéo (ffmpeg) : juger 16 images pour le prix d'une | `python outils/planche.py --test` |
| `.claude/skills/carrousel-html/outils/carrousel.py` | carrousel JSON vers PNG aux couleurs de la charte, 5 styles (podcast, uni, éditorial, Reel, vidéo longue découpée), conversation et pub statique, contrôles de débordement, de zone sûre et de contraste ; `rendre`, `exemple`, `images`, `reel`, `split` | `--test` |
| `.claude/skills/carrousel-html/outils/file.py` | page de revue de la semaine, file du jour, rotation des styles, limites par réseau ; `revue`, `ajouter`, `retirer`, `etat`, `du-jour` | `--test` |
| `.claude/skills/carrousel-html/outils/tiktok-photo.py` | option : publication en mode photo TikTok par le navigateur ; `--setup`, `--dry-run`, `--contenu-ia` | `--test` |
| `.claude/skills/carrousel-image-ia/outils/carrousel-ia.py` | règles du carrousel en images IA, prompts tirés de la charte, banque d'images, finition ; `exemple`, `verifier`, `prompts`, `finir`, `banque` | `--test` |
| `.claude/skills/essais-multiples/outils/essais.py` | registre des essais, lectures à 24 h et 72 h, verdict, seuil de republication | `--test` |
| `.claude/skills/decoupe-shorts/outils/decoupe.py` | moments d'une vidéo longue vers Shorts 1080x1920 (ffmpeg), mode buste, liaison refusée | `--test` |
| `.claude/skills/montage-video-code/outils/commun.py` | base commune : ffmpeg, encodeur (carte graphique ou processeur), verrou de rendu, lecture de la charte | `--test` |
| `.claude/skills/montage-video-code/outils/transcrire.py` | prise vers mots horodatés ; `prise.mp4 t.json` | `--test` |
| `.claude/skills/montage-video-code/outils/couper.py` | coupe silences, « euh », reprises et bruits de bouche ; `prise.mp4 t.json --apercu`, `--depuis` | `--test` |
| `.claude/skills/montage-video-code/outils/habiller.py` | sous-titres, cartes, chapitres, zooms et logo aux couleurs de la charte ; `verifier`, `rendre`, `chapitres` | `--test` |
| `.claude/skills/montage-video-code/outils/rythme.py` | contrôle du rythme ; `video --profil reel` ou `long` | `--test` |
| `.claude/skills/montage-video-code/outils/revue.py` | page de revue : notes par minutage, une vidéo à la fois ; `dossier [--reseau]` | `--test` |
| `.claude/skills/montage-video-code/outils/broll.py` | images d'illustration (Pexels) avec registre des licences ; `"requête"` | `--test` |
| `.claude/skills/sons-et-musique/outils/sonotheque.py` | sonothèque et licences ; `ajouter`, `choisir`, `verifier` | `--test` |
| `.claude/skills/sons-et-musique/outils/mixage.py` | couche son, musique sous la voix, niveau ; `video -o s --musique auto`, `mesurer` | `--test` |
| `.claude/skills/tournage/outils/verif.py` | garde du tournage (définition, images par seconde, caméra) ; `prise --attendu 3840x2160`, `cameras` | `--test` |
| `.claude/skills/reels-et-shorts/outils/gabarit.py` | Reel aux gabarits rythme, éditorial ou simple ; `coupe t.json --gabarit rythme` | `--test` |
| `.claude/skills/tournage/outils/ecran.py` | script vers écran de lecture plein écran | `--test` |

Installe chaque outil en le copiant dans `outils/` du vault de l'utilisateur, puis lance son `--test` : il doit écrire « AUTO-TEST OK ».

## Fichiers créés dans le vault de l'utilisateur
- `wiki/maps/machine-contenu.md` : le hub du bloc (cadence, réseaux, chaîne, liens vers chaque brique).
- `wiki/maps/banque-idees.md`, `veille.md`, `banque-accroches.md`, `posts-gabarits.md`, `carrousels.md`, `style-maison.md`, `reels.md`, `essais.md`, `youtube.md`, `tournage.md`, `montage.md`, `sons.md`, `shorts.md`, `distribution.md`, `mesure.md`.
- `outputs/` : `sujets/`, `courts/`, `youtube/`, `carrousels/`, `shorts/`, `essais/`, `articles/`, `veille/`, `mesure/`, `file-publication/`.

## Les leçons du système d'origine à garder en tête
1. Des dizaines d'articles générés en masse n'ont presque rien rapporté. Une lettre écrite pour une vraie personne, depuis une source humaine, bat l'article optimisé.
2. La phrase 1 d'une vidéo courte est une scène. La plainte résumée fait fuir avant 3 secondes.
3. Ce qui marche ailleurs se réécrit par l'angle. Les mots copiés finissent classés non originaux.
4. Un style se valide sur une vidéo avant d'en monter un lot. Une note de l'utilisateur devient une règle écrite, de préférence dans le code.
5. Un plancher tenu bat un pic abandonné : la cadence se pose sur une mauvaise semaine.

## Fin du bloc
Le bloc est fait quand les 19 tests passent (ou ceux du chemin court) et que `wiki/maps/parcours.md` les coche. Propose ensuite le bloc F (automatisation et pilotage) : les tâches planifiées qui font tourner veille, essais, publication et bilan sans l'utilisateur.


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
