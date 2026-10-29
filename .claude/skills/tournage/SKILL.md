---
name: tournage
description: "Prépare et sécurise la séance de tournage : réglage unique du logiciel d'enregistrement, garde technique (la caméra propose-t-elle vraiment la résolution voulue, la prise test sort-elle à la bonne taille, avec le son au bon niveau), écran de lecture du script aux couleurs de la charte, checklist du jour, dépôt des prises. Fournit deux outils testés. Utiliser quand l'utilisateur dit « je tourne demain », « prépare mon tournage », « fais-moi un prompteur », « ma caméra filme flou ». Pas pour écrire le script (utiliser script-video), ni pour monter (utiliser montage-video-code)."
---
# Tournage

## Pourquoi
Dans le système d'origine, des séances entières ont été perdues pour des détails : une caméra branchée derrière un concentrateur USB 2 qui enregistrait en petite résolution sans prévenir (des semaines de vidéos « 4K » étaient en fait agrandies), un logiciel d'enregistrement en ligne qui saccadait, un cadrage trop serré pour les montages verticaux, un écran capturé par erreur avec le script dessus. La brique règle tout ça avant que la caméra tourne, avec une garde qui mesure au lieu de croire.

## Prérequis
- `script-video` ou `reels-et-shorts` (un texte validé par le board). `charte-graphique` conseillé (l'écran de lecture prend ses couleurs sombres).
- Une caméra ou un téléphone, un micro si possible, un logiciel d'enregistrement : OBS Studio (gratuit, conseillé sur ordinateur) ou l'appareil photo du téléphone.
- Python 3.10 ou plus récent, ffmpeg 7.1 ou plus récent. `commun.py` de `montage-video-code` copié dans `outils/` du vault.
- Outils joints dans `outils/`, chacun avec `--test` : `verif.py` (garde du tournage : caméras et prise test) et `ecran.py` (script vers écran de lecture plein écran).

## Interview
Lis d'abord : `wiki/maps/tournage.md` s'il existe, `wiki/maps/moi.md`. Puis demande, une question à la fois :
1. « Avec quoi filmes-tu, et avec quel logiciel ? » Range dans `wiki/maps/tournage.md`, section « Matériel ». Si c'est un appareil photo branché par un adaptateur HDMI vers USB, note le nom de l'adaptateur.
2. « Tes vidéos longues donneront-elles aussi des Shorts verticaux ? » Si oui, la 4K compte : une découpe verticale d'une image 1080p ne fait qu'environ 600 px de large. Range dans « Résolution visée ».
3. « Tu lis ton texte en entier, ou tu parles depuis un plan de quelques points ? » Range dans « Format d'écran ». Beaucoup trouvent leur vidéo « lue » avec le texte complet ; un plan de 5 points et l'accroche apprise par cœur donnent un ton plus naturel.
4. « Où places-tu l'écran de lecture par rapport à la caméra ? » Conseille juste sous l'objectif. Range dans « Plateau ».
5. « Tu portes une tenue fixe pour tes vidéos ? » Une tenue constante aide à être reconnu. Range dans « Plateau ».

## Construire
1. **Le branchement (l'utilisateur guidé par Claude, 10 min, une seule fois).** Branche la caméra (ou son adaptateur) directement sur un port USB 3 de l'ordinateur (souvent bleu, à l'arrière du PC), sans concentrateur. Claude lance `python outils/verif.py cameras` : la liste des caméras et des micros vus par l'ordinateur. Puis `python outils/verif.py cameras --camera "<nom exact>"` : la plus grande résolution proposée. Si la 4K manque alors que la caméra filme en 4K, change de port et relance. Sur Mac, `cameras` liste les appareils ; vérifie la résolution dans le logiciel d'enregistrement.
2. **Le réglage du logiciel (l'utilisateur guidé par Claude, 20 min, une seule fois).** Dans OBS Studio : Paramètres, Vidéo, résolution de base et de sortie à la taille de la caméra (3840x2160 si elle filme en 4K, sinon 1920x1080), images par seconde égales à celles de la caméra (souvent 30). Paramètres, Sortie, mode avancé, format MP4 ou MKV, encodeur matériel s'il existe (NVIDIA, AMD ou Intel). Une scène « Caméra » avec seulement la caméra et le micro : jamais la capture de l'écran. Dans la source caméra, choisis la résolution la plus haute proposée. Filme large : tête, épaules et de l'air au-dessus de la tête. Écris tous ces réglages dans `wiki/maps/tournage.md`.
3. **La prise test (l'utilisateur 1 min, Claude 1 min, avant CHAQUE séance).** Il filme 10 secondes en parlant normalement. Claude lance `python outils/verif.py test.mp4 --attendu 3840x2160 --fps 30` (les valeurs de `tournage.md`). La sortie dit « PRÊTE À TOURNER » ou la raison en clair : résolution trop petite, son absent, son qui sature, son trop faible. Puis `python outils/planche.py test.mp4 --n 4 -o planche.jpg` pour le cadrage et la lumière.
4. **L'écran de lecture (Claude, 2 min).** `python outils/ecran.py outputs/youtube/<slug>/script.md`. Les lignes entre crochets sont des notes (repères de diapo, gestes), dans la couleur secondaire de la charte. Dans le navigateur : F11, puis Espace pour avancer, + et - pour la taille. Choisis texte complet ou plan selon « Format d'écran ».
5. **La checklist du jour (Claude, 10 min).** `outputs/tournage/AAAA-MM-JJ.md` : prise test passée, batterie et carte mémoire, micro testé, lumière, tenue, photo de miniature prévue (pose, regard, objet), ordre des vidéos, une prise par accroche si des essais sont prévus. Seule la caméra est enregistrée, jamais l'écran.
6. **Le dépôt (l'utilisateur, 2 min).** Il nomme chaque prise avec son numéro et un mot (« 1 prix »), la dépose dans le dossier convenu (hors de la synchronisation, voir `montage-video-code`) et dit « j'ai tourné ». Claude relance `verif.py` sur chaque fichier avant le montage.

## Test
`python outils/verif.py --test` et `python outils/ecran.py --test` écrivent « AUTO-TEST OK » ; la prise test du jour sort « PRÊTE À TOURNER » à la résolution de `tournage.md` ; l'écran de lecture s'ouvre avec le script validé ; la checklist du jour est cochée.

## Pièges vécus
- **Une caméra 4K derrière un concentrateur USB 2.** L'adaptateur ne proposait que du 720p, sans aucun message. Des semaines de vidéos ont été tournées ainsi ; la version « 4K » publiée était un agrandissement. Port USB 3 direct, et `verif.py cameras` puis la prise test à chaque séance.
- **Le logiciel réglé en 720p malgré l'option « haute qualité ».** Le réglage de la scène primait. La prise test mesurée par ffprobe a montré l'écart ; une case cochée ne prouve rien.
- **Un logiciel d'enregistrement en ligne qui saccadait.** La caméra se figeait toutes les dizaines de secondes dans l'application, quelle que soit la qualité choisie. OBS enregistrait la même caméra sans défaut. En cas de saccades, compare avec OBS avant de chercher plus loin.
- **L'écran capturé avec le script à côté de la caméra.** Au montage, tout a dû repasser en caméra seule. La scène d'enregistrement ne contient que la caméra et le micro.
- **Un cadrage trop serré.** Les montages verticaux avec texte et panneau au-dessus manquaient de place, et les gestes sortaient du cadre. Filme large : tête, épaules, de l'air au-dessus de la tête.
- **Des accroches jouées avec décor et mise en scène.** Jugées irréalistes, jamais tournées. Écris des accroches qu'il peut dire face caméra.
- **Une tenue différente à chaque vidéo.** Rien ne liait les vidéos entre elles. Une tenue fixe aide à être reconnu.

## Entretien dans le temps
Chaque problème de séance devient une ligne de la checklist et, si c'est mesurable, un contrôle de `verif.py`. La prise test reste obligatoire même quand tout marchait la veille : un câble déplacé suffit.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (matériel, réglages, résolution visée, tenue). Propose ensuite `montage-video-code`.
