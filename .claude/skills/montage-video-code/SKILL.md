---
name: montage-video-code
description: "Monte les vidéos par le code, aux couleurs de la marque : transcription locale, coupe des silences, hésitations, reprises et bruits de bouche, plan des moments (chapitres, citations, listes, textes, zooms, plans de coupe), sous-titres, aperçu léger, contrôle du rythme, app de revue où l'on pose une note à l'instant précis, rendu final rapide (carte graphique si elle existe). Fournit sept outils testés. Utiliser quand l'utilisateur dit « monte ma vidéo », « coupe les silences », « habille ma vidéo », « j'ai tourné », « je veux revoir le montage ». Pas pour un Reel monté à un gabarit (utiliser reels-et-shorts), ni pour découper une vidéo longue en Shorts (utiliser decoupe-shorts), ni pour la musique (utiliser sons-et-musique)."
---
# Montage vidéo par le code

## Pourquoi
Un monteur coûte cher et un logiciel de montage demande des heures. Le système d'origine monte par le code : la prise est transcrite en local, les coupes se calculent sur les mots, l'habillage suit un plan écrit moment par moment, et l'entrepreneur regarde un aperçu dans une petite app de revue où chaque note se pose à la seconde près. Chaque note devient une règle écrite avant la vidéo suivante. Deux leçons ont fixé la méthode : valider un style sur une seule vidéo avant d'en monter un lot, et ne jamais lancer plusieurs rendus lourds à la fois (le PC a gelé avec trois rendus en parallèle). Les tours de revue se font en aperçu léger, avant un seul rendu final.

## Prérequis
- `tournage` (prises vérifiées), `charte-graphique` (sinon les outils prennent la charte « simple » et le disent), `script-video` pour les vidéos longues.
- Python 3.10 ou plus récent, ffmpeg 7.1 ou plus récent (Windows : `winget install ffmpeg` ; Mac : `brew install ffmpeg`). C'est toute la base : chaque outil marche avec ffmpeg seul.
- Transcription : `pip install faster-whisper` (gratuit, le modèle d'environ 1,5 Go se télécharge au premier usage). Autre voie sans paquet Python : le filtre whisper de ffmpeg avec un fichier modèle (voir l'en-tête de `transcrire.py`).
- Facultatif : une clé Pexels gratuite pour les plans de coupe (`broll.py`). Facultatif et plus lourd : HyperFrames (Node.js 22 ou plus) pour des animations plus riches (étape 10).
- Outils joints dans `outils/`, chacun avec `--test` :

| Outil | Rôle |
|---|---|
| `commun.py` | la boîte partagée : ffmpeg, encodeur (carte graphique ou processeur), verrou de rendu, charte, sous-titres ASS. Obligatoire pour tous les autres outils vidéo du kit |
| `transcrire.py` | prise vers transcription mot par mot (format Whisper) |
| `couper.py` | retire silences, hésitations, reprises et bruits de bouche ; écrit la liste des coupes à relire |
| `habiller.py` | plan des moments vers vidéo habillée (cartes, textes, zooms, plans de coupe, sous-titres, logo) ; tableau des moments et chapitres YouTube |
| `rythme.py` | contrôle du rythme sur les pixels (trou mort, élément qui clignote), en avertissement |
| `revue.py` | app locale de revue : notes horodatées, approbation, zones cachées par les réseaux, bouton « sans musique » |
| `broll.py` | plan de coupe libre de droits (Pexels) avec sa trace de licence |

## Interview
Lis d'abord : `wiki/maps/tournage.md` (matériel, résolution), `wiki/business/charte.md` et `bibliotheque/marque/charte-jetons.json`, `wiki/maps/montage.md` s'il existe, `wiki/maps/sons.md` s'il existe. Ne redemande rien de ce qui y est.

Puis demande, une question à la fois :
1. « Montre-moi une à trois vidéos dont tu aimes le montage. » Range les liens dans `wiki/maps/montage.md`, section « Références ». On copie le mouvement et le rythme (durée des plans, entrée des textes, place des sous-titres), jamais les mots ni les images.
2. « Tu veux un montage sobre (coupes et sous-titres) ou habillé (cartes, zooms, plans de coupe) ? » Range dans « Style ». Conseille sobre pour les trois premières vidéos : sortir compte plus que l'habillage.
3. « Pour tes vidéos longues, sous-titres incrustés dans l'image ou fichier de sous-titres envoyé à YouTube ? » Range dans « Sous-titres ». Le fichier se corrige après coup ; l'image, jamais.
4. « Tu veux revoir chaque vidéo avant publication, ou seulement les premières ? » Range dans « Validation ».
5. « Où ranges-tu tes prises ? » Propose un dossier hors de tout dossier synchronisé dans le nuage (Dropbox, Google Drive et les autres), par exemple `Vidéos/montage/` : les gros fichiers vidéo y ralentissent tout, et un fichier verrouillé par la synchronisation en plein rendu fait échouer l'écriture. Range dans « Dossiers ».

## Construire
1. **Installer les outils (Claude, 10 min).** Copie les sept fichiers de `outils/` dans `outils/` du vault, avec `planche.py` du kit s'il n'y est pas. Lance `python outils/commun.py --test`, puis le `--test` de chaque outil : chacun écrit « AUTO-TEST OK ». Écris dans `wiki/maps/montage.md` l'encodeur choisi (`python -c "import sys; sys.path.insert(0, 'outils'); import commun; print(commun.encodeur())"` : carte graphique NVIDIA, AMD, Intel ou Mac, sinon processeur). Polices : si un rendu écrit « police remplacée », télécharge les polices de la charte sur Google Fonts (gratuites) et range les `.ttf` dans `bibliotheque/marque/polices/`, ou fais installer la police à l'utilisateur (double-clic sur le fichier, puis « Installer »).
2. **Transcrire (Claude, 5 min plus le calcul).** Une seule fois : `pip install faster-whisper`. Puis `python outils/transcrire.py <prise>.mp4 <dossier>/<slug>/transcription.json`. Une prise de 15 minutes prend quelques minutes sur le processeur.
3. **Couper (Claude, 15 min).** `python outils/couper.py <prise>.mp4 <dossier>/<slug>/transcription.json -o <dossier>/<slug>/ --apercu`. Lis `coupes.md` en entier, surtout les reprises et les bruits. Une coupe douteuse : remets le morceau dans `garder` de `coupes.json`, puis relance avec `--depuis <dossier>/<slug>/coupes.json`. Le rendu sans `--apercu` se fait à la fin, une seule fois.
4. **Le plan des moments (Claude, 20 min).** Écris `<dossier>/<slug>/plan.json` (format en tête de `habiller.py`) depuis `transcription-coupee.json` et le script. Une carte de chapitre à chaque grande partie, une citation pour une phrase-principe, une liste pour un récapitulatif d'étapes, un texte seulement quand la phrase dite le justifie, un zoom sur la phrase clé, un plan de coupe pour une scène concrète (`python outils/broll.py "action précise en anglais" --usage <slug>`). Chaque élément porte « dit » (la phrase) et « prouve » (ce qu'il montre). Variété : jamais deux fois le même type de suite, aucun type au-delà d'un quart des moments. Puis `python outils/habiller.py verifier <dossier>/<slug>/plan.json --video <dossier>/<slug>/coupe-apercu.mp4` : corrige jusqu'à zéro alerte, ou note dans `montage.md` l'alerte acceptée et pourquoi.
5. **L'aperçu et la planche (Claude, 15 min).** `python outils/habiller.py rendre <dossier>/<slug>/coupe-apercu.mp4 <dossier>/<slug>/plan.json --sous-titres <dossier>/<slug>/transcription-coupee.json --apercu`. Puis la commande de planche écrite au bas de `tableau-moments.md` (une image au milieu de chaque moment). Lis la planche d'abord : note chaque image sur 10 (lisibilité, place du visage, couleur, idée), corrige les trois pires points jusqu'à 8 partout. Seulement ensuite, montre-la.
6. **Le son (Claude, 5 min).** Avec `sons-et-musique` : `python outils/mixage.py <aperçu habillé>.mp4 -o <dossier>/revue/<slug>.mp4 --musique auto --plateforme youtube --intro 20`. Il écrit aussi la version sans musique et la frise des sons pour la revue.
7. **Le rythme (Claude, 2 min).** `python outils/rythme.py <dossier>/revue/<slug>.mp4 --profil long` (Reel : `--profil reel`). Un trou mort ou un clignotement : regarde l'instant indiqué, corrige s'il gêne. C'est un avertissement, jamais un blocage.
8. **La revue (l'utilisateur 10 min, Claude 5 min).** Lance `python outils/revue.py <dossier>/revue` : le navigateur s'ouvre. Guide l'utilisateur : « Espace pour lire. Quand quelque chose te gêne, appuie sur N, écris ta note, Entrée. Quand la vidéo est bonne, appuie sur A. » Avec `--reseau`, il regarde sur son téléphone (même Wi-Fi) : c'est là que les gens verront la vidéo. Ensuite, lis `notes_a_traiter.md`. Écris chaque note en règle datée et numérotée dans `wiki/maps/montage.md` avant de corriger, puis corrige. L'ancienne version va dans `<dossier>/revue/_anciennes/`.
9. **Le rendu final (Claude, le temps du calcul).** Après « approuvé » : relance `couper.py --depuis` sans `--apercu`, puis `habiller.py rendre` et `mixage.py` sur la coupe pleine résolution. La carte graphique encode si elle sait le faire, un seul rendu à la fois (verrou), en priorité basse. Puis `python outils/habiller.py chapitres <dossier>/<slug>/plan.json` donne les chapitres YouTube aux vrais temps du montage. Passe la main à `distribution-api` (vidéo, chapitres, fichier `.srt` si l'option `--srt` a servi).
10. **Option HyperFrames, pour des animations plus riches (Claude 20 min, seulement si l'utilisateur le veut).** Le chemin ffmpeg fait des coupes nettes et des cartes simples. Pour des transitions glissées, des cartes arrondies et des animations calées image par image : `winget install OpenJS.NodeJS.LTS` (Mac : `brew install node`), puis `npx -y hyperframes@<version> init essai`, `npx -y hyperframes@<version> browser ensure`, `npx -y hyperframes@<version> doctor`. Écris la version qui marche dans `montage.md` et écris-la toujours dans la commande. Copie `bibliotheque/marque/charte.css` dans le projet : la composition n'utilise que ses variables. Règles du moteur : chaque élément timé a ses attributs de début, de durée et de piste ; la vidéo est muette, le son passe par une piste à part ; rien d'aléatoire ni d'horloge dans les animations. Les skills HyperFrames s'ajoutent à Claude Code par `npx skills add heygen-com/hyperframes`. Pour une vidéo en 4K, rends seulement le calque d'animation (fond transparent) et pose-le sur la caméra avec ffmpeg : c'est ce qui a rendu le rendu 4K supportable dans le système d'origine.

## Test
Les deux preuves sont obligatoires :
- Chaque outil de `outils/` écrit « AUTO-TEST OK » avec `--test`.
- Une vraie prise passe la chaîne (transcrire, couper, habiller, mixer), sort à la résolution filmée sans silence ni hésitation audible, et l'utilisateur l'a approuvée dans l'app de revue (`approuve` vaut `true` dans son `.notes.json`), ou ses notes sont devenues des règles datées dans `wiki/maps/montage.md`.

## Pièges vécus
- **Les bruits de bouche passaient entre les mailles.** Un logiciel de coupe retirait les silences et les « euh », mais gardait les claquements de lèvres et la toux : ils ne sont ni silencieux ni transcrits. L'entrepreneur repassait derrière à la main. `couper.py` cherche un son court et fort sans mot dessous, entre deux mots.
- **Une coupe trop serrée mangeait la fin des mots.** La transcription finit souvent un mot un peu trop tôt. Chaque bord de coupe glisse jusqu'au creux de la voix, un quart de seconde au plus.
- **Des coupes en plein milieu d'une phrase.** Une détection trop zélée a jeté des phrases simplement dites autrement. Seules les vraies reprises partent, et deux phrases complètes qui commencent pareil n'en sont pas. Relis toujours `coupes.md`.
- **Le PC a gelé.** Trois rendus lourds lancés en parallèle. Le verrou de `commun.py` n'en laisse passer qu'un, en priorité basse, sur 4 fils. Deux conversations Claude sur le même lot la même nuit se sont aussi écrasées : une seule conversation par lot.
- **Un lot entier monté dans un style pas encore validé.** Les mêmes erreurs partout. Une vidéo, ses notes, les règles, puis la suivante. Une fois le style figé, Claude peut monter tout le lot en l'absence de l'utilisateur, qui revoit tout d'un coup dans l'app de revue.
- **Des animations posées partout pour faire « monté ».** Elles fatiguaient sans rien dire. Une animation n'apparaît que si la phrase dite la justifie : c'est le rôle du champ « prouve ». Un même type de carte sur près de la moitié des moments a aussi lassé : la règle de variété vient de là.
- **Des tours de revue en pleine résolution.** Chaque correction coûtait un long rendu. Les revues se font en aperçu léger ; la pleine résolution se rend une seule fois, après le oui.
- **Une vidéo annoncée en 4K était un agrandissement.** La caméra enregistrait en petite résolution sans prévenir (voir `tournage`). Exporte toujours à la résolution filmée, et vérifie-la.
- **Une vidéo sortie trop basse.** Un rendu mesuré bien sous -20 LUFS : les plateformes ne remontent jamais le son. Vise -14 (ou -16 si le premier mot sonne écrasé), voir `sons-et-musique`.
- **Une police remplacée sans prévenir.** Hors de la machine qui a la police, le texte sortait dans une autre. Les outils l'écrivent en clair : « police remplacée ».
- **Des chapitres devinés avant le tournage.** Ils tombaient à côté. Les chapitres viennent des cartes du montage, aux vrais temps, avec le premier à 00:00.
- **Une version du moteur d'animation changeait sous les pieds.** Une commande sans numéro de version prend la dernière parue. Épingle la version qui marche.

## Entretien dans le temps
- Les règles validées restent dans `wiki/maps/montage.md`, datées et numérotées. Chaque note de revue en ajoute une, de préférence chiffrée (« sous-titre à 1,5 s au moins à l'écran »), et quand c'est possible elle passe dans le code de l'outil, avec son test.
- Les anciennes versions et leurs notes vont dans `_anciennes/`. Les aperçus n'ont pas de ménage automatique : ajoute un nettoyage mensuel des aperçus de plus de 30 jours (bloc F, `taches-planifiees`).
- Après une mise à jour de ffmpeg ou de Python, relance tous les `--test`.
- `mesure-et-apprentissage` dit quels montages retiennent le mieux : les règles gagnantes montent en tête de `montage.md`.

## Après
Mets à jour `wiki/maps/parcours.md` (brique `montage-video-code` faite), une ligne dans `log.md`, et la mémoire (style validé, encodeur, dossier des prises). Propose ensuite `sons-et-musique`, puis `decoupe-shorts`.
