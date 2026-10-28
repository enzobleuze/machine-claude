---
name: offre-et-echelle
description: "Construit l'offre principale façon Hormozi (résultat rêvé, probabilité perçue, délai, effort, pile de valeur, garantie, rareté vraie) et l'échelle d'offres du gratuit au premium, avec les offres uniques automatiques. Utiliser quand l'utilisateur dit « construis mon offre », « mon offre ne se vend pas », « quels prix », « échelle d'offres », « upsell », « offre irrésistible ». Pas pour le script de l'appel (utiliser appel-de-vente) ni pour la page de paiement technique (utiliser crm-et-messages)."
---
# Offre et échelle d'offres

## Pourquoi
Une bonne offre se vend presque seule, une offre floue épuise. Dans le système d'origine, le business avait déjà vendu avec une offre unique haut de gamme. La relance a ajouté une échelle : une porte gratuite, un petit abonnement, une offre du milieu, un accompagnement premium, et à chaque moment de décision une offre spéciale vraiment unique. Deux leçons ont compté : chaque tactique de persuasion se garde dans sa version vraie, et le faux (fausse date, fausse rareté, faux témoignage) est rejeté sans débat.

## Prérequis
- `entretien-fondateur` (offres passées, preuves, client idéal).
- Bloc C conseillé : notebook d'un expert en offres (par exemple les livres d'Alex Hormozi, comme option) pour faire valider chaque choix, et le skill `offers` s'il est installé.

## Interview
**Lis d'abord** : `wiki/business/offres.md`, `preuves.md`, `client-ideal.md` (ses désirs, ses objections), `objections.md` si `appels-analyse` a tourné, `chiffres.md` (prix passés et volumes).

Puis demande :
1. Quel est le résultat que ton client veut vraiment, dit avec ses mots ?
2. Qu'est-ce qui le fait douter que ça marche pour lui ?
3. Combien de temps avant un premier résultat visible ? Et le résultat complet ?
4. Qu'est-ce qui lui demande le plus d'effort aujourd'hui, que ton offre peut lui enlever ?
5. Quelle limite réelle as-tu ? (Places, heures, dates de session.)
6. Quelle garantie peux-tu tenir sans te mettre en danger ?
7. Quels prix as-tu déjà pratiqués, et à combien de personnes ?
8. Veux-tu vendre vite à bas prix puis monter, ou tenir un prix haut dès le départ ?

## Construire
1. **L'équation de valeur (ensemble, 20 min).** Écris dans `wiki/business/offre-principale.md` quatre blocs : résultat rêvé (ses mots), preuves qu'il peut y arriver (tes preuves réelles), délai (premier résultat et résultat complet), effort enlevé. Chaque bloc trace vers une source du vault.
2. **Problèmes vers solutions (Claude, 20 min).** Liste chaque obstacle que le client rencontre avant, pendant et après (cherche dans `objections.md` et `client-ideal.md`). Pour chacun, une solution concrète de l'offre (module, séance, modèle, accès). Ce tableau devient la pile de valeur.
3. **Pile, prix, garantie (ensemble, 20 min).** Range les solutions en pile avec une valeur estimée raisonnable pour chacune. Pose le prix. Choisis la garantie de la réponse 6 et écris ses conditions exactes. Nomme l'offre avec le résultat dedans.
4. **Rareté et urgence vraies (Claude, 10 min).** Seulement ce qui est réel : places limitées par ton temps, date de début d'une session, prix de lancement pour un nombre précis de personnes, bonus qui disparaît à une date tenue. Écris la règle dans `offre-principale.md` : « jamais de compte à rebours qui repart, jamais de prix barré inventé, jamais de preuve empruntée ».
5. **L'échelle (ensemble, 20 min).** Dans `wiki/business/echelle-offres.md`, un tableau : porte gratuite (communauté, guide, quiz), petit prix récurrent, offre du milieu, premium. Pour chaque marche : prix, ce qu'elle contient, à qui elle s'adresse, la marche suivante, et où on la montre (partout, ou seulement en coulisse après un non au prix).
6. **Offres uniques automatiques (Claude, 20 min).** À chaque moment de décision (ajout au panier, page de remerciement, fin d'essai, résiliation, nouveau membre), une offre forte qui s'affiche une seule fois dans la vie du contact. La rareté est réelle : étiquette posée dans le CRM, date, code unique, refus poli si la personne la redemande. Liste-les dans `echelle-offres.md`, section « Offres uniques ». Le branchement technique se fait dans `crm-et-messages`.
7. **Validation (Claude, 10 min).** Pose chaque choix de prix et de tactique au notebook expert du bloc C : « est-ce que ça marche, et l'expert l'utilise-t-il ? ». Garde le mécanisme dans sa version vraie, rejette le faux. Note la réponse sourcée sous chaque choix. Montre le résultat à l'utilisateur.
8. **Passer au board (Claude, 5 min).** Tout texte d'offre qui sera lu par le client passe par le board des textes du bloc C avant publication.

## Test
`offre-principale.md` a les quatre blocs sourcés, une pile, un prix, une garantie écrite et une règle de rareté vraie, et l'utilisateur dit l'offre en une phrase à voix haute sans regarder l'écran.

## Pièges vécus
- **Tout rejeter par prudence.** Sur une vingtaine de tactiques d'une formation marketing, Claude les avait toutes jugées trop agressives. Revues par le board, la plupart sont restées dans leur version honnête. Seul le faux est sorti.
- **Les faux témoignages.** Un site affichait des témoignages et des chiffres que personne ne pouvait prouver, et des agents automatiques les ont recopiés ailleurs. Purge tout ce qui n'est pas vrai avant de faire de la pub.
- **La peur comme levier.** Jouer sur la peur la plus profonde du client (perdre ce qu'il aime) vend parfois à court terme et détruit la confiance. Écris-la comme ligne rouge.
- **Redemander chaque prix à l'utilisateur.** Il voulait que les prix des offres automatiques soient tranchés avec le board, puis montrés. Demande-lui une fois sa préférence, ensuite applique-la.

## Entretien dans le temps
- Après chaque série de 5 appels de vente, relis les objections et ajoute une solution à la pile si une objection revient.
- Une fois par trimestre, revue des prix et de l'échelle avec les chiffres de ventes réels.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, la mémoire (préférence prix bas ou haut). Propose ensuite `appel-de-vente`.
