---
name: sons-et-musique
description: "Monte une sonothèque avec licences (bruitages, musiques libres), règle le son des montages (volume, musique sous la voix, effets) et fait vérifier le résultat. Utiliser quand l'utilisateur dit « ajoute de la musique », « des bruitages », « le son de ma vidéo est bizarre ». Pas pour le montage image (utiliser montage-video-code)."
---
# Sons et musique

## Pourquoi
Claude n'entend pas. Dans le système d'origine, les premiers montages avaient des effets sonores mal placés, des « pops » trop rapprochés, une musique qui couvrait la voix, et des titres dont la licence était douteuse. La brique a réglé trois choses : une sonothèque où chaque son a sa licence notée, des règles simples de placement validées par l'entrepreneur, et un contrôle par mesure (volume, pics) plus un outil d'écoute qui décrit le son. La musique sous licence commerciale sert seulement là où la plateforme la couvre.

## Prérequis
- `montage-video-code`. ffmpeg.
- Sources de sons libres, au choix : Openverse (sans clé, filtre CC0 et CC BY), Freesound, packs CC0. Musique sous licence : la bibliothèque de la plateforme (sons Instagram, bibliothèque audio YouTube) ou un service payant comme Epidemic Sound.
- Option : un outil d'écoute par IA (par exemple earshot, open source) pour décrire et comparer des sons.

## Interview
Lis d'abord : `wiki/maps/montage.md`, `wiki/maps/moi.md` (abonnements). Puis demande :
1. « Tu veux de la musique sous ta voix, ou la voix seule ? » Range dans `wiki/maps/sons.md`, section « Goût ».
2. « Des bruitages (transitions, clics), oui ou non ? » Range dans « Goût ».
3. « As-tu un abonnement musique ? Sinon, on reste sur du libre. » Range dans « Sources ».
4. « Sur Instagram et TikTok, tu choisis toi-même le son tendance ? » Ces plateformes ont leurs propres sons : souvent c'est lui qui décide à la publication.

## Construire
1. **La sonothèque** (Claude, 20 min). `bibliotheque/sons/` avec un `catalogue-son.json` : fichier, type (bruitage, musique), humeur, durée, source, licence, attribution exigée, plateformes permises. Remplis avec des sons CC0 ou CC BY (Openverse : `https://api.openverse.org/v1/audio/?q=piano&license=cc0,by`). Une musique sous licence commerciale porte « Instagram et TikTok seulement » si sa licence ne couvre pas YouTube.
2. **Les règles de placement** (Claude, 10 min). Dans `wiki/maps/sons.md` : musique sous la voix baissée nettement (autour de 20 dB sous la voix), bruitage seulement sur un événement visible, un écart minimum entre deux effets du même type (l'origine a fixé environ 1,5 s entre deux « pops »), pas de son sur chaque coupe. Volume final autour de -14 LUFS pour les réseaux : `ffmpeg -i in.mp4 -af loudnorm=I=-14:TP=-1.5:LRA=11 -c:v copy out.mp4`.
3. **La musique sous la voix** (Claude, 10 min). Mixage ffmpeg qui baisse la musique quand la voix parle : `ffmpeg -i voix.mp4 -i musique.mp3 -filter_complex "[1:a]volume=0.25[m];[m][0:a]sidechaincompress=threshold=0.05:ratio=8[mc];[0:a][mc]amix=inputs=2:duration=first[a]" -map 0:v -map "[a]" -c:v copy sortie.mp4`.
4. **Le contrôle** (Claude, 5 min par vidéo). Mesure : `ffmpeg -i sortie.mp4 -af ebur128 -f null -` (volume intégré, pics). Écoute : avec un outil d'écoute, décris le mixage et repère les effets trop rapprochés. Sinon, l'utilisateur écoute 30 secondes au casque.
5. **La revue** (l'utilisateur). Chaque remarque devient une règle de `wiki/maps/sons.md`.

## Test
La sonothèque contient au moins 20 sons avec licence notée, et une vidéo montée mesure entre -15 et -13 LUFS avec une musique qui ne couvre jamais la voix.

## Pièges vécus
- Un son « pop » doux d'un logiciel de montage, détesté par l'entrepreneur, revenait partout : un goût précis devient une règle écrite, jamais un rappel oral.
- Des effets sur chaque coupe : épuisant à l'oreille. Un effet suit un événement visible.
- Une musique commerciale utilisée sur YouTube sans droits : risque de réclamation. La colonne « plateformes permises » tranche.
- Juger le son sur la seule forme d'onde : il faut mesurer le volume et écouter (ou faire écouter par un outil).

## Entretien dans le temps
Ajoute les sons bien notés à la sonothèque, retire ceux que l'utilisateur rejette. Relis les licences une fois par an, les conditions des services changent.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (goût sonore). Propose ensuite `mesure-et-apprentissage`.
