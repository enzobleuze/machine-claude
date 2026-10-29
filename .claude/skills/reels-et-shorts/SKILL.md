---
name: reels-et-shorts
description: "Met en place la chaîne des vidéos courtes face caméra (Reels, Shorts, TikTok) : script court, fiche du jour, dépôt des prises, coupe, montage à un gabarit aux couleurs de la marque (« rythme » : plans courts et écran partagé ; « éditorial » : panneau clair avec titre de section ; « simple » : face caméra sobre), cartes animées, sous-titres, appel final, son, revue, puis essais. Fournit un outil testé. Utiliser quand l'utilisateur dit « je veux faire des Reels », « écris mes scripts courts », « j'ai filmé, monte-les », « fais un Reel avec cette vidéo », « gabarit rythme », « gabarit éditorial ». Pas pour découper une vidéo longue (utiliser decoupe-shorts)."
---
# Reels et Shorts

## Pourquoi
Le système d'origine a construit une petite usine : les idées arrivent (banque, veille), chaque idée devient un script court avec plusieurs ouvertures, une fiche du jour liste ce qui reste à filmer, l'entrepreneur filme d'un bloc et dépose ses prises, Claude coupe et monte à un gabarit. Les leçons de mesure ont fixé deux règles : la phrase 1 est une scène, et 15 à 45 secondes tiennent mieux qu'un long monologue. Les gabarits viennent de Reels de créateurs mesurés image par image (durée des plans, première coupe, part de l'écran partagé), puis passés au filtre des notes de l'entrepreneur jusqu'à ce qu'il dise « garde-le comme ça ».

## Prérequis
- `banque-idees`, `veille-et-tendances`, `accroches`. Bloc C (`board-textes`, `agent-client-ideal`).
- `tournage` (prises vérifiées), `charte-graphique`, `montage-video-code` (pour `commun.py`, `transcrire.py`, `couper.py`, `rythme.py`, `revue.py`), `sons-et-musique` (pour `mixage.py` et la sonothèque). Tous ces outils dans le même dossier `outils/` du vault.
- ffmpeg 7.1 ou plus récent. Une caméra ou un téléphone qui filme au moins en 1080p, idéalement en 4K si la prise est en paysage.
- `essais-multiples` pour la mise en ligne.
- Outil joint : `outils/gabarit.py` (testé : `python outils/gabarit.py --test`).

## Interview
Lis d'abord : la banque, la banque d'accroches, `wiki/maps/machine-contenu.md`, `wiki/maps/moi.md` (temps disponible), `wiki/maps/montage.md` et `wiki/maps/sons.md`. Puis demande, une question à la fois :
1. « Avec quoi filmes-tu : téléphone à la verticale, ou caméra à l'horizontale ? » Range dans `wiki/maps/tournage.md`, section « Matériel ». À l'horizontale, filme large : l'outil recadre en vertical.
2. « Combien de vidéos courtes peux-tu filmer d'un bloc, et quel jour ? » Range dans `machine-contenu.md`, section « Cadence ».
3. « Où vas-tu déposer tes prises ? » (un dossier hors synchronisation, par exemple `Vidéos/montage/courts/_depot/`). Range dans `machine-contenu.md`.
4. « Lis-tu un texte ou parles-tu librement ? » Le format de la fiche en dépend.
5. Montre les trois gabarits sur une vidéo test (étape 4) puis demande : « Lequel te ressemble ? » Range dans `wiki/maps/reels.md`, section « Gabarit ». Un roulement entre deux ou trois gabarits est possible, et les chiffres trancheront (`mesure-et-apprentissage`).

## Construire
1. **Le gabarit de script court (Claude, 10 min).** Dans `wiki/maps/reels.md` : une durée cible (15 à 45 s), 5 ouvertures (de `accroches`), une scène, un principe, une action, un mot-clé ou une ressource à la fin. 60 à 170 mots au total. Un seul principe par vidéo.
2. **Les scripts et la fiche du jour (Claude, 20 min pour un lot).** Pour chaque idée choisie : `outputs/courts/scripts/<n>-<slug>.md` avec en tête la table des ouvertures. Passe le lot à `board-textes` puis à `agent-client-ideal`. Seuls les verts entrent dans `outputs/courts/fiche-du-jour.md`, avec un écran de lecture fait par `ecran.py` (`tournage`).
3. **Installer et tester l'outil (Claude, 10 min).** Copie `outils/gabarit.py` dans `outils/` du vault, lance `python outils/gabarit.py --test` (« AUTO-TEST OK »). Il a besoin de `commun.py`, `mixage.py`, `sonotheque.py` et `rythme.py` dans le même dossier.
4. **La première vidéo, un gabarit à la fois (Claude, 20 min).** Sur la première prise déposée : `verif.py` (`tournage`), puis `transcrire.py`, puis `couper.py --apercu` (`montage-video-code`) : le Reel part toujours d'une prise sans silence ni reprise. Ensuite Claude lit `transcription-coupee.json` et écrit `visuels.json` (format en tête de `gabarit.py`) : deux à quatre passages où une image MONTRE l'exemple, la scène ou la conséquence de ce qui est dit, sans recopier ses mots ; jamais deux visuels du même type de suite ; jamais dans les deux premières secondes ni pendant l'appel final ; un « punch » sur la phrase clé ; l'instant où commence l'appel final. Les textes des cartes passent `board-textes`. Prise à l'horizontale : `python outils/planche.py prise.mp4 --n 4` pour lire où est le visage (`--centre`).
5. **Rendre (Claude, quelques minutes).** `python outils/gabarit.py <coupe>.mp4 <transcription-coupee>.json --gabarit rythme --visuels visuels.json --mot-cle <MOT> --centre 0.5 -o outputs/courts/montage/<n>-<slug>/ --apercu`. L'outil coupe les plans sur des débuts de mots, place l'écran partagé et les cartes, pose les sous-titres à une place fixe par mise en page, ajoute l'appel « écris MOT en commentaire », le logo pendant l'appel s'il existe, les bruitages sur chaque action visible, la musique 18 dB sous la voix, et vérifie le rythme. Lis `montage.md` (mesures, sons retirés, police remplacée) et regarde `python outils/planche.py reel-apercu.mp4 --n 12`.
6. **La revue (l'utilisateur, 10 min).** `python outils/revue.py outputs/courts/montage` : il regarde sur son téléphone (`--reseau`), touche S pour voir les zones cachées par Instagram, TikTok et YouTube, N pour une note, A pour approuver. Claude écrit chaque note en règle dans `wiki/maps/reels.md` (ou dans le code de `gabarit.py`, avec son test) AVANT la vidéo suivante. Quand le gabarit est approuvé sans note, écris « Figé le AAAA-MM-JJ » dans `reels.md` : toute modification ensuite demande son accord.
7. **Le lot (Claude, en l'absence de l'utilisateur une fois le gabarit figé).** Monte toutes les prises du lot, une à la fois (le verrou de rendu l'impose), rends sans `--apercu` celles qu'il a approuvées, puis `essais-multiples` (une prise par ouverture, plusieurs essais par vidéo).

## Test
`python outils/gabarit.py --test` écrit « AUTO-TEST OK », et une prise réelle déposée ressort en Reel 1080x1920 au gabarit choisi, sans silence ni reprise, à -14 LUFS, approuvée dans l'app de revue, avec ses ouvertures prêtes pour les essais.

## Pièges vécus
- **Un premier essai statique et muet.** L'entrepreneur jugeait un gabarit comme un Reel fini : sans animation ni bruitage, il doutait de tout le travail, et il ne voulait pas répéter ses exigences. Un gabarit naît avec ses entrées animées, ses bruitages sobres et sa musique ; un essai montré démarre sur un début de phrase et reste publiable dans la forme. Un défaut connu se signale en une ligne AVANT qu'il regarde.
- **Des sous-titres qui bougeaient et changeaient de couleur.** Une seule allure de sous-titre pour tout le Reel, à une place fixe par mise en page (sur le torse en plein visage, sur la jointure en écran partagé).
- **Des cartes trop rapides pour être lues.** « On n'a même pas le temps de lire. » Moins de visuels, chaque élément à l'écran le temps de le lire, une tenue complète avant de partir.
- **Toujours le même type de carte.** Des textos à la suite lassaient ; alterner texto, liste et mot a plu. `gabarit.py` le signale dans `montage.md`, et la consigne de l'étape 4 l'évite.
- **Un cadrage suivi image par image, saccadé.** Le gabarit éditorial a fini en cadrage fixe, avec un zoom doux sur la phrase clé seulement.
- **Un cadrage trop serré au tournage.** Les mises en page avec panneau manquaient de place : filmer plus large (tête, épaules, de l'air au-dessus).
- **Une caméra à 720p.** Le plein écran vertical était agrandi près de trois fois, doux. Vérifie la résolution avant de monter (`verif.py`).
- **Un lot entier monté dans un style pas encore validé.** Les mêmes erreurs partout. Une vidéo, ses notes, les règles, puis la suivante.
- **Des effets jugés bon marché.** Lueurs, néons, dégradés de texte, rotations 3D, effets de panne : écartés. La sobriété de la charte passe avant l'effet.
- **Des transitions qui glissent.** L'entrepreneur les voulait douces, avec un léger flou de mouvement. Le chemin ffmpeg fait des coupes nettes (le style de référence) ; pour des glissements, passe par HyperFrames (`montage-video-code`, étape 10).
- **Des scripts traduits presque mot à mot depuis des vidéos étrangères.** Moins bons devant le client idéal que les versions libres.

## Entretien dans le temps
Chaque remarque de l'utilisateur sur un montage devient une règle écrite, de préférence dans le code de `gabarit.py` avec son test. Les réglages chiffrés sont en tête du fichier (`PLAN_CIBLE`, `SANS_VISAGE`, `ZOOM`, `SOUS_VOIX`, `Y_ST`). `mesure-et-apprentissage` dit quels gabarits, sujets et durées gagnent ; la fiche du jour se trie avec.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (matériel, jour de tournage, gabarit figé). Propose ensuite `essais-multiples`.
