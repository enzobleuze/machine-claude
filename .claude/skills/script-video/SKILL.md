---
name: script-video
description: "Écrit le script d'une vidéo longue au format lettre à une vraie personne, assez simple pour qu'un enfant le comprenne : accroche, une seule histoire, étapes répétées, récaps, appel. Utiliser quand l'utilisateur dit « écris le script de ma vidéo », « script YouTube sur X », « mon script est trop dense ». Pas pour un script de 30 secondes (utiliser reels-et-shorts)."
---
# Script vidéo

## Pourquoi
Le premier script long du système d'origine était riche, avec des boucles et des étapes, mais trop dense : il fallait être très concentré pour suivre, même pour celui qui le disait. La correction a gardé ce qui plaisait (l'histoire, les accroches, les étapes) et ajouté la simplicité : une seule histoire, chaque étape dite en une phrase qu'on répète, un récap avant de passer à la suite. Le format qui a pris : une lettre de coaching à un homme ou une femme précise, lue devant la caméra. Sur une vidéo réelle, une bonne part des mots dits n'étaient pas dans le script, souvent les meilleurs : le script guide la voix, il ne l'enferme pas.

## Prérequis
- `banque-idees`, `accroches`, `youtube-systeme` (le paquet de la vidéo).
- Bloc D (voix, paroles réelles de l'utilisateur), bloc C (`board-textes`, `agent-client-ideal`, carnet expert).

## Interview
Lis d'abord : la fiche voix, les transcriptions de ses vidéos passées (ses vraies phrases), `outputs/youtube/<slug>/`, la colonne « Pièces faites » de la banque (pour ne pas redonner un principe déjà donné). Puis demande :
1. « Pour qui est cette vidéo ? Une personne, sa situation de ce soir. » Range en tête du script.
2. « Tu lis tout ton texte, ou tu préfères une fiche avec tes phrases clés et des notes ? » Range dans `wiki/maps/tournage.md`, section « Format d'écran ». Les deux ont marché selon les moments : demande-lui.
3. « As-tu une histoire vraie (à toi, ou d'un client avec son accord et sans son nom) pour cette vidéo ? »

## Construire
1. **Le fond d'abord** (Claude, 15 min). Avant d'écrire une ligne : 3 phrases réelles de l'utilisateur sur ce thème (avec leur chemin dans le vault), la réponse du carnet expert, un principe central unique en une phrase, absent des vidéos déjà faites.
2. **L'ossature** (Claude, 10 min). Accroche (3 variantes de types différents, `accroches`), la promesse de la vidéo, une seule histoire (une personne, une scène), 3 étapes au plus, un récap oral après chaque étape, un appel doux au milieu, l'appel principal à la fin. Durée cible : compte environ 150 à 230 mots par minute selon son débit, mesuré sur une de ses vidéos.
3. **Le texte** (Claude, 20 min). Écris dans sa voix, avec ses phrases réelles. Une idée par phrase. Aucun retour en arrière dans le temps sans le dire. Écris dans `outputs/youtube/<slug>/script.md` le texte complet et, si l'utilisateur préfère, `fiche.md` (les phrases exactes de l'accroche, des récaps et des appels, le reste en notes).
4. **Le test de l'enfant** (Claude, 5 min). Fais lire le script par un sous-agent sans contexte, à qui l'on dit : « Raconte cette vidéo en 3 phrases à un enfant de 10 ans. » S'il n'y arrive pas, simplifie et recommence.
5. **La porte** (Claude). `board-textes` (bloc C) puis `agent-client-ideal` en mode test : où décroche-t-il ? Corrige à ces endroits.
6. **L'écran** (Claude). Passe le texte validé à `tournage` pour l'écran de lecture.

## Test
Le script a un verdict vert du board, un sous-agent neuf le raconte en 3 phrases justes, et chaque étape apparaît au moins deux fois (annoncée, puis récapitulée).

## Pièges vécus
- Plusieurs personnages qui s'empilent dans la même vidéo : le spectateur fatigué décroche en essayant de suivre qui fait quoi.
- Un récap qui parle d'une étape jamais annoncée.
- Le texte complet lu à l'écran peut sonner lisse ; la fiche à notes a donné plus d'élan à un moment, puis l'entrepreneur est revenu au texte complet parce que les notes le ralentissaient. Les deux se proposent, il choisit.
- Le même conseil donné dans deux vidéos de suite : tiens un registre des principes déjà donnés.

## Entretien dans le temps
Après chaque tournage, compare la transcription au script : les phrases improvisées qui ont marché rejoignent ses paroles réelles dans le vault. Les endroits où la rétention chute (`mesure-et-apprentissage`) deviennent des règles du gabarit.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (format d'écran choisi). Propose ensuite `tournage`.
