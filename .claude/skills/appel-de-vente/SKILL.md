---
name: appel-de-vente
description: "Tout le cycle de vente autour d'un appel : script d'appel avec objections, préparation de 10 minutes, débrief après l'appel, relances des non-acheteurs et des absents, et vente notée dans le compteur du mois. Utiliser quand l'utilisateur dit « j'ai un appel dans 10 minutes », « prépare mon appel avec X », « débrief mon appel », « relance X », « j'ai vendu », « écris mon script d'appel ». Pas pour l'analyse de fond des appels (utiliser appels-analyse) ni pour l'offre elle-même (utiliser offre-et-echelle)."
---
# Appel de vente : script, préparation, débrief, relance

## Pourquoi
Le chiffre d'affaires d'un service se fait en appel. Dans le système d'origine, plus d'une centaine d'appels réels ont été minés pour en tirer les objections comptées et les règles du script. Ensuite, chaque appel a eu sa page de préparation lisible en deux minutes, son débrief technique, et sa relance du plus chaud au plus froid. Une vente qui n'est pas notée n'existe pas pour le plan : la commande `vente` la met dans le compteur du mois.

## Prérequis
- `offre-et-echelle`, `fiches-clients`, `appels-analyse` (pour `objections.md`).
- `cockpit-app` pour noter les ventes (le script `cockpit_build.py` suffit, même sans le serveur).
- Bloc C : board des textes pour les relances.

## Interview
**Lis d'abord** : `wiki/business/offre-principale.md`, `echelle-offres.md`, `objections.md`, `client-ideal.md`, les analyses dans `wiki/appels/`, tout script existant (cherche « script » dans `wiki/` et `raw/`).

Puis demande, la première fois :
1. Comment se passe un appel aujourd'hui, du bonjour au prix ? Raconte le dernier que tu as signé.
2. Quel est ton taux de présence aux rendez-vous, à peu près ? Que fais-tu avec les absents ?
3. Comment prends-tu le paiement ? (Lien pendant l'appel, facture, virement.)
4. Si la personne dit non au prix, que lui proposes-tu ? (La marche du dessous de l'échelle, ou rien.)
5. Comment veux-tu relancer : message, email, vocal ? Combien de fois au plus ?

## Construire
1. **Script d'appel (ensemble, 20 min).** Écris `wiki/scripts/script-appel.md` en phases avec une ancre par phase (`%% #accueil %%`, `%% #situation %%`, `%% #douleur %%`, `%% #vision %%`, `%% #ecart %%`, `%% #offre %%`, `%% #prix %%`, `%% #objections %%`, `%% #paiement %%`). Chaque phase a ses questions exactes et ce qu'on cherche à entendre. Les phrases viennent de ses appels signés, pas d'un modèle générique.
2. **Réponses aux objections (Claude, 15 min).** Dans `wiki/scripts/objections-reponses.md`, une section par objection de `objections.md`, dans l'ordre de fréquence, avec la réponse qui a fermé dans un vrai appel et la phase où revenir après (`retour : #ecart`).
3. **Préparation, avant chaque appel (Claude, 5 min).** Quand l'utilisateur dit « j'ai un appel avec X » : lis sa fiche, son questionnaire, ses messages. Rends une page `outputs/appels/prep-<date>-<prenom>.md` lisible en deux minutes : situation en 3 lignes avec ses mots, ce qu'il veut, l'objection la plus probable et sa réponse, la marche de l'échelle qui lui va, une question d'ouverture personnelle. Pas d'invention : ce qui n'est pas dans le dossier est marqué « à demander ».
4. **Débrief, après l'appel (Claude, 15 min).** Lance d'abord `appels-analyse` sur l'enregistrement. Ajoute la grille technique : temps de parole, silences après le prix, reformulations, faux oui (« ça a l'air bien » sans engagement), moment où le prix est tombé, paiement proposé pendant l'appel ou reporté, objection non traitée. Rends trois choses qui ont marché et une seule à changer au prochain appel. Écris sous l'analyse de l'appel.
5. **Relances (Claude, 10 min par lot).** Classe les non-acheteurs : absent, « je réfléchis », prix, autre. Pour chacun, un message dans sa voix, du plus chaud au plus froid, avec une raison vraie de répondre (une ressource, une question, une place qui se libère). Passe chaque texte au board. Dépose en brouillon dans le CRM ou montre-le pour envoi manuel. Absents : un message le jour même, un autre deux jours plus tard, puis la fiche passe en `prochain_pas: relance dans 30 jours`.
6. **Noter la vente (Claude, 1 min).** Quand l'utilisateur dit « j'ai vendu 1 500 à X » ou « X a payé », lance :
   ```
   python scripts/cockpit/cockpit_build.py vente 1500 "Prénom Nom"
   ```
   Note chaque paiement reçu au moment où il arrive (un paiement en trois fois = trois lignes, à leur date). Mets à jour la fiche (type client, offre, paiements) et l'objectif « ventes » du trimestre dans `plan.md`.

## Test
Pour un vrai appel : la page de préparation existe avant l'appel, le débrief nomme une seule chose à changer, et après la vente `cockpit_build.py ligne` affiche le nouvel encaissé du mois.

## Pièges vécus
- **Le script générique.** Les phrases d'un livre de vente sonnaient faux dans la bouche du fondateur. Les phrases qui marchent viennent de ses appels signés.
- **Enchaîner sur le prix trop tôt.** L'analyse des appels perdus a souvent trouvé le même moment de bascule : le client doutait encore, et le prix arrivait quand même. Le script revient à la phase d'écart avant le prix.
- **Le faux oui.** « Ça a l'air super » n'est pas un oui. Demande l'engagement concret.
- **La relance qui supplie.** Une relance sans raison vraie de répondre abîme la dignité du vendeur. Chaque relance apporte quelque chose.
- **Les ventes oubliées.** Le compteur du mois montrait zéro alors que des paiements étaient arrivés. Note chaque paiement le jour même.

## Entretien dans le temps
- Chaque appel : préparation puis débrief.
- Chaque mois : la réponse aux objections qui ferme le plus remonte en premier dans `objections-reponses.md`.
- Le Cockpit montre l'argent du mois contre la cible.

## Après
Mets à jour `wiki/maps/parcours.md`, `log.md`. Propose ensuite `cockpit-app` s'il n'est pas installé, sinon `crm-et-messages`.
