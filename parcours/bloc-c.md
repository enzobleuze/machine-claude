---
title: "Bloc C : Experts"
type: map
created: AAAA-MM-JJ
updated: AAAA-MM-JJ
tags: [machine, parcours]
sources: ["[[blueprint]]", "[[parcours]]", "[[routage]]"]
---
# Bloc C : les experts

But du bloc : Claude cesse d'imaginer ce que diraient les experts de l'utilisateur et leur demande, sources citées. Puis chaque décision passe devant un comité, et chaque texte destiné aux clients passe devant un board, avec une porte qui refuse tout texte modifié après le verdict.

À avoir avant : bloc A (vault, mémoire, recherche par le sens `scripts/cerveau.py`, ingestion) et bloc B (cœur `CLAUDE.md`, sous-agents, `claude -p`). Pour le board et le client idéal : l'entretien fondateur du bloc D (client idéal, voix, preuves). On peut faire le bloc C avant la fin du bloc D, puis revenir compléter les sièges.

## Ordre et dépendances

| # | Skill | Dépend de | Ce qu'il produit | Test binaire |
|:-|:-|:-|:-|:-|
| 1 | `notebooklm-brancher` | bloc A | `notebooklm` installé et connecté, `scripts/nlm_ask.py` | `nlm_ask.py auth` sort 0 et une vraie question sort 0 avec une source citée |
| 2 | `carnets-experts` | 1 | un carnet par expert, `carnets.json`, `wiki/maps/carnets.md` | chaque carnet répond à sa question d'identité (sortie 0) et l'utilisateur reconnaît l'auteur |
| 3 | `routage-carnets` | 2 | `wiki/maps/routage-carnets.md`, règle de phase 0 dans `CLAUDE.md` | sur un sujet réel, Claude choisit seul le bon carnet et cite le principe sourcé |
| 4 | `controle-verite` | bloc A (fiches sources) | `scripts/verite.py`, `auteurs.json`, `noms-prives.txt`, chiffres permis | texte piège : 3 sorties 1 ; texte propre : 3 sorties 0 |
| 5 | `controle-voix` | bloc D (guide de voix) | `scripts/lint_voix.py`, `regles-voix.json` | texte piège sort 1 ; texte approuvé par l'utilisateur sort 0 |
| 6 | `agent-client-ideal` | 4, bloc D | `.claude/agents/client-ideal.md`, `verbatims.md` pseudonymisés | `verite.py noms` sort 0 sur les verbatims ; un test complet est jugé crédible |
| 7 | `comite-decision` | bloc B | skill de séance `comite`, archive `outputs/comite/` | une vraie séance : 5 avis différents, un angle mort trouvé à la relecture |
| 8 | `comite-roast-ancre` | 1, 2, 3, 7 | `scripts/roast/`, `sieges-roast.json`, skill de séance `roast` | une séance rapide va au bout, citations retrouvées mot pour mot |
| 9 | `board-textes` | 1, 2, 3, 4, 5, 6 | `scripts/porte_board.py`, `board-config.json`, skill de séance `board` | un texte réel : `board.md` VERT et porte à 0 ; un mot ajouté : porte à 1 |
| 10 | `skills-marketing` | 5, 9, bloc D | pack installé, contexte produit, filtre de sortie | un skill du pack se déclenche, cite le vrai contexte, et sa sortie finale passe le lint |

Les briques 4 et 5 ne dépendent pas de NotebookLM : si la connexion Google bloque, les faire d'abord.

## Outils fournis (tous en Python, bibliothèque standard seule, avec `selftest`)

| Outil | Rôle | Commandes |
|:-|:-|:-|
| `notebooklm-brancher/outils/nlm_ask.py` | une question à un carnet, conversation neuve, taille limitée, garde-fou auteur et sources | `auth`, `ask <carnet> <question.txt>`, `selftest` |
| `notebooklm-brancher/outils/garder-connexion.pyw` | maintien de la connexion toutes les 20 minutes, repli sur les cookies de Firefox, alerte après 3 échecs | `--une-fois`, `--navigateur <nom>`, `--test` |
| `notebooklm-brancher/outils/reparer-connexion.ps1` | connexion durable sous Windows (Firefox, antivirus, import, tâche de maintien), lancé par l'utilisateur en administrateur | `-Email <adresse>` |
| `carnets-experts/outils/carnets.modele.json` | gabarit du registre des carnets | |
| `comite-roast-ancre/outils/roast.py` | sièges en `claude -p` sans outils, en parallèle ; notes pondérées et bandes | `tour <dossier> <n>`, `scores <dossier>`, `selftest` |
| `comite-roast-ancre/outils/siege-systeme.md` | prompt système d'un siège | |
| `board-textes/outils/porte_board.py` | texte extrait, empreinte, porte | `extraire`, `empreinte`, `verifier <texte> <board.md>`, `selftest` |
| `board-textes/outils/board-config.modele.json`, `board.modele.md` | sièges requis, gabarit du verdict | |
| `controle-verite/outils/verite.py` | chiffres sourcés, attributions, noms privés, pseudonymisation | `chiffres`, `attributions`, `noms`, `pseudonymiser`, `selftest` |
| `controle-voix/outils/lint_voix.py`, `regles-voix.modele.json` | lint par règles dures configurables | `<texte> [--fix] [--json]`, `selftest` |
| `.claude/agents/client-ideal.modele.md` | gabarit du sous-agent client idéal | |

## Tests de fin de bloc
1. Tous les selftests passent : `python scripts/<outil>.py selftest` imprime `selftest OK` pour `nlm_ask`, `verite`, `lint_voix`, `porte_board`, et `roast/roast.py`.
2. Une question réelle à chaque carnet sort 0.
3. Un vrai texte de l'utilisateur fait le tour complet : contrôles gratuits, sièges, `board.md` VERT, porte à 0 ; puis une virgule changée, porte à 1.
4. Une vraie décision passe au comité (classique ou roast) et l'utilisateur dit que le verdict l'aide.

## Ce que le bloc laisse dans le vault
`carnets.json`, `board-config.json`, `regles-voix.json`, `auteurs.json` à la racine ; `scripts/nlm_ask.py`, `scripts/verite.py`, `scripts/lint_voix.py`, `scripts/porte_board.py`, `scripts/roast/` ; `.claude/agents/client-ideal.md` ; les cartes `wiki/maps/carnets.md`, `routage-carnets.md`, `board-textes.md`, `doctrine-arbitrages.md`, `regles-verite.md`, `client-ideal.md`, `sieges-roast.json` ; dans `.gitignore` : `noms-prives.txt`, `outputs/client-ideal/table.json`, `outputs/client-ideal/sources/`.


Voir aussi : [[blueprint]] (carte générale), [[parcours]] (suivi), [[routage]] (commandes).
