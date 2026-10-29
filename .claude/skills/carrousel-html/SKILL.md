---
name: carrousel-html
description: "Fabrique les carrousels rendus en local aux couleurs de la charte (texte uni, idée forte en photo façon podcast, éditorial et conversation, vidéo courte en carrousel, vidéo longue en split, pub statique), sans crédit d'image, les fait revoir sur une page, puis en publie un par jour par une file. Utiliser quand l'utilisateur dit « fais un carrousel », « transforme ma vidéo en carrousel », « carrousel simple », « une pub statique », « revue des carrousels », « oui 1, 4 », « carrousel du jour ». Pas pour un carrousel aux images générées par IA (utiliser carrousel-image-ia)."
---
# Carrousels rendus en local

## Pourquoi
Dans le système d'origine, les carrousels aux images générées coûtaient des crédits et beaucoup de reprises. Un premier moteur en code avait été arrêté : son rendu ressemblait à ce que tout le monde produit. Le second a marché parce qu'il copiait au pixel près les mises en page de quelques comptes que l'entrepreneur aimait, avec sa propre marque : le texte vit dans un fichier JSON que le navigateur rend en images, sans rien payer. Avec une page de revue où il disait oui ou non, puis une file qui publie un carrousel par jour, la cadence est devenue tenable sans qu'il y pense.

## Prérequis
- `charte-graphique` (bloc D) : `bibliotheque/marque/charte.css` et `charte-jetons.json`. Tant qu'elle n'existe pas, l'outil prend la charte « simple » et le dit.
- `board-textes` (bloc C), le dossier du client idéal et la voix (bloc D), la ressource gratuite et son mot-clé s'il y en a un.
- `distribution-api` (bloc E) pour publier : la file écrit dans sa file de publication, elle ne publie rien seule.
- Python 3.8 ou plus récent. Aucune bibliothèque à installer pour le rendu.
- Un navigateur Chrome ou Edge. Windows 10 et 11 ont déjà Edge : rien à installer. Si l'outil ne le trouve pas, Claude pose le chemin une fois avec `setx NAVIGATEUR "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"` puis rouvre le terminal. Mac : Chrome ou Edge dans Applications. Linux : `sudo apt install chromium`.
- ffmpeg pour les images tirées d'une vidéo et le passage en JPEG (Windows : `winget install ffmpeg` ; Mac : `brew install ffmpeg`). Vérifier avec `ffmpeg -version`.
- Pour une vidéo transformée en carrousel : ses sous-titres en `.srt` ou `.vtt` (ceux envoyés à YouTube, ou une transcription locale faster-whisper).
- Option TikTok en mode photo : `pip install playwright` (le script se sert du Chrome déjà installé, aucun autre navigateur à télécharger).
- Outils joints, chacun testé hors ligne : `outils/carrousel.py` (rendu), `outils/file.py` (revue et file), `outils/tiktok-photo.py` (option TikTok).

## Interview
Lis d'abord : `bibliotheque/marque/charte-jetons.json` et `wiki/business/charte.md`, le dossier du client idéal, la fiche voix, `wiki/maps/carrousels.md` s'il existe, `wiki/maps/distribution.md` (réseaux branchés), la liste des mots-clés actifs s'il y en a une. Ne redemande rien de ce qui y est déjà.

Puis demande, une question à la fois :
1. « Montre-moi 2 ou 3 comptes dont tu aimes les carrousels. » Range dans `wiki/maps/carrousels.md`, section « Références ». Tu copies la mise en page, jamais les textes.
2. « Qu'est-ce que tu as comme matière : des vidéos face caméra, une vidéo longue par semaine, des vidéos courtes, ou seulement du texte ? » Range dans « Styles » : un style sans matière sort de la rotation.
3. « Une seule action en dernière slide. Le mieux : un mot à écrire en commentaire, qui envoie ta ressource en message privé si ton outil le fait. Sinon, le lien de ta bio. Lequel, et que reçoit la personne ? » Range dans « Action ».
4. « Ton pseudo ou ton site pour le pied de page ? » Il va dans le champ `pied` de chaque JSON.
5. « Sur quels réseaux, et à quelle heure tes clients regardent leur téléphone ? » Range dans `outputs/carrousels/reseaux.json` (étape 8).
6. « Tu veux revoir chaque carrousel avant qu'il parte ? » La réponse attendue est oui : la revue est la règle. Range dans « Règles ».

## Construire
1. **Installer (Claude, 5 min).** Copie les trois outils dans `outils/` du vault. Lance `python outils/carrousel.py --test`, `python outils/file.py --test` et `python outils/tiktok-photo.py --test` : chacun écrit « AUTO-TEST OK ». Le premier rend un carrousel de chaque style ; sans navigateur, il teste le HTML et le signale.
2. **Choisir le style (Claude, 2 min).** Un style par carrousel, d'après la matière du sujet :

   | Style | Quand | Ce qu'il faut | Déroulé |
   |:-|:-|:-|:-|
   | `podcast` | une idée forte dite face caméra | une vidéo de la personne | 5 à 7 slides ; couverture au mot géant rempli par la photo (`mot`, `ligne`, `italique`), puis du texte en capitales ; `align` à gauche ou à droite quand la personne est de l'autre côté de l'image |
   | `uni` | un enseignement en texte pur, le plus rapide | du texte | gros titre, lignes aérées ; `carte` avec un tableau « avant, après » pour la slide à garder |
   | `edito` | un plan en étapes | du texte, quelques images | titre, image au milieu, liste à `coches`, `bulle` de l'appel final |
   | conversation (`edito` + `messages`) | une scène de messages, puis la réponse qui sauve la situation | du texte | 6 à 8 slides : la phrase reçue et la question, la scène, la mauvaise réponse (celle qui part toute seule), ce que l'autre entend, la bonne réponse, pourquoi elle tient, l'appel |
   | `reel` | recycler une vidéo courte | la vidéo et ses sous-titres | 9 à 12 captures ; texte qui vend en boîtes (accroche, problème, mécanisme, ce soir, objection, appel), 22 mots au plus par slide |
   | `split` | le meilleur passage d'une vidéo longue, le jour de sa sortie | la vidéo et ses sous-titres | 8 à 11 slides, deux captures par slide, chacune avec la phrase dite à cet instant ; seulement des phrases réellement dites, sauf l'appel final |
   | pub statique | une publicité ou un post d'une image | du texte | `edito` ou conversation, une seule slide, `"taille": [1080, 1080]` ou `[1080, 1350]` |

   Rotation : jamais le même style deux jours de suite. Sans vidéo, un sujet saute `podcast`, `reel` et `split`.
3. **Les images (Claude, 10 min).** Une vidéo face caméra : `python outils/carrousel.py images video.mp4 --at 30,95.5 -o outputs/carrousels/<slug>/img` garde l'image la plus nette autour de chaque instant. Une vidéo courte ou longue : `python outils/carrousel.py reel video.mp4 --srt video.srt --debut 81 --fin 117 -o outputs/carrousels/<slug>` (ou `split`) écrit un brouillon `slides.json` avec ses images. Regarde toujours la planche (`python outils/planche.py "outputs/carrousels/<slug>/img/*.jpg" -o planche.jpg`) : si les yeux sont mi-clos sur une image, reprends-la 0,3 seconde plus tôt ou plus tard.
4. **Le texte (Claude, 15 min).** Pars de `python outils/carrousel.py exemple <style> > outputs/carrousels/<slug>/slides.json`, ou du brouillon. La couverture donne envie de la suite (test : « que veut-on voir après ? » ; si la réponse honnête est rien, c'est une étiquette). La slide 2 répond tout de suite à la couverture. Puis le problème, le mécanisme, ce qu'on fait ce soir, l'objection, l'appel. La réponse complète n'arrive jamais trop tôt. Une idée par slide, des phrases complètes avec un verbe, les mots d'un enfant de 12 ans, une consigne égale un geste faisable ce soir, et le récapitulatif ne fait que répéter ce qui a été dit. `*mot*` met un mot en valeur (un seul par slide), `\n` passe à la ligne. La légende va dans le champ `legende` du même fichier, pour que le board la couvre aussi : une première ligne qui tient seule en moins de 125 caractères, l'action, un morceau que le carrousel ne dit pas, le geste du soir, l'action redite, trois mots-dièse. Ensuite, deux lecteurs à froid (deux sous-agents neufs, chaque slide lue seule) : le client fatigué le soir, puis un ado de 14 ans. Chacun redit la slide en une phrase ; une slide mal redite se réécrit.
5. **La porte (Claude).** `slides.json` (slides et légende) passe par `board-textes`. Le `board.md` s'écrit à côté. Rien ne se rend en version finale sans verdict vert.
6. **Rendre (Claude, 2 min).** `python outils/carrousel.py rendre outputs/carrousels/<slug>/slides.json`. Les PNG 1080x1350 sortent dans `png/`, avec `_controles.txt` (contraste le plus bas de chaque slide). L'outil refuse un texte qui déborde, un texte trop près du bord, un contraste trop faible, deux boîtes fortes sur une slide, « glisse » ou un tiret long : corrige le texte, jamais l'outil. Regarde la planche (`python outils/planche.py "outputs/carrousels/<slug>/png/slide-*.png" -o planche.jpg`), puis relis-la en directeur artistique : désigne les deux slides les plus faibles et corrige seulement celles-là. Une retouche du texte après le verdict relance le board.
7. **La revue (l'utilisateur, 5 min).** `python outils/file.py revue` écrit `outputs/carrousels/revue/index.html`. Ouvre-la pour lui. Il clique Oui ou Non sous chaque carrousel, écrit une remarque s'il veut, puis « Copier ma réponse » et la colle dans la conversation (par exemple « oui 1, 4 · non 2 · 3 : la couverture est trop chargée »). Claude lance `python outils/file.py ajouter 1,4` (avec `--pas-avant 4:AAAA-MM-JJ` pour un carrousel lié à une sortie). La file refuse un carrousel sans verdict vert ou sans légende propre. Chaque remarque devient une règle de `wiki/maps/carrousels.md`, et dans le code quand c'est mesurable.
8. **Publier un par jour (Claude, 10 min).** Remplis `outputs/carrousels/reseaux.json` (écrit au premier lancement) depuis `wiki/maps/distribution.md` : l'heure, la rotation, et pour chaque réseau `max` (images au plus) et `mot_cle` (le mot en commentaire y envoie-t-il un message privé ?). Exemple : `"bluesky": {"max": 4, "mot_cle": false}`. Essaie d'abord `python outils/file.py du-jour --date <date d'un carrousel en file> --a-blanc`. Puis crée la tâche planifiée (bloc F, `taches-planifiees` et `wrapper-de-tache`) qui lance `python outils/file.py du-jour` chaque jour une heure avant l'heure de publication. Elle écrit les entrées dans `outputs/file-publication/<date>.json`, que le script de `distribution-api` programme. Là où le mot-clé ne répond pas, la dernière slide « Écris MOT » et la ligne d'appel de la légende sont retirées. Au-delà de la limite d'un réseau, l'appel final reste.
9. **TikTok en mode photo (option, Claude puis l'utilisateur, 15 min).** Seulement si l'outil de publication refuse le carrousel TikTok (il réclame une vidéo). `pip install playwright`, puis `python outils/tiktok-photo.py --setup` : une fenêtre s'ouvre, l'utilisateur se connecte une fois avec le code QR de son téléphone. Essai : `python outils/tiktok-photo.py --title "..." --text "..." --image a.jpg --image b.jpg --dry-run --headed`. Ensuite, Claude ajoute au script de publication une règle : une entrée avec `"voie": "navigateur"` lance `tiktok-photo.py` avec ses images et son texte. Pour des images générées par IA, ajoute `--contenu-ia` (les règles de TikTok demandent de les signaler) ; la décision de l'utilisateur va dans « Règles ». Plan de secours : un outil de publication qui accepte les carrousels TikTok, comme Metricool.

## Test
Les trois `--test` écrivent « AUTO-TEST OK ». Un vrai carrousel de 6 à 10 slides en 1080x1350 existe avec son `board.md` vert, l'utilisateur l'a dit oui sur la page de revue, et il figure dans `outputs/file-publication/` à sa date.

## Pièges vécus
- **Le look générique.** Le premier moteur en code produisait le même rendu que tout le monde et a été arrêté. Le second copie des mises en page précises, mesurées sur des comptes aimés (marges, tailles, interlignes), et les habille de la marque de l'utilisateur.
- **« Glisse » sur la couverture.** Jugé inutile : l'accroche suffit à donner envie. Une flèche entourée d'une ombre douce dans le coin le dit sans un mot, et l'outil refuse le mot.
- **Des captures aux yeux mi-clos.** Elles ont été refusées à la revue. Choisis des images où la personne a les deux yeux bien ouverts, sur la planche.
- **Des captures délavées.** Une vidéo de téléphone filmée en HDR donnait des images grises. L'outil les convertit maintenant ; sans la version complète de ffmpeg, il prévient.
- **Une vidéo courte recopiée en blocs.** La transcription posée telle quelle sur les captures ennuyait. Le texte d'un carrousel vend une idée. L'entrepreneur a aussi voulu beaucoup moins de captures de vidéos courtes que des autres styles.
- **Des mentions inutiles.** « Situation type », « mise en scène », des prénoms, l'heure d'un téléphone, une fausse interface d'application : retirés pour toujours. Une conversation n'est jamais présentée comme un vrai échange de client, ni en image ni en légende.
- **Des formules qui sonnent faux.** Une phrase défensive dans une légende (« personne ne peut te le promettre ») sonnait faux, et une accroche qui juge le lecteur le faisait partir. La file bloque les formules déjà refusées.
- **Une belle phrase que personne ne comprend.** Une image qu'il faut traduire dans sa tête, ou un récapitulatif qui parle d'une étape jamais annoncée : les lecteurs à froid les attrapent avant la publication.
- **Un carrousel refusé par une API.** Un réseau attendait une vidéo à la place des photos, et chaque réseau a sa propre limite d'images. Ces limites vivent dans `reseaux.json`, et TikTok passe par le navigateur.
- **Un échec qui n'en était pas un.** TikTok Studio affichait le post avec du retard : le script recharge plusieurs fois avant de conclure, et vérifie qu'un post n'est pas déjà en ligne avant de reposter.
- **Le même son à chaque fois.** Un historique empêche un son de revenir avant 15 carrousels, et jamais un « son original » d'un inconnu.

## Entretien dans le temps
- Chaque style garde son exemple validé dans `wiki/maps/carrousels.md`. Chaque remarque de revue y devient une règle, puis un refus dans l'outil quand on peut la mesurer.
- Chaque semaine, `python outils/file.py etat` montre la file. Le gardien du bloc F surveille la tâche du jour.
- `mesure-et-apprentissage` compare les styles (enregistrements et partages pour 100 vues, réactions sur la slide 2 comparées à la couverture). Un style qui perd sort de la rotation de `reseaux.json`.
- Après un changement de charte, relance `rendre` sur les carrousels encore en file.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (styles retenus, action finale, réseaux, heure), et ajoute la ligne dans `wiki/maps/routage.md`. Propose ensuite `carrousel-image-ia` s'il veut des visuels générés, sinon `accroches`.
