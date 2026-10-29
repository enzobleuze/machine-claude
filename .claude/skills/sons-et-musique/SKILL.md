---
name: sons-et-musique
description: "Monte la sonothèque de la marque (bruitages et musiques, chaque son avec sa licence et ses plateformes permises) et pose la couche son des montages : musique sous la voix au bon écart, bruitages calés sur leur pic et seulement sur un mouvement visible, écarts minimum entre deux sons, niveau final mesuré, version sans musique pour la revue. Fournit deux outils testés. Utiliser quand l'utilisateur dit « ajoute de la musique », « mets des bruitages », « le son de ma vidéo est bizarre », « la musique couvre ma voix ». Pas pour le montage image (utiliser montage-video-code)."
---
# Sons et musique

## Pourquoi
Claude n'entend pas. Dans le système d'origine, les premiers montages avaient des effets mal placés, des « pops » en rafale, une musique qui couvrait la voix, et des titres dont la licence était douteuse. La brique a réglé quatre choses : une sonothèque où chaque son a sa licence et ses plateformes permises, des règles de placement chiffrées validées par l'entrepreneur, un mixage qui mesure tout (volume de la voix, de la musique, de chaque bruitage, niveau final), et une écoute humaine dans l'app de revue avec un bouton « sans musique » pour comparer. La musique sous licence commerciale sert seulement là où la plateforme la couvre.

## Prérequis
- `montage-video-code` (pour `commun.py`, obligatoire, et l'app de revue). `charte-graphique` conseillé : ses mots d'ambiance guident le choix de la musique.
- Python 3.10 ou plus récent, ffmpeg 7.1 ou plus récent.
- Sources de sons libres, au choix : Openverse (sans clé, filtres CC0 et CC BY), Freesound (compte gratuit), Pixabay et Mixkit (licences maison, à lire), packs CC0. Musique sous licence commerciale : la bibliothèque de la plateforme (sons Instagram et TikTok, bibliothèque audio YouTube) ou un service payant (Epidemic Sound, Artlist), seulement si l'utilisateur veut payer.
- Facultatif : un outil d'écoute par IA (par exemple earshot, open source) pour décrire un mixage. Il ne remplace jamais l'écoute de l'utilisateur.
- Outils joints dans `outils/`, chacun avec `--test` : `sonotheque.py` (le catalogue avec licences, la mesure du pic de chaque bruitage, le choix d'une musique accordée à la charte) et `mixage.py` (la couche son complète et le niveau final).

## Interview
Lis d'abord : `wiki/maps/montage.md`, `wiki/maps/sons.md` s'il existe, `wiki/business/charte.md` (les mots d'ambiance), `wiki/maps/moi.md` (abonnements). Puis demande, une question à la fois :
1. « Tu veux de la musique sous ta voix, ou ta voix seule ? Et sur les vidéos longues : musique partout, ou seulement dans l'intro ? » Range dans `wiki/maps/sons.md`, section « Goût ». Le système d'origine a fini avec de la musique seulement dans l'intro des vidéos longues, et sous toute la durée des Reels.
2. « Des bruitages (petits sons quand un texte ou une carte arrive) : oui, un peu, ou pas du tout ? » Range dans « Goût ».
3. « Un son que tu détestes déjà ? » Range dans « Bannis » : le nom exact du fichier ou de l'effet, rien de plus large.
4. « As-tu un abonnement musique ? Sinon, on reste sur du libre. » Range dans « Sources ».
5. « Sur Instagram et TikTok, tu choisis toi-même le son tendance à la publication ? » Ces plateformes ont leurs propres sons : souvent c'est l'utilisateur qui décide au moment de publier, et le montage part alors sans musique.

## Construire
1. **Installer (Claude, 5 min).** Copie `outils/sonotheque.py` et `outils/mixage.py` dans `outils/` du vault (avec `commun.py` de `montage-video-code`). Lance les deux `--test` : « AUTO-TEST OK ».
2. **La sonothèque de départ (Claude, 20 min).** Cherche une vingtaine de sons libres : `https://api.openverse.org/v1/audio/?q=whoosh&license=cc0,by` (remplace « whoosh » par « click », « pop », « notification », « impact », puis par des musiques calmes accordées aux mots de la charte). Pour chaque fichier retenu (téléchargé avec l'accord de l'utilisateur) : `python outils/sonotheque.py ajouter <fichier> --type bruitage --role whoosh --licence CC0 --source <lien de la page>` (CC BY : ajoute `--attribution "Titre, auteur, licence"`). Une musique : `--type musique --humeurs calme,chaud`. Une musique dont la licence ne couvre pas YouTube : `--plateformes instagram,tiktok`. L'outil range le fichier dans `bibliotheque/sons/<rôle>/` et mesure sa durée, son pic et son niveau.
3. **Les règles écrites (Claude, 10 min).** Dans `wiki/maps/sons.md`, recopie les règles de départ et ce que l'interview a dit : musique 18 dB sous la voix (12 a été jugé trop fort) ; un bruitage seulement sur un mouvement visible (une carte qui arrive, une bulle qui pop), jamais sur une simple coupe ; au moins 1,5 s entre deux pops ; jamais deux fois le même fichier de suite ; niveau final -14 LUFS pour les réseaux, -16 si le premier mot sonne écrasé. Ces écarts sont dans `mixage.py` (`ECART_VOIX`) et `sonotheque.py` (`ECART_MIN`) : une note de l'utilisateur change le chiffre dans le code, avec son test.
4. **Mixer une vidéo (Claude, 5 min).** `python outils/mixage.py <video>.mp4 -o <sortie>.mp4 --musique auto --plateforme youtube` (vidéo longue : ajoute `--intro 20`). Les bruitages viennent d'un `sons.json` (`[{"role": "whoosh", "t": 3.2}]`, t = l'instant de l'action visible) : `reels-et-shorts` l'écrit tout seul, sinon Claude l'écrit depuis le plan des moments. L'outil cale le pic de chaque son sur son instant, retire un son trop près du précédent de son rôle, refuse une musique non permise sur la plateforme, et écrit `<sortie>_sans_musique.mp4` et `<sortie>.son.json` (ce qui est placé, ce qui est retiré et pourquoi).
5. **Le contrôle (Claude, 5 min).** `python outils/mixage.py mesurer <sortie>.mp4` doit donner la cible à un point près, crête sous -1 dBTP. Lis `<sortie>.son.json` : un son retiré pour « aucun son de ce rôle permis » veut dire qu'il manque ce rôle dans la sonothèque. Avec un outil d'écoute, fais décrire le mixage et repérer les effets trop rapprochés.
6. **L'écoute (l'utilisateur, 5 min).** Dans l'app de revue (`revue.py`), il écoute au casque puis sur le haut-parleur du téléphone, avec et sans musique (bouton « Sans musique »). Chaque remarque devient une règle de `wiki/maps/sons.md` et, si c'est un chiffre, un réglage dans le code.

## Test
`python outils/sonotheque.py verifier` sort 0 avec au moins 20 sons (licence, source et plateformes notées pour chacun), et une vidéo mixée mesure la cible à un point près (`mixage.py mesurer`), avec une musique que l'utilisateur juge sous sa voix à l'écoute.

## Pièges vécus
- **Un son détesté revenait partout.** Un « pop doux » d'un logiciel de montage, jugé ridicule par l'entrepreneur. Le bannissement a ensuite été élargi à tort à tous les pops, que l'entrepreneur voulait garder. Un goût devient une règle écrite, et un bannissement vise le fichier nommé, jamais toute sa famille (`sonotheque.py bannir <id>`).
- **Des effets sur chaque coupe.** Épuisant à l'oreille. Un bruitage suit un mouvement visible ; une coupe d'un zoom à l'autre reste muette.
- **Des pops en rafale.** Plusieurs sons du même genre à quelques dixièmes de seconde : un bruit de jeu vidéo. Les écarts minimum par rôle règlent ça (pop 1,5 s, whoosh 0,35 s, impact 1,5 s).
- **Un son calé sur son début au lieu de son pic.** Un whoosh dont le souffle culmine au milieu arrivait en retard sur l'image. L'outil mesure le pic de chaque fichier et le pose sur l'instant de l'action.
- **Une musique trop forte.** À 12 dB sous la voix, elle gênait l'écoute ; 18 dB a été validé. Mesurer la voix et la musique avant de les mélanger évite de régler à l'aveugle.
- **Une musique commerciale sur YouTube.** Risque de réclamation sur une chaîne monétisée. La colonne « plateformes » tranche, et `mixage.py` refuse une musique non permise.
- **Un niveau final trop haut écrasait le premier mot.** Un limiteur poussé à fond aplatit les attaques. Si le premier mot sonne écrasé, descends la cible à -16.
- **Juger le son sur la forme d'onde.** Il faut mesurer et écouter. Les chiffres disent si c'est trop fort ; seule l'oreille dit si c'est agréable.
- **Des chiffres sur l'audio venus de nulle part.** « Le son fait la moitié de l'expérience », « tant de pourcent regardent sans le son » : rien de sourcé. Ne les écris ni dans un contenu, ni dans une règle.

## Entretien dans le temps
- Ajoute les sons bien notés, bannis ceux que l'utilisateur rejette (le fichier précis). Vise au moins trois fichiers par rôle utilisé : un même son qui revient se remarque.
- Relis les licences une fois par an (les conditions des services changent) et relance `sonotheque.py verifier`.
- Une tâche planifiée peut lancer `verifier` chaque mois et prévenir dans le résumé si un fichier manque.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (goût sonore, sons bannis, cible de niveau). Propose ensuite `reels-et-shorts` ou `decoupe-shorts`, puis `mesure-et-apprentissage`.
