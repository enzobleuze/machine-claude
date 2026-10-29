---
title: "Bloc D : Business"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc D : Business

Ce bloc transforme ce que l'utilisateur sait de son activité en un business piloté : un plan unique, des fiches clients, des appels analysés, une offre claire, un tunnel qui marche seul, et un Cockpit qui dit chaque matin quoi faire. Les pubs arrivent en dernier, seulement quand le tunnel est prouvé.

## Avant de commencer
- Bloc A installé (vault, mémoire, zones privées, secrets hors du vault).
- Bloc B conseillé (hooks, pour la ligne de situation en début de conversation).
- Bloc C conseillé (board des textes, agent client idéal, notebooks d'experts). Sans lui, les skills marchent, mais les textes au client passent seulement par la relecture voix.

## Ordre et dépendances

| # | Skill | Dépend de | Temps de l'utilisateur | Test binaire |
|-|-|-|-|-|
| 1 | `entretien-fondateur` | bloc A | 4 séances de 20 min | Les 18 cases de `wiki/business/_entretien.md` sont cochées ou « à vérifier » |
| 1b | `dossier-client-ideal` | 1, bloc A | 4 à 6 séances de 20 min (Claude extrait, l'utilisateur valide) | `verifier-dossier.py` sort 0 et l'utilisateur reconnaît ses clients dans le niveau 3 |
| 2 | `voix-personnelle` | 1 | 20 min + test à l'aveugle | L'utilisateur ne reconnaît pas 2 réponses de Claude sur 3 |
| 3 | `plan-unique` | 1 | 20 min, puis 15 min chaque lundi | `cockpit_build.py ligne` cite la vraie prochaine tâche |
| 4 | `regle-des-4-pourcent` | 1, 3 | 20 min | Aucune case de l'utilisateur hors de ses 3 activités ni sans durée |
| 5 | `fiches-clients` | bloc A, 1 | 10 min + complétion par lots | Aucune « Fiche illisible » au build, Claude répond « où en est X ? » depuis la fiche |
| 6 | `appels-analyse` | 5 | 15 min de branchement | Un appel analysé, chaque citation retrouvée mot pour mot |
| 7 | `repondre-client` | 2, 5 | 2 min par message | 3 réponses jugées « je l'aurais envoyée » |
| 8 | `offre-et-echelle` | 1 (6 conseillé) | 3 séances de 20 min | L'utilisateur dit son offre en une phrase sans écran |
| 9 | `appel-de-vente` | 5, 6, 8 | 20 min pour le script | Préparation avant, débrief après, vente notée au compteur |
| 9b | `charte-graphique` | bloc A (1 conseillé) | 10 à 20 min, plus le choix sur l'aperçu | `charte.py valider` sort 0 et l'utilisateur a dit oui sur l'aperçu |
| 10 | `cockpit-app` | 3, 5 (9b conseillé) | 5 min | `test_cockpit.py` OK, raccourci bureau, lecture en 5 secondes |
| 11 | `crm-et-messages` | 5, 7 | 10 min pour la clé | `crm_lire.py` liste les vraies conversations du jour |
| 12 | `email-liste` | 2, 8 (11 conseillé) | 20 min de réglage du domaine | Le contact de test reçoit tout et sort au faux rendez-vous |
| 13 | `tunnel-et-quiz` | 8, 11, 12 | 2 séances de 20 min | Le faux prospect va du commentaire à l'accès sans geste humain |
| 14 | `pubs-apres-tunnel` | 13 vert | 20 min + décision du budget | Événement de conversion vu, lecture à 30 jours au cash réel |

La charte (9b) peut se faire à tout moment après le bloc A ; le Cockpit, les carrousels et les vidéos la lisent, et prennent la charte « simple » tant qu'elle manque. Le Cockpit (10) peut s'installer plus tôt, juste après le plan (3) : il marche sans fiches ni ventes et affiche « inconnu ». Le script `cockpit_build.py` sert aussi seul, pour la ligne de situation et pour noter les ventes.

## Ce qui passe en parallèle
Dès l'étape 7, chaque personne qui écrit reçoit une réponse le jour même, et chaque appel est préparé puis débriefé (étape 9). Ces deux gestes n'attendent pas la fin du bloc.

## Fichiers produits dans le vault de l'utilisateur
- `wiki/business/` : `fondateur.md`, `client-ideal.md` (le dossier complet), `precision-emotionnelle.md`, `pensees-client/` (un fichier par situation), `offres.md`, `preuves.md`, `chiffres.md` (privé), `offre-principale.md`, `echelle-offres.md`, `objections.md`
- `wiki/maps/` : `banque-experience.md` (partagée avec `ingestion-appels`), `voix.md`, `regle-4-pourcent.md`, `cockpit.md`, `crm.md`, `mots-cles.md`, `email.md`, `pubs.md`
- `wiki/strategie/` : `plan.md`, `tunnel.md`
- `wiki/clients/` (privé), `wiki/appels/`, `wiki/scripts/script-appel.md`, `wiki/scripts/objections-reponses.md`
- `scripts/cockpit/` (Cockpit), `scripts/voix_lint.py`, `scripts/voix_mesure.py`, `scripts/crm_lire.py`
- `outputs/cockpit/state.json` et `outputs/cockpit/ventes.jsonl`
- `bibliotheque/marque/` : `charte.json` (le choix), `charte.css` et `charte-jetons.json` (générés), le logo, `propositions/` ; `wiki/business/charte.md` ; `scripts/charte.py`

## Outils joints au repo
- `.claude/skills/dossier-client-ideal/outils/` : gabarits de la fiche, de la précision émotionnelle et des pensées par situation, un exemple rempli (métier inventé), les questions pour les carnets, `verifier-dossier.py` (`--test`).
- `.claude/skills/plan-unique/outils/plan.modele.md` : modèle du plan (bloc lisible par script + semaine + feuille de route avec PROCHAINE).
- `.claude/skills/fiches-clients/outils/fiche-client.modele.md` : modèle de fiche client.
- `.claude/skills/charte-graphique/outils/charte.py` : `valider`, `construire` (écrit `charte.css` et `charte-jetons.json`), `apercu`, `proposer` (quatre chartes prêtes plus une sur mesure, sur une page d'aperçu), `--test`. Déduit surfaces, lignes, thème inverse et couleurs d'état, et garantit les contrastes. Bibliothèque standard seulement.
- `.claude/skills/cockpit-app/outils/` : `cockpit_build.py` (moteur : construit `state.json` ; `vente M QUI --offre X`, `idee T`, `ligne`, `dossier ID`, `--check`), `cockpit_sources.py` (sources : Linear par clé ou `taches.md`, agenda iCal, échelle d'offres, réseaux, tournage, appel ; importé par le moteur), `cockpit_serveur.py` (serveur local sur 127.0.0.1 et écritures ; `--demo`, `--port N`, `--no-open`), `index.html` (écrans Aujourd'hui, Clients, Appel, Échelle, Agenda, Réseaux, Tournage, Plan ; clair et sombre aux couleurs de la charte), `cockpit_demo.py` (faux vault de démonstration), `charte-simple.css` (charte de secours), `test_cockpit.py` (tests hors ligne), `lancer-cockpit.bat` et `lancer-cockpit.command` (raccourcis). Python 3.8 ou plus, bibliothèque standard seulement.

## Tests du bloc
1. `python -X utf8 .claude/skills/cockpit-app/outils/test_cockpit.py` sort `OK` (faux vault temporaire, build, ventes, serveur, lecture du modèle de plan).
2. `python -X utf8 .claude/skills/cockpit-app/outils/cockpit_build.py --check` sort `contrôles OK`.
2b. `python -X utf8 .claude/skills/charte-graphique/outils/charte.py --test` sort `AUTO-TEST OK`.
3. Dans le vault de l'utilisateur, après l'étape 10 : une nouvelle conversation commence par la ligne de situation, et la page du Cockpit s'ouvre depuis le raccourci bureau.
4. À la fin du bloc : le test de bout en bout du tunnel (étape 13) est vert dans `wiki/strategie/tunnel.md`.

## Mise à jour du parcours
Après chaque skill, coche la ligne correspondante dans `wiki/maps/parcours.md` avec la date et le résultat du test.


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
