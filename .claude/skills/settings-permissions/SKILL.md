---
name: settings-permissions
description: "Règle settings.json et les permissions de Claude Code : ce que Claude fait sans demander, ce qu'il demande, ce qui lui est interdit, à quel niveau ranger chaque réglage. Utiliser quand l'utilisateur dit « arrête de me demander la permission », « Claude a touché à un fichier qu'il ne devait pas », « règle les permissions », « mode auto ». Pas pour un script automatique à chaque événement (utiliser hooks-ecrire)."
---
# settings.json et permissions

## Pourquoi
Au début du système d'origine, chaque lecture et chaque commande banale demandait un clic. L'entrepreneur cliquait « oui » sans lire, ce qui rendait les vraies alertes inutiles. À l'inverse, une session lancée sans aucune garde a failli effacer du travail. La solution : une liste blanche large pour le banal, une liste « demande » courte pour ce qui compte, une liste noire pour les secrets et le destructif, plus les hooks du socle en filet de sécurité.

## Prérequis
- hooks-ecrire lu (le socle a l'anti-suppression : elle reste le filet même si une permission est trop large).
- Aucun coût.

## Interview
Lis d'abord : `~/.claude/settings.json`, `.claude/settings.json`, `.claude/settings.local.json` s'ils existent (ne recopie jamais une valeur secrète dans ta réponse : liste seulement les clés), `wiki/maps/moi.md` (niveau informatique), le fichier mémoire `feedback_autonomie.md`.

Puis demande :
1. « Quels dossiers je peux modifier sans te demander ? » (proposition : `wiki/`, `outputs/`).
2. « Quels dossiers sont intouchables ? » (proposition : `raw/` qui ne se modifie jamais, les secrets).
3. « Quelles commandes je lance souvent et qui t'agacent quand je demande ? » Si la personne ne sait pas, Claude lance le skill intégré `/fewer-permission-prompts` (s'il existe dans ta version), qui lit les transcriptions et propose une liste.
4. « Est-ce que tu veux que j'envoie du code sur GitHub sans demander ? » (par défaut : je demande).
5. « Tu travailles sur un seul ordinateur ou plusieurs ? » (décide ce qui va dans le fichier partagé par git ou dans le fichier local).

Range les réponses dans les fichiers de réglages, et une page `wiki/maps/permissions.md` qui explique chaque ligne en français.

## Construire

1. **Les trois niveaux (5 min).** Claude explique où va quoi :
   | Fichier | Portée | Dans git ? |
   |:-|:-|:-|
   | `~/.claude/settings.json` | tous les projets de la personne | non |
   | `.claude/settings.json` | ce vault, partagé | oui |
   | `.claude/settings.local.json` | ce vault, cet ordinateur seulement | non (ajoute-le au `.gitignore`) |
   Le plus précis gagne. Les hooks du vault vont dans `.claude/settings.json`, les réglages de goût (modèle, effort, thème) dans `~/.claude/settings.json`.

2. **Partir de l'exemple (10 min).** Claude ouvre `outils/settings.exemple.json`, l'adapte aux réponses, puis le FUSIONNE dans `.claude/settings.json` : il garde chaque clé existante (surtout `hooks`), ajoute les listes, retire la ligne `$commentaire`. Il valide le JSON : `python -c "import json;json.load(open('.claude/settings.json',encoding='utf-8'))"`.

3. **La syntaxe des règles (5 min).** À montrer à la personne avec ses propres exemples :
   - `Read`, `Glob`, `Grep` : tout l'outil.
   - `Edit(wiki/**)` : seulement sous ce dossier.
   - `Bash(git status:*)` : cette commande avec n'importe quels arguments.
   - `mcp__<serveur>__<outil>` : un outil d'un connecteur.
   L'ordre de décision est : `deny` gagne sur `ask`, qui gagne sur `allow`.

4. **Le mode de travail (5 min).** Claude présente les modes (touche Maj+Tab dans le terminal, ou le sélecteur de l'app) : normal (demande pour les écritures), accepter les modifications, plan (lecture seule), et le mode automatique si ta version le propose. Le mode automatique a ses propres listes `autoMode.allow` et `autoMode.soft_deny` dans `~/.claude/settings.json` : on y décrit en phrases ce qui est routine et ce qui doit rester confirmé (exemple de soft_deny : « écrire dans raw/, qui est immuable »). Jamais `--dangerously-skip-permissions` sans les hooks du socle branchés.

5. **Les variables utiles (5 min).** Dans la clé `env` : `CLAUDE_CODE_SUBAGENT_MODEL` (modèle par défaut des sous-agents, voir sous-agents-modeles). Rien de secret dans `env` : les clés vont dans `~/.claude/secrets/` et sont lues par les scripts.

6. **La page d'explication (5 min).** Claude écrit `wiki/maps/permissions.md` : chaque ligne `allow`, `ask`, `deny` avec sa raison en une phrase. Trois [[liens]] : [[hooks]], [[CLAUDE]], [[routage]].

## Test
Les trois sont vrais :
- Le JSON se charge sans erreur (commande de l'étape 2).
- Dans une nouvelle session, Claude lit une page du wiki et lance `git status` sans demander.
- Claude tente `Read` sur un fichier de `~/.claude/secrets/` : c'est refusé.

## Pièges vécus
- **Écraser les hooks.** Un réglage recopié par-dessus l'ancien fichier a débranché tous les hooks en silence. Toujours fusionner, jamais remplacer, et relire la clé `hooks` après.
- **La liste blanche trop large.** `Bash(*)` permet aussi la suppression. Les permissions larges se font par commande, et l'anti-suppression du socle reste branchée.
- **Les secrets dans settings.json.** Un jeton collé dans `env` part dans git. Les secrets vivent hors du vault, toujours.
- **Le fichier local commité.** `.claude/settings.local.json` doit être dans `.gitignore`.
- **Les clics « oui » réflexes.** Si la personne clique sans lire, la liste `allow` est trop courte. Agrandis-la sur le banal pour que les vraies questions se remarquent.

## Entretien dans le temps
- Une fois par mois, Claude relance `/fewer-permission-prompts` (ou relit les transcriptions) et propose les 5 commandes les plus demandées à ajouter.
- Chaque nouveau script dans `scripts/` qui tourne souvent : sa ligne `Bash(python scripts/<nom>.py:*)` dans `allow`.

## Après
Coche la ligne `settings-permissions` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, puis propose la brique suivante : sous-agents-modeles.
