---
title: "Bloc A : Cerveau"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc A : le Cerveau

Le bloc A donne à Claude une mémoire fiable et un savoir rangé : un vault où rien ne se perd, une mémoire relue à chaque conversation, une recherche qui trouve par le sens, des sources qui entrent toutes seules, un entretien de nuit, des sauvegardes. Tout le reste du repo s'appuie dessus.

Règle de passage : une brique est cochée dans `wiki/maps/parcours.md` seulement quand son test binaire passe. Chaque skill commence par son interview.

## Ordre d'installation

| # | Skill | Dépend de | Test qui prouve que c'est fait |
|:-|:-|:-|:-|
| 1 | `architecture-vault` | rien | `python scripts/creer-vault.py . --essai` affiche « Créés : 0 » |
| 2 | `securite-git-secrets` | 1 | `python scripts/sauvegarde-git.py --verif` sort 0, dépôt « Private » sur GitHub, le hook bloque `rm -rf` (code 2) |
| 3 | `memoire-fichiers` | 1 | `python scripts/memoire-check.py` sort « OK », et une conversation neuve cite les préférences sans ouvrir de fichier |
| 4 | `bibliothecaire-installer` | 1, 3 | une question métier reçoit une réponse qui cite la bonne note par son chemin |
| 5 | `recherche-par-le-sens` | 4 | `python scripts/cerveau-check.py` : tous les tests d'or passent en mode sens |
| 6 | `ingestion-fichiers` | 1, 3, 4 | après un `/ingest`, `raw-nouveaux.py` affiche 0 et aucun lien mort neuf |
| 7 | `lint-wiki` | 1 | `python scripts/lint_wiki.py --strict` sort 0 après `/lint` |
| 8 | `jardinier` | 2, 7 | une nuit en écriture : résumé daté, commit « jardinier: entretien », zéro frontmatter incomplet |
| 9 | `fin-de-session` | 3, 7 | après `/fin` : entrée du jour dans `log.md`, leçon en mémoire, commit de session |
| 10 | `sauvegardes-3-lieux` | 2 | marqueur Drive de moins de 24 h, aucun `.env` dans le miroir, restauration d'essai réussie |

## Sources à brancher ensuite (selon l'interview, dans l'ordre de ce qu'il utilise le plus)

| Skill | Dépend de | Test |
|:-|:-|:-|
| `ingestion-drive` | 2, 6 | le Dépôt est vide après tri, chaque déplacement est dans `outputs/ingest-drive/journal.csv`, aucun fichier disparu |
| `ingestion-notion` | 2, 6 | deux passages de suite : le second écrit 0 page |
| `ingestion-appels` | 2, 6 | relance sans nouvel appel, banque d'expérience remplie par sujet avec citations datées |
| `ingestion-reseaux` | 6 | chaque save du lot a un verdict, au moins un playbook créé, propositions tranchées par la personne |
| `ingestion-articles` | 5, 6 | base des articles à jour, extraits courts marqués `court`, page auteur reliée |

## Ce que le socle fournit déjà (à copier, jamais réécrire)
- `.claude/skills/bibliothecaire/SKILL.md` : le texte du mode Bibliothécaire.
- `.claude/hooks/bibliothecaire-activate.js`, `liens-wiki-check.js`, `anti-suppression.js` et `.claude/settings.hooks.json`.
- `.claude/commands/cerveau.md`, `fin.md`, `passation.md`, `reprise.md`, `idee.md`.
- `outils/cerveau.py` : la recherche par le sens (copié en `scripts/cerveau.py` du vault).

## Outils joints par les skills du bloc
Tous en Python 3.9+, sans dépendance cachée, avec `--test` quand ils ont de la logique. Ils se copient dans `scripts/` du vault.

| Outil | Skill | Rôle |
|:-|:-|:-|
| `creer-vault.py` | architecture-vault | squelette du vault, n'écrase rien |
| `memoire-check.py` | memoire-fichiers | contrôle de MEMORY.md et des fichiers mémoire |
| `cerveau-check.py` | recherche-par-le-sens | test d'or de la recherche par le sens |
| `raw-nouveaux.py` | ingestion-fichiers | ce qui attend dans raw/ |
| `lint_wiki.py` | lint-wiki | bilan de santé (importé par le jardinier) |
| `jardinier.py` | jardinier | entretien de nuit, rodage, un commit |
| `sauvegarde-git.py` | securite-git-secrets | commit et push robustes, refus des secrets |
| `sauvegarde-drive.py`, `filtre-sauvegarde.txt` | sauvegardes-3-lieux | miroir, versions, coffre chiffré |
| `depot-scan.py` | ingestion-drive | scan et déplacement sûrs du Dépôt |
| `pull-notion.py` | ingestion-notion | copie incrémentale des bases |
| `pull-fathom.py` | ingestion-appels | rapatriement des appels |
| `saves-export.py` | ingestion-reseaux | liste des saves depuis l'export officiel |
| `articles-db.py` | ingestion-articles | base dédoublonnée des articles clippés |

## Temps
Les dix briques principales tiennent en quelques sessions courtes : chaque étape de chaque skill est prévue pour 20 minutes maximum. Les envois longs (premier miroir, premier rapatriement d'appels) tournent seuls pendant qu'on fait autre chose.

## Fin du bloc
Quand les dix briques sont cochées : entrée dans `log.md`, mise à jour de la ligne « où on en est » de `wiki/maps/parcours.md`, et proposition du bloc B (méthode et moteur Claude Code).


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
