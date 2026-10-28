---
name: pubs-apres-tunnel
description: "Prépare puis lance les pubs payantes seulement quand le tunnel complet est prouvé : verrou d'entrée, structure de compte simple, événement optimisé, créas par concepts, règles de lecture et plafond de perte fixé par l'utilisateur. Utiliser quand l'utilisateur dit « je veux faire de la pub », « lance une campagne », « mes pubs ne marchent pas », « budget pub ». Pas pour le contenu organique (bloc E) ni pour le tunnel (utiliser tunnel-et-quiz)."
---
# Pubs, seulement après le tunnel

## Pourquoi
Les pubs amènent des inconnus. Si le tunnel les perd, chaque euro dépensé paie pour perdre des gens. Dans le système d'origine, le business avait déjà vécu des pubs qui marchaient puis s'étaient éteintes après un changement de l'algorithme de la plateforme. À la relance, la décision a été claire : d'abord la machine à contenu, puis l'aimant et les emails, puis la vente et l'accueil client, et les pubs en dernier. Pendant ce temps, Claude s'est formé (meilleures pubs de la niche, structure de compte, plan de test) sans dépenser un euro.

## Prérequis
- `tunnel-et-quiz` avec un test de bout en bout vert. C'est le verrou.
- Un compte publicitaire (Meta, Google, TikTok, au choix), un moyen de paiement que l'utilisateur ajoute lui-même.
- Le suivi des conversions : pixel ou balise de la plateforme, idéalement aussi l'API de conversions côté serveur.
- Bloc C conseillé : notebooks d'experts en pubs de ton choix, pour valider chaque règle.

## Interview
**Lis d'abord** : `wiki/strategie/tunnel.md` (le test est-il vert ?), `wiki/strategie/plan.md`, `chiffres.md` (prix, taux de signature en appel), `echelle-offres.md`, toute trace de pubs passées dans `raw/`.

Puis demande :
1. As-tu déjà fait de la pub ? Qu'est-ce qui a marché, et quand ça s'est arrêté ?
2. Combien peux-tu dépenser par jour pendant un mois de test, sans mettre ton business en danger ?
3. Quelle perte maximale acceptes-tu sur ce test avant de couper ? (C'est ta décision, Claude ne la prend jamais.)
4. Combien te rapporte un client en moyenne sur ses premiers 30 jours ?
5. Quelles vidéos ou quels posts organiques ont le mieux marché ?

Range dans `wiki/maps/pubs.md`.

## Construire
1. **Vérifier le verrou (Claude, 5 min).** Lis `tunnel.md`. Si le test de bout en bout n'est pas vert, arrête-toi ici : dis-le en une phrase et propose `tunnel-et-quiz`. Vérifie aussi que toutes les preuves affichées sont vraies : un témoignage ou un chiffre non prouvé se retire avant la première pub.
2. **Formation sans dépense (Claude, 20 min par passe).** Étudie la bibliothèque publique des pubs de la plateforme (pour Meta : la Bibliothèque publicitaire) sur ta niche : les pubs actives depuis longtemps sont celles qui rapportent. Note les formats, les angles, les accroches dans `outputs/pubs/etude-niche.md`. Vérifie les règles de la plateforme sur ton sujet (attributs personnels, santé, finance) dans sa page officielle.
3. **Suivi des conversions (utilisateur guidé, 20 min).** Installe le pixel ou la balise sur les pages du tunnel. Déclare l'événement qui compte : questionnaire ou quiz terminé tant que les rendez-vous sont rares, puis rendez-vous pris. Jamais le clic ni la visite : la plateforme livre exactement ce que tu lui demandes. Teste avec l'outil de test d'événements de la plateforme.
4. **Structure simple (Claude, 15 min).** Une campagne, un ensemble de pubs à large audience, quelques pubs. Écris le plan dans `outputs/pubs/plan-test.md` : budget par jour (réponse 2), durée, événement, règle de coupe, plafond de perte (réponse 3).
5. **Créas par concepts (Claude, 20 min par lot).** Une majorité de concepts neufs (un concept change le format, l'angle ou la croyance visée) et une minorité de variantes des gagnants. Pars des contenus organiques qui ont marché. Chaque texte passe par le board. Ne mélange pas images et vidéos dans le même ensemble.
6. **Lancer (utilisateur, 10 min).** L'utilisateur ajoute son moyen de paiement et appuie sur publier. Claude ne dépense jamais et ne valide jamais un paiement.
7. **Lire (Claude, 10 min par semaine).** Ne touche à rien pendant 7 jours. Un changement à la fois. Juge au cash encaissé (CRM et paiements) rapporté à la dépense, jamais au seul retour affiché par la plateforme. Coupe dès que le plafond de perte est atteint. Écris chaque lecture dans `wiki/maps/pubs.md`.

## Test
Le verrou est vert, l'événement de conversion remonte dans l'outil de test de la plateforme, et après 30 jours `pubs.md` contient le coût par rendez-vous et le cash encaissé, comparés au plafond de perte décidé par l'utilisateur.

## Pièges vécus
- **Payer pour perdre des gens.** Sans emails automatiques, sans paiement et accès automatiques, les prospects payés se perdent. Le verrou vient avant tout le reste.
- **Les anciennes gagnantes mortes.** Des pubs qui ont marché pendant longtemps peuvent s'éteindre après un changement de l'algorithme. Relance avec des concepts neufs.
- **Optimiser pour le clic.** La plateforme a livré des clics bon marché qui ne prenaient jamais rendez-vous. Optimise pour l'étape qui précède l'argent.
- **Juger au chiffre de la plateforme.** Le retour affiché par le compte pub surestime souvent. Le cash réel fait foi.
- **Les faux témoignages.** Une pub qui renvoie vers une page aux preuves inventées expose à la loi et à la plateforme. Purge avant de lancer.

## Entretien dans le temps
- Chaque semaine : lecture (étape 7), un seul changement.
- Chaque mois : un nouveau lot de concepts.
- Le plafond de perte et le budget se revoient seulement avec l'utilisateur.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, le plan (étape « pubs »), la mémoire (budget et plafond décidés, avec la date). Le bloc D est fini : propose le bloc E (machine à contenu) s'il n'est pas installé, ou le bloc F.
