---
name: decoupe-shorts
description: "Découpe une vidéo longue en plusieurs Shorts verticaux : choix des moments dans la transcription, contrôle, rendu 1080x1920 par ffmpeg, un Short par jour. Fournit un outil testé. Utiliser quand l'utilisateur dit « fais des Shorts de ma vidéo », « découpe ma vidéo longue », « recycle ma vidéo ». Pas pour des vidéos courtes filmées exprès (utiliser reels-et-shorts)."
---
# Découpe en Shorts

## Pourquoi
Chaque vidéo longue du système d'origine contient plusieurs passages qui tiennent seuls. Une chaîne automatique en tire environ sept Shorts, un par jour dès le lendemain de la sortie, publiés partout. Les premiers essais ont appris le cadrage : un recadrage vertical plein cadre zoomait trop et devenait flou sur une source en 1080p ; la vidéo entière posée sur la même image floutée a mieux tenu. L'entrepreneur a validé chaque lot au début, et chaque remarque est devenue une règle dans le code.

## Prérequis
- `youtube-systeme` et `montage-video-code` (une vidéo longue montée), ffmpeg.
- Une transcription horodatée (faster-whisper en local, ou le fichier de sous-titres envoyé à YouTube).
- Bloc C (`board-textes` pour titres et légendes). `distribution-api` et `essais-multiples` pour la suite.
- Outil joint : `outils/decoupe.py` (testé : `python outils/decoupe.py --test`).

## Interview
Lis d'abord : `wiki/maps/youtube.md`, `wiki/maps/machine-contenu.md` (réseaux), `wiki/maps/montage.md`. Puis demande :
1. « Combien de Shorts par vidéo, et combien par jour ? » Range dans `wiki/maps/shorts.md`, section « Rythme ».
2. « Tu veux valider chaque lot avant publication ? » Conseille oui au début, puis plus du tout une fois que tout est juste. Range dans « Validation ».
3. « Ta vidéo est filmée en 4K ou en 1080p ? » Le mode de cadrage en dépend.

## Construire
1. **Installer l'outil** (Claude, 5 min). Copie `outils/decoupe.py` dans `outils/` du vault, lance `python outils/decoupe.py --test` (« AUTO-TEST OK »).
2. **Choisir les moments** (Claude, 15 min). Dans la transcription horodatée, choisis quelques moments de plus que le lot voulu, de 20 à 90 s : compris seul, accroche dans les 3 premières secondes (`accroches`), idée complète, sur le sujet, aucun appel à l'action au milieu. Écris `outputs/shorts/<slug>/moments.json` : `[{"debut": 81.5, "fin": 124.0, "titre": "..."}]`. Garde les meilleurs.
3. **Rendre** (Claude, quelques minutes par Short). `python outils/decoupe.py video.mp4 outputs/shorts/<slug>/moments.json -o outputs/shorts/<slug>/ --mode flou`. Mode `centre` seulement si la source est en 4K. L'outil refuse un moment trop court, trop long ou qui chevauche, et normalise le son.
4. **Habiller** (Claude, option). Titre dans la zone haute, sous-titres : passe chaque Short par la composition de `montage-video-code`, ou garde-les bruts au début.
5. **Contrôler** (Claude, 5 min). `python outils/planche.py outputs/shorts/<slug>/short-01.mp4 --n 8` par Short : phrase coupée, titre sur le visage, répétition. Titres et légendes passent `board-textes` (bloc C) et l'accroche passe `agent-client-ideal`.
6. **Publier** (Claude). Un Short par jour via `distribution-api` ; sur Instagram, par `essais-multiples`. Le lien de la vidéo complète va dans la légende (ou en première réponse sur les réseaux qui pénalisent les liens).

## Test
`python outils/decoupe.py --test` écrit « AUTO-TEST OK », et une vraie vidéo longue donne un dossier de Shorts en 1080x1920 avec `shorts.json`, chacun avec titre et légende validés.

## Pièges vécus
- Recadrage vertical d'une source en 1080p : environ 600 px de large, flou. Mode flou par défaut, mode centre seulement en 4K.
- Une phrase coupée net à la fin d'un moment : prends la fin de phrase dans la transcription, jamais un horodatage arrondi.
- Le lien natif « vidéo associée » d'un Short ne se règle que dans YouTube Studio : ajoute-le à la feuille du jour J.
- Certains réseaux refusent une vidéo hébergée sur un domaine non vérifié : passe par la médiathèque de l'outil de publication.

## Entretien dans le temps
Chaque remarque sur un Short devient une règle dans `wiki/maps/shorts.md` ou dans l'outil. Quand l'utilisateur dit que le lot est parfait plusieurs fois de suite, passe la validation en mode automatique. `mesure-et-apprentissage` dit quels types de moments gagnent.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (rythme, validation). Propose ensuite `distribution-api`.
