---
name: montage-video-code
description: "Monte les vidéos par du code (ffmpeg pour couper et assembler, HyperFrames ou Remotion pour l'habillage) : coupes des silences et hésitations, textes à l'écran, zooms, sous-titres, rendu. Utiliser quand l'utilisateur dit « monte ma vidéo », « habille ma facecam », « coupe les silences ». Pas pour découper une vidéo longue en Shorts (utiliser decoupe-shorts)."
---
# Montage vidéo par le code

## Pourquoi
Un monteur coûte cher et un logiciel de montage demande des heures. Le système d'origine monte par le code : une composition HTML décrit les textes, les zooms et les cartes, un moteur la rend en vidéo, ffmpeg fait les coupes et l'encodage. L'entrepreneur regarde, donne ses notes, et chaque note devient une règle. Deux leçons ont fixé la méthode : valider un style sur une seule vidéo avant d'en monter un lot, et ne jamais lancer plusieurs rendus lourds à la fois (le PC a gelé avec trois rendus en parallèle).

## Prérequis
- `tournage` (prises vérifiées), `script-video` ou `reels-et-shorts`.
- ffmpeg, Node.js 22 ou plus. HyperFrames (open source, `npx hyperframes`) ou Remotion en secours. Les skills HyperFrames s'installent dans Claude Code par `npx skills add heygen-com/hyperframes`.
- Option : un logiciel qui coupe les silences et hésitations par API (Tella, Descript), ou la transcription locale faster-whisper pour couper soi-même.
- Outil partagé : `outils/planche.py` pour juger sans ouvrir chaque image.

## Interview
Lis d'abord : `wiki/maps/tournage.md`, la charte de marque (`images-de-marque`), `wiki/maps/montage.md` s'il existe. Puis demande :
1. « Montre-moi 1 à 3 vidéos dont tu aimes le montage. » Range dans `wiki/maps/montage.md`, section « Références ». On copie le mouvement et le rythme (coupes, zooms, entrée des textes, place des sous-titres), jamais les mots ni les images.
2. « Tes couleurs et polices ? » Range dans « Charte » (ou reprends `images-de-marque`).
3. « Tu veux revoir chaque vidéo avant publication, ou seulement les premières ? » Range dans « Validation ».

## Construire
1. **Installer et tester le moteur** (Claude, 20 min). `npx hyperframes init test-montage` puis le rendu de l'exemple. Écris dans `wiki/maps/montage.md` les commandes qui marchent sur sa machine (Windows et Mac diffèrent parfois sur les chemins et les guillemets ; passe les options JSON par fichier, jamais en ligne).
2. **Mesurer une référence** (Claude, 15 min). Sur une vidéo de référence de l'utilisateur : `ffmpeg -i ref.mp4 -vf "select='gt(scene,0.3)',showinfo" -f null - 2>&1 | grep pts_time` donne les instants de coupe ; `python outils/planche.py ref.mp4 --n 16` montre les cadrages. Écris le brief « case par case » : durée moyenne d'un plan, taille du visage, entrée des textes, niveau sonore, et ce qu'on en garde.
3. **Couper** (Claude, 15 min). Transcris la prise (faster-whisper en local, gratuit). Retire silences, hésitations et reprises (garde la dernière reprise d'une phrase). Avec un outil par API, travaille sur une copie pour garder l'original intact. Exporte dans la résolution filmée.
4. **Habiller** (Claude, 20 min). Composition HyperFrames : la vidéo coupée en clip, des textes à l'écran seulement quand la phrase dite les justifie, un léger zoom aux coupes, sous-titres, visage centré et textes centrés au milieu du cadre. Chaque élément timé a ses attributs de début, de durée et de piste ; rien d'aléatoire dans les animations.
5. **Rendre** (Claude). Un rendu lourd à la fois, en priorité basse, ffmpeg limité à 4 fils (`-threads 4`). Après le rendu, une planche de 16 images et l'écoute (`sons-et-musique`). Un rapport court par vidéo, pour pouvoir reprendre si tout s'arrête.
6. **La revue** (l'utilisateur, 10 min). Il regarde et donne ses notes. Claude écrit chaque note en règle dans `wiki/maps/montage.md` avant la vidéo suivante, puis corrige.

## Test
Une prise réelle ressort montée, sans silence ni hésitation audible, à la résolution prévue, et l'utilisateur la valide ou ses notes sont devenues des règles écrites.

## Pièges vécus
- Plusieurs rendus et détourages en parallèle : le PC a gelé. Un seul monteur de rendu à la fois.
- Deux conversations Claude sur le même lot de montage la même nuit : elles se sont écrasées. Un verrou de rendu (un fichier `rendu.lock`) et une seule conversation par lot.
- Un lot entier monté dans un style pas encore validé : les mêmes erreurs partout. Une vidéo, ses notes, puis la suite. Une fois le style figé, le lot peut se monter en l'absence de l'utilisateur.
- Des animations posées partout pour faire « monté » : une animation n'apparaît que si la phrase dite la justifie.
- Une version du moteur qui change sous les pieds : épingle la version qui marche.

## Entretien dans le temps
Les règles validées restent dans `wiki/maps/montage.md` avec la date de validation. Garde les anciennes versions et leurs notes dans un sous-dossier `_anciennes/`. Le cache des rendus n'a pas de ménage automatique : prévois un nettoyage mensuel (bloc F).

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (style validé). Propose ensuite `decoupe-shorts`.
