---
name: reels-et-shorts
description: "Met en place la chaîne des vidéos courtes face caméra (Reels, Shorts, TikTok) : script court, fiche de tournage du jour, dépôt des prises, montage, puis essais. Utiliser quand l'utilisateur dit « je veux faire des Reels », « écris mes scripts courts », « j'ai filmé, monte-les ». Pas pour découper une vidéo longue (utiliser decoupe-shorts)."
---
# Reels et Shorts

## Pourquoi
Le système d'origine a construit une petite usine : les idées arrivent (banque, veille), chaque idée devient un script court avec plusieurs ouvertures, une fiche du jour liste ce qui reste à filmer, l'entrepreneur filme d'un bloc et dépose ses prises, Claude monte. Les leçons de mesure ont fixé deux règles : la phrase 1 est une scène, et une durée de 15 à 45 secondes tient mieux qu'un long monologue pour ce format. Le tournage a aussi compté : une caméra mal réglée a donné des prises trop petites pour être recadrées en vertical.

## Prérequis
- `banque-idees`, `veille-et-tendances`, `accroches`.
- Bloc C (`board-textes`, `agent-client-ideal`).
- ffmpeg installé. Une caméra ou un téléphone qui filme au moins en 1080p, idéalement en 4K.
- `montage-video-code` pour le montage, `essais-multiples` pour la mise en ligne.

## Interview
Lis d'abord : la banque, la banque d'accroches, `wiki/maps/machine-contenu.md`, `wiki/maps/moi.md` (temps disponible). Puis demande :
1. « Avec quoi filmes-tu : téléphone, webcam, appareil photo ? Et en quelle résolution ? » Range dans `wiki/maps/tournage.md` (créé par `tournage`), section « Matériel ».
2. « Combien de vidéos courtes peux-tu filmer d'un bloc, et quel jour ? » Range dans `machine-contenu.md`, section « Cadence ».
3. « Où vas-tu déposer tes prises ? » (un dossier synchronisé, par exemple `_depot/courts/`). Range dans `machine-contenu.md`.
4. « Lis-tu un texte ou parles-tu librement ? » Le format de la fiche en dépend.

## Construire
1. **Le gabarit de script court** (Claude, 10 min). Dans `wiki/maps/reels.md` : une durée cible (15 à 45 s), 5 ouvertures (de `accroches`), une scène, un principe, une action, un mot-clé ou une ressource à la fin. 60 à 170 mots au total. Un seul principe par vidéo.
2. **Les scripts** (Claude, 20 min pour un lot). Pour chaque idée choisie : `outputs/courts/scripts/<n>-<slug>.md` avec en tête la table des ouvertures (essai, texte à l'écran, premiers mots). Passe le lot à `board-textes` puis à `agent-client-ideal`. Seuls les verts entrent dans la fiche.
3. **La fiche du jour** (Claude, 10 min). `outputs/courts/fiche-du-jour.md` liste les scripts verts pas encore filmés, les plus prometteurs d'abord, et une version écran (texte en grand) générée comme dans `tournage`.
4. **Le dépôt** (l'utilisateur). Il filme, dépose dans le dossier convenu, dit « j'ai déposé ». Une prise par ouverture si les essais sont prévus.
5. **Le contrôle des prises** (Claude, 5 min). `ffprobe -v error -show_entries stream=width,height,r_frame_rate -of csv=p=0 prise.mp4` sur chaque fichier. Sous 1080 de large en vertical, préviens et propose de régler la caméra. Puis `python outils/planche.py prise.mp4 --n 12 -o planche.jpg` pour voir le cadrage.
6. **Montage puis essais** (Claude). `montage-video-code`, puis `essais-multiples`.

## Test
Un lot de scripts verts existe, la fiche du jour liste ceux à filmer, et une prise déposée ressort montée en 1080x1920 avec ses ouvertures prêtes pour les essais.

## Pièges vécus
- Une caméra derrière un mauvais câble ou un mauvais réglage a enregistré en petite résolution : impossible de recadrer net. Vérifie une prise de 10 s avec ffprobe avant chaque séance.
- Un cadrage trop serré gênait les styles de montage avec texte et images autour : filme plus large (tête, épaules, de l'air au-dessus).
- Un lot entier monté dans un style pas encore validé : les mêmes erreurs partout. Valide le style sur une vidéo, note les remarques, puis monte le lot.
- Des scripts traduits presque mot à mot depuis des vidéos étrangères : moins bons devant le client idéal que les versions libres.

## Entretien dans le temps
Chaque remarque de l'utilisateur sur un montage devient une règle écrite (dans le skill de montage ou dans le code). `mesure-et-apprentissage` dit quels sujets et quelles durées gagnent ; la fiche du jour se trie avec.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (matériel, jour de tournage). Propose ensuite `essais-multiples`.
