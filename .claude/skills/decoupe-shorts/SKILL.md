---
name: decoupe-shorts
description: "Découpe une vidéo longue en plusieurs Shorts verticaux 1080x1920 : choix des moments dans la transcription, calage sur les phrases, refus des moments qui ne se comprennent pas seuls, cadrage tête et buste sur fond flouté, titre et sous-titres aux couleurs de la charte, revue en lot, un Short par jour. Fournit un outil testé. Utiliser quand l'utilisateur dit « fais des Shorts de ma vidéo », « découpe ma vidéo longue », « recycle ma vidéo », « shorts <vidéo> OK ». Pas pour des vidéos courtes filmées exprès (utiliser reels-et-shorts)."
---
# Découpe en Shorts

## Pourquoi
Chaque vidéo longue du système d'origine contient plusieurs passages qui tiennent seuls. Une chaîne automatique en tire environ sept Shorts, un par jour dès le lendemain de la sortie, publiés partout. Les premiers essais ont appris le cadrage : un recadrage vertical plein cadre zoomait trop et devenait flou, la vidéo entière au milieu laissait trop de vide ; la tête et le buste en 3:4, calés en bas sur la même image floutée, avec le titre dans le flou du haut, ont gagné. L'entrepreneur a validé chaque lot au début, et chaque remarque est devenue une règle dans le code, jusqu'au jour où le lot est parti seul.

## Prérequis
- `youtube-systeme` et `montage-video-code` (une vidéo longue montée, `commun.py` et `transcrire.py` copiés dans `outils/` du vault). `charte-graphique` conseillé (titre et sous-titres).
- ffmpeg 7.1 ou plus récent. La transcription horodatée de la vidéo longue (`transcrire.py`).
- Bloc C (`board-textes` pour titres et légendes, `agent-client-ideal` pour l'accroche). `distribution-api` et `essais-multiples` pour la suite.
- Outil joint : `outils/decoupe.py` (testé : `python outils/decoupe.py --test`).

## Interview
Lis d'abord : `wiki/maps/youtube.md`, `wiki/maps/machine-contenu.md` (réseaux), `wiki/maps/montage.md`, `wiki/maps/tournage.md` (résolution filmée). Puis demande, une question à la fois :
1. « Combien de Shorts par vidéo, et combien par jour ? » Range dans `wiki/maps/shorts.md`, section « Rythme ». Le système d'origine : environ sept par vidéo, un par jour, à partir du lendemain de la sortie.
2. « Tu veux valider chaque lot avant publication ? » Conseille oui au début, puis plus du tout une fois que tout est juste. Range dans « Validation ».
3. « Tu te filmes en miroir (image retournée) ? » Les Shorts suivent le même réglage. Range dans « Cadrage ».
4. « Quel mot les gens peuvent commenter pour recevoir ta ressource ? » (s'il en existe une, voir `tunnel-et-quiz`). Range dans « Légende ».

## Construire
1. **Installer l'outil (Claude, 5 min).** Copie `outils/decoupe.py` dans `outils/` du vault et lance `python outils/decoupe.py --test` (« AUTO-TEST OK »).
2. **Choisir les moments (Claude, 20 min).** Dans la transcription horodatée, choisis quelques moments de plus que le lot voulu, de 20 à 90 s : compris seul, accroche dans les 3 premières secondes (`accroches`), idée complète, sur le sujet, aucun appel à l'action au milieu. À valeur égale, préfère le passage où l'utilisateur tranche (un verdict, un contre-pied, un ordre court) et celui où la tension repart au moins une fois (un « mais » qui ouvre une question neuve) ; un passage qui ne fait que décrire reste en réserve. Écris `outputs/shorts/<slug>/moments.json` : `[{"debut": 81.5, "fin": 124.0, "titre": "..."}]`. Les titres passent `board-textes`.
3. **Cadrer (Claude, 3 min).** `python outils/planche.py video.mp4 --n 4` : repère où est le visage dans l'image (0 = bord gauche, 1 = bord droit) pour `--centre`.
4. **Rendre un aperçu (Claude, quelques minutes).** `python outils/decoupe.py video.mp4 outputs/shorts/<slug>/moments.json --mots transcription.json --centre 0.5 -o outputs/shorts/<slug>/ --apercu` (ajoute `--miroir` si noté). Avec `--mots`, chaque moment démarre sur un début de mot et finit sur une fin de phrase ; un moment qui commence par un mot de liaison (« donc », « ensuite ») est refusé avec la raison : remplace-le par un moment de réserve. Mode `flou` (vidéo entière au milieu) ou `centre` (plein cadre, seulement depuis une source 4K) si l'utilisateur le préfère.
5. **Contrôler (Claude, 5 min).** `python outils/planche.py outputs/shorts/<slug>/short-01.mp4 --n 8` par Short : phrase coupée, titre sur le visage, sous-titre caché par l'interface (zone du bas), répétition. L'accroche passe `agent-client-ideal`. Un Short avec un défaut sort du lot et un moment de réserve le remplace.
6. **La revue en lot (l'utilisateur, 10 min).** `python outils/revue.py outputs/shorts/<slug>` (app de `montage-video-code`), touche S pour voir ce que cache l'interface des réseaux. Ses notes deviennent des règles dans `wiki/maps/shorts.md` ou dans l'outil. Quand il dit « shorts <slug> OK », Claude relance sans `--apercu` : le rendu final à pleine résolution.
7. **Publier (Claude).** Un Short par jour via `distribution-api` ; sur Instagram, par `essais-multiples`. Le lien de la vidéo complète va dans la légende (ou en première réponse sur les réseaux qui pénalisent les liens). Aucun appel à l'action dans la vidéo elle-même.

## Test
`python outils/decoupe.py --test` écrit « AUTO-TEST OK », et une vraie vidéo longue donne un dossier de Shorts en 1080x1920 avec `shorts.json`, chacun commençant sur un début de phrase, avec titre et légende validés par le board.

## Pièges vécus
- **Un recadrage vertical d'une source en 1080p.** Environ 600 px de large agrandis : flou. Le plan tête et buste sur fond flouté tient avec une source 1080p ; le plein cadre attend une source 4K.
- **La vidéo entière posée au milieu.** Une bande vide restait sous l'image. Le buste calé en bas, avec le titre dans le flou du haut, a réglé ça.
- **Une phrase coupée net à la fin d'un moment.** Prends la fin de phrase dans la transcription, jamais un horodatage arrondi : `--mots` le fait.
- **Un Short qui commence par « Donc si on revient à l'histoire ».** Incompréhensible sans le reste. Un moment qui démarre sur un mot de liaison est refusé.
- **Un titre d'accroche qui trahissait le propos.** Accrocheur, mais faux par rapport à ce qui était dit. Le titre se choisit pour sa fidélité au passage, puis passe le board.
- **Un passage hors sujet.** Le plus grand risque d'un lot automatique. Le contrôle de l'étape 5 vérifie que chaque Short parle du sujet de la chaîne.
- **Le lien natif « vidéo associée ».** Il ne se règle que dans YouTube Studio, sans API : ajoute-le à la feuille du jour J.
- **Un réseau qui refuse une vidéo hébergée sur un domaine non vérifié, un autre qui refuse les fichiers trop lourds.** Passe par la médiathèque de l'outil de publication, et prévois une copie allégée.

## Entretien dans le temps
Chaque remarque sur un Short devient une règle dans `wiki/maps/shorts.md` ou dans l'outil, avec son test. Quand l'utilisateur dit que le lot est parfait plusieurs fois de suite, passe la validation en mode automatique (`shorts.md`, section « Validation ») : le lot part seul, sans notification sauf panne. `mesure-et-apprentissage` dit quels types de moments gagnent.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (rythme, validation, miroir). Propose ensuite `distribution-api`.
