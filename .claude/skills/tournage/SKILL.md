---
name: tournage
description: "Prépare et sécurise la séance de tournage : matériel vérifié, résolution contrôlée, écran de lecture du script en grand, checklist du jour, dépôt des prises. Fournit un générateur d'écran testé. Utiliser quand l'utilisateur dit « je tourne demain », « prépare mon tournage », « fais-moi un prompteur ». Pas pour écrire le script (utiliser script-video)."
---
# Tournage

## Pourquoi
Dans le système d'origine, des séances entières ont été perdues pour des détails : une caméra branchée derrière un mauvais câble qui enregistrait en petite résolution, un logiciel d'enregistrement réglé en 720p malgré l'option haute qualité, un cadrage trop serré pour les montages verticaux, un écran capturé par erreur avec le script dessus. L'entrepreneur voulait aussi lire son script en grand, en direct, sans notes à côté. La brique règle tout ça avant que la caméra tourne.

## Prérequis
- `script-video` ou `reels-et-shorts` (un texte validé par le board).
- Une caméra ou un téléphone, un micro si possible, un logiciel d'enregistrement (OBS Studio gratuit, Tella, l'appareil photo du téléphone).
- ffmpeg installé (pour `ffprobe`). Outil joint : `outils/ecran.py` (testé : `python outils/ecran.py --test`).

## Interview
Lis d'abord : `wiki/maps/tournage.md` s'il existe, `wiki/maps/moi.md`. Puis demande :
1. « Avec quoi filmes-tu, et avec quel logiciel ? » Range dans `wiki/maps/tournage.md`, section « Matériel ».
2. « Où places-tu ton écran de lecture par rapport à la caméra ? » Conseille juste sous l'objectif. Range dans « Plateau ».
3. « Tu portes une tenue fixe pour tes vidéos ? » Une tenue constante aide à être reconnu. Range dans « Plateau ».
4. « Combien de temps as-tu pour une séance ? » Range dans « Séance ».

## Construire
1. **Le réglage du matériel** (l'utilisateur guidé par Claude, 20 min, une seule fois). Dans OBS Studio : Paramètres, Vidéo, résolution de base et de sortie à la taille de la caméra (3840x2160 si elle filme en 4K, sinon 1920x1080), 30 images par seconde ; Paramètres, Sortie, mode avancé, format MP4 ou MKV, encodeur matériel si présent. Branche la caméra directement sur un port USB 3 de l'ordinateur, sans concentrateur. Filme large : tête, épaules et de l'air au-dessus de la tête.
2. **La prise test** (l'utilisateur, 1 min, avant chaque séance). Il filme 10 secondes. Claude lance `ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 test.mp4`. La largeur et la hauteur doivent correspondre au réglage. Puis `python outils/planche.py test.mp4 --n 4 -o planche.jpg` pour vérifier le cadrage et la lumière.
3. **L'écran de lecture** (Claude, 2 min). `python outils/ecran.py outputs/youtube/<slug>/script.md`. Les lignes entre crochets sont des notes en bleu (repères de slide, gestes). Dans le navigateur : F11, puis Espace pour avancer. Choisis texte complet ou fiche selon sa préférence notée dans « Format d'écran ».
4. **La checklist du jour** (Claude, 10 min). `outputs/tournage/AAAA-MM-JJ.md` : prise test faite, batterie et carte, micro testé, lumière, tenue, photo de miniature prévue (pose, regard, objet), ordre des vidéos, une prise par ouverture si des essais sont prévus. Seulement la caméra est enregistrée, jamais l'écran.
5. **Le dépôt** (l'utilisateur, 2 min). Il nomme chaque prise avec son numéro et un mot (« 1 prix ») et la dépose dans le dossier convenu, puis dit « j'ai tourné ». Claude vérifie chaque fichier avec ffprobe avant le montage.

## Test
La prise test sort à la résolution réglée (ffprobe le prouve), l'écran de lecture s'ouvre avec le script validé, et la checklist du jour est cochée.

## Pièges vécus
- Une caméra 4K branchée derrière un concentrateur USB 2 : enregistrée en petite résolution sans prévenir. Port direct, et ffprobe à chaque séance.
- Un logiciel qui a capturé l'écran avec le script à côté de la caméra : au montage, tout a dû passer en caméra seule, image par image. Désactive la capture d'écran.
- Une source en 1080p recadrée en vertical ne fait qu'environ 600 px de large : floue. Filme en 4K si les Shorts viennent de la vidéo longue.
- Des accroches jouées avec décor et mise en scène, jugées irréalistes et jamais tournées : écris des accroches qu'il peut dire face caméra.

## Entretien dans le temps
Chaque problème de séance devient une ligne de la checklist. La prise test reste obligatoire même quand tout marchait la veille : un câble déplacé suffit.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (matériel, réglages, tenue). Propose ensuite `montage-video-code`.
