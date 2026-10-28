---
name: banque-idees
description: "Construit la banque d'idées de contenu tirée des vraies questions des clients (appels, commentaires, messages, formulaires). Utiliser quand l'utilisateur dit « je ne sais pas quoi poster », « fais ma banque d'idées », « range cette question », « on parle de quoi cette semaine ». Pas pour la veille des concurrents ou des tendances (utiliser veille-et-tendances)."
---
# Banque d'idées

## Pourquoi
Dans le système d'origine, les sujets choisis au hasard faisaient peu de vues, et la recherche n'amenait presque personne. Les meilleurs contenus venaient tous d'une phrase réelle d'un client : un mot dit en appel, un commentaire, un message privé. La banque garde ces phrases mot à mot, compte celles qui reviennent et sort chaque semaine le sujet le plus demandé. On arrête de chercher ses idées : on les ramasse là où elles arrivent déjà.

## Prérequis
- Bloc A : le vault et l'ingestion (appels, messages, réseaux), pour que les questions arrivent seules.
- Bloc D : la fiche client idéal (ses mots, ses situations) et l'offre.
- Bloc C : le carnet expert du domaine, pour vérifier le fond.
- Aucun coût.

## Interview
Lis d'abord : `wiki/maps/moi.md`, la fiche client idéal du bloc D, les dernières transcriptions d'appels, les notes clients, `wiki/maps/banque-idees.md` s'il existe. Puis demande, une question à la fois :
1. « Où tes clients te posent-ils des questions ? » (appels, commentaires, messages, email, formulaire, groupe). Range la liste dans la banque, section « Sources ».
2. « Quelle question entends-tu le plus souvent en ce moment ? Dis-la avec ses mots à lui. » Elle devient la première ligne.
3. « Y a-t-il des sujets que tu ne veux jamais traiter ? » Range dans la section « Interdits ».
4. « Combien de contenus longs par semaine peux-tu vraiment tenir, même une mauvaise semaine ? » Range dans `wiki/maps/machine-contenu.md`, section « Cadence ». Pose un plancher tenable plutôt qu'un objectif héroïque.

## Construire
1. **Créer la banque** (Claude, 5 min). Écris `wiki/maps/banque-idees.md` avec ce tableau :
   ```
   | id | Question mot à mot | Source (chemin) | Fois entendue | Situation précise | Statut | Pièces faites |
   ```
   Statuts : `idée`, `vérifiée` (le fond est juste), `choisie`, `faite`, `écartée`. La colonne « Question mot à mot » ne se paraphrase jamais. Crée aussi `wiki/maps/machine-contenu.md` (hub du bloc E : cadence, réseaux, chaîne, liens vers chaque brique) s'il n'existe pas.
2. **Remplir depuis le vault** (Claude, 20 min). Cherche par le sens (skill `recherche-par-le-sens` du bloc A) dans les transcriptions et les messages : les phrases qui commencent par « comment », « pourquoi », « est-ce que », « il/elle me dit », « j'ai peur ». Une ligne par question, avec le chemin de la note. Deux questions qui veulent dire la même chose fusionnent et leur compteur monte.
3. **Brancher l'arrivée continue** (Claude, 15 min). Ajoute une étape à l'ingestion du bloc A : chaque nouvel appel ou message passe par la recherche de questions et alimente la banque. Vérifie que la commande courte `.claude/commands/idee.md` existe (« note cette idée : … » ajoute une ligne) ; sinon crée-la.
4. **Le choix de la semaine** (Claude, 10 min). Trie par « Fois entendue », puis par fraîcheur. Propose les deux premières à l'utilisateur avec la question mot à mot et la situation. Il dit oui ou en change une.
5. **Vérifier le fond** (Claude, 10 min). Avant qu'une idée passe `vérifiée`, pose la réponse prévue au carnet expert du domaine (bloc C). Une affirmation catégorique sans source reste en `idée`.

## Test
La banque contient au moins 20 questions réelles, chacune avec un chemin de source qui existe dans le vault, et le sujet de la semaine sort en une demande.

## Pièges vécus
- Des idées inventées par l'IA à partir d'un mot-clé : elles sonnaient juste et ne touchaient personne. Sans chemin de source, une idée n'entre pas.
- Le même principe donné dans plusieurs vidéos d'affilée : tiens la colonne « Pièces faites » à jour et relis-la avant de choisir.
- Un questionnaire automatique envoyé chaque semaine à l'entrepreneur pour nourrir les articles : personne n'y répondait, il a été coupé. Ramasse les questions là où elles tombent déjà.

## Entretien dans le temps
Le jardinier (bloc A) signale chaque semaine les lignes sans source et les doublons. Chaque contenu publié remplit « Pièces faites ». Une idée `écartée` garde sa raison en une ligne, pour ne pas la reproposer.

## Après
Mets à jour `wiki/maps/parcours.md` (brique faite), ajoute une ligne à `log.md`, note en mémoire les sujets interdits s'il en a donné. Propose ensuite `veille-et-tendances`.
