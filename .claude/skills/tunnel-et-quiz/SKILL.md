---
name: tunnel-et-quiz
description: "Construit le tunnel complet, de l'aimant (un quiz de situation, un guide ou une vidéo) jusqu'à l'accès client, avec la carte des portes, les pages, les étiquettes, le paiement, le contrat et un test de bout en bout avec un faux prospect. Utiliser quand l'utilisateur dit « fais mon quiz », « mon tunnel », « aimant à prospects », « page de capture », « parcours du prospect », « teste mon tunnel ». Pas pour les pubs (utiliser pubs-apres-tunnel)."
---
# Tunnel et quiz

## Pourquoi
Un inconnu qui découvre ton contenu doit trouver un chemin clair jusqu'à l'achat, et chaque étape doit marcher sans toi. Dans le système d'origine, le choix de l'aimant a été pesé longtemps entre un webinaire et un quiz. Le gagnant a été un quiz de situation : la personne choisit ce qu'elle vit et ce qu'elle fait en réponse, et reçoit un diagnostic, un guide et une courte vidéo. Tous les mots-clés en commentaire y mènent. La preuve que le tunnel est fini est un test de bout en bout avec un faux prospect, du commentaire jusqu'à l'accès au programme.

## Prérequis
- `offre-et-echelle`, `crm-et-messages`, `email-liste`.
- Un outil de quiz et de pages : celui du CRM (GoHighLevel a un constructeur de quiz), ou un outil dédié (Tally, Typeform, ScoreApp), ou une page HTML hébergée (GitHub Pages par exemple, gratuit). Un outil de paiement (Stripe ou celui du CRM) et de signature de contrat.

## Interview
**Lis d'abord** : `client-ideal.md` (situations fréquentes, mots exacts), `echelle-offres.md`, `wiki/maps/mots-cles.md`, `wiki/maps/email.md`, tout tunnel existant (cherche « quiz », « landing », « page » dans `wiki/` et `raw/`).

Puis demande :
1. Quelles sont les 4 à 6 situations que vivent tes clients quand ils te trouvent ? (Dans leurs mots.)
2. Pour chaque situation, qu'est-ce qu'ils font souvent en réponse, qui aggrave les choses ?
3. Que veux-tu offrir à la fin : un diagnostic, un guide, une vidéo, une invitation à un appel ?
4. Quelle est la porte d'entrée des prospects aujourd'hui ? (Réseaux, site, bouche à oreille.)
5. Comment un client paie-t-il, signe-t-il, accède-t-il au programme aujourd'hui ? Qu'est-ce qui est encore à la main ?

## Construire
1. **Carte des portes (Claude, 15 min).** `wiki/strategie/tunnel.md` : chaque porte d'entrée (vidéo, mot-clé, page du site, recommandation), l'aimant, la page de résultat, la séquence email, l'appel, le paiement, le contrat, l'accès, la communauté. Une flèche par passage, avec l'étiquette CRM posée à chaque étape (`source-…`, `aimant-…`, `rdv-pris`, `client-…`).
2. **Questions du quiz (ensemble, 20 min).** Six à dix questions courtes. Les premières : sa situation, choisie parmi les réponses 1. Puis ce qu'il fait en réponse (réponses 2). Puis deux ou trois questions de qualification (urgence, budget, disponibilité) en fin de quiz. Chaque profil de résultat a un nom simple et vient d'une combinaison réelle.
3. **Page de résultat (Claude, 20 min par profil).** Diagnostic en ses mots, ce qui se passe vraiment, la première action à faire ce soir, le guide en cadeau, une courte vidéo de l'utilisateur, l'invitation vers la marche suivante. Passe chaque texte au board.
4. **Construire dans l'outil (Claude et utilisateur, 20 min par bloc).** Questions, logique des profils, capture email, étiquettes. Si l'outil n'a pas d'API, Claude écrit les textes et la logique dans un fichier, et guide l'utilisateur écran par écran. Les textes du quiz vivent dans un seul fichier du vault (`outputs/quiz/quiz.json` ou `.md`) : on change le fichier, puis l'outil.
5. **Brancher les mots-clés (Claude, 10 min).** Chaque mot-clé de douleur de `mots-cles.md` mène au quiz avec la bonne situation présélectionnée quand l'outil le permet. Mets à jour le tableau.
6. **Après le oui (ensemble, 20 min par élément).** Paiement, contrat signé, accès au programme, entrée dans la communauté, message de bienvenue client. Chaque élément se déclenche seul après le paiement. Ce qui reste à la main est écrit dans `tunnel.md`, section « encore manuel », avec son temps.
7. **Test de bout en bout (Claude et utilisateur, 20 min).** Un faux prospect (adresse de test, compte de test sur le réseau) passe tout : commentaire, DM, quiz, email, rendez-vous, paiement en mode test, contrat, accès. Note chaque étape « OK » ou « cassé » dans `tunnel.md`. Corrige et relance jusqu'à tout « OK ».

## Test
Le faux prospect va du commentaire jusqu'à l'accès au programme sans aucun geste de l'utilisateur, et chaque étiquette attendue est posée sur sa fiche CRM.

## Pièges vécus
- **Un aimant qui ne parle pas de sa situation.** Un quiz « quel est ton profil ? » général attirait moins qu'un quiz qui part de ce que la personne vit ce soir. Pars des situations réelles.
- **Le mauvais aimant envoyé.** Un agent IA du CRM a envoyé le webinaire à une personne à qui on avait promis le diagnostic du quiz. Chaque mot-clé et chaque agent doivent pointer vers la même ressource que la promesse.
- **Le tunnel à moitié fini.** Payer pour amener du monde vers un tunnel qui perd les gens après l'email 1 coûte cher. Le test de bout en bout est le verrou avant toute pub.
- **Les textes éparpillés.** Les textes modifiés directement dans l'outil se perdaient. Un seul fichier source dans le vault.

## Entretien dans le temps
- Chaque mois : taux de fin du quiz, taux d'email capté, rendez-vous pris par profil.
- Après tout changement dans l'outil : refaire le test de bout en bout.
- Quand un profil convertit mal, réécris sa page de résultat (une à la fois).

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`, le plan (l'étape « tunnel » cochée si le test passe). Propose ensuite `pubs-apres-tunnel`, seulement si le test de bout en bout est vert.
