---
name: posts-reseaux
description: "Écrit et cadence les posts texte des réseaux (X, Threads, LinkedIn, Facebook) à partir des vraies phrases de l'utilisateur. Utiliser quand l'utilisateur dit « fais mes posts », « posts sur X », « combien je poste par jour », « mes Threads ». Pas pour les carrousels (utiliser carrousel-html) ni la publication elle-même (utiliser distribution-api)."
---
# Posts réseaux

## Pourquoi
Le système d'origine a fait varier sa cadence plusieurs fois. Un plafond prudent de quelques posts par jour bridait la portée d'un compte qui grandissait, alors que les comptes qui percent publient beaucoup, et beaucoup de réponses. À l'inverse, remplir un quota avec des posts faibles fait baisser l'engagement moyen, et la plateforme le lit comme un mauvais signal. Ce qui a tenu : un stock de posts qui tiennent debout seuls, un volume monté par paliers mesurés, et les réponses aux commentaires faites vite. Un réseau qui ne donnait presque aucune portée sans abonnement payant a été mis en pause plutôt que nourri à vide.

## Prérequis
- `banque-idees` et de préférence une pièce mère transcrite (`sujet-en-pieces`).
- Bloc D (voix), bloc C (`board-textes`, `controle-voix`).
- `distribution-api` pour publier sans copier-coller.

## Interview
Lis d'abord : `wiki/maps/machine-contenu.md` (réseaux, cadence), la fiche voix, les derniers posts publiés s'il les a exportés. Puis demande :
1. « Sur quels réseaux texte es-tu actif, et combien d'abonnés à peu près sur chacun ? » Range dans `machine-contenu.md`, section « Réseaux ».
2. « Combien de minutes par jour peux-tu donner aux réponses ? » Range dans « Cadence ». Les réponses comptent autant que les posts.
3. « Colle-moi 3 posts à toi qui ont bien marché. » Range dans `wiki/maps/posts-gabarits.md`, section « Gagnants ».
4. « Y a-t-il un réseau où tu veux payer pour la portée (abonnement vérifié) ? » La réponse change la cadence sur ce réseau.

## Construire
1. **Les gabarits** (Claude, 20 min). Dans `wiki/maps/posts-gabarits.md`, écris 8 à 12 gabarits de forme tirés de ses gagnants et de la veille : la phrase à garder, la scène éclair, la question qui appelle une vraie réponse, la petite liste pratique, le constat suivi de ce qu'on fait. Chaque gabarit a un numéro, un exemple et une règle de longueur. Repères qui ont servi : sur X, une ligne courte bat souvent le fil long ; sur Threads, l'accroche tient dans les premiers 150 caractères avant le « voir plus » ; sur LinkedIn et Facebook, une ligne d'ouverture puis des paragraphes courts.
2. **Le lot** (Claude, 20 min). À partir du `coeur.md` du sujet ou de la transcription, écris les posts du jour en tournant sur les gabarits. Reprends ses phrases réelles. Lien jamais dans le corps : en première réponse.
3. **La porte** (Claude). Chaque post passe par `board-textes` (bloc C) en lot. Un post refusé est réécrit ou jeté, jamais publié « quand même ».
4. **La cadence** (Claude, 10 min). Écris la règle dans `machine-contenu.md` : un palier de départ par réseau, une hausse seulement si l'engagement moyen par post tient sur 2 semaines, une baisse si les posts faibles s'accumulent. Les posts partent dans les fenêtres où son audience est réveillée, et l'utilisateur reste joignable 30 à 60 minutes après.
5. **Les réponses** (l'utilisateur, minutes choisies). Claude prépare chaque jour une liste des commentaires qui méritent une vraie réponse, avec une proposition. L'utilisateur répond lui-même ou valide.

## Test
Une semaine de posts existe en file, chacun avec son numéro de gabarit et son verdict vert, et la règle de cadence est écrite avec ses seuils de hausse et de baisse.

## Pièges vécus
- Le plafond prudent pris pour une loi : il venait d'un mauvais test fait avant les contrôles de qualité. Teste toi-même, par paliers.
- Le quota rempli de posts faibles : l'engagement moyen baisse et tout le compte en pâtit. Un post qui ne tient pas seul ne part pas.
- Des posts traduits mot à mot depuis d'autres comptes : vues rapides, risque d'être jugé non original. Passe par la veille et l'angle.
- Les vidéos et carrousels repostés tels quels sur un réseau texte y ont fait très peu de vues : adapte au format du réseau.
- Une question finale sur chaque post finit par sonner mécanique : garde-la pour un gabarit dédié.

## Entretien dans le temps
Chaque semaine, `mesure-et-apprentissage` classe les gabarits par résultat. Un gabarit perdant plusieurs semaines de suite sort ; un gagnant reçoit des variantes. Les abonnés se relèvent à date fixe pour voir la tendance.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (cadence et réseaux choisis). Propose ensuite `carrousel-html`.
