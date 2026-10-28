---
name: bibliothecaire-installer
description: "Installe le mode Bibliothécaire toujours actif : un hook de début de session injecte la façon de chercher dans le vault (trois étagères vécu, principe, source ; le sens avant les mots ; aller à la vraie note). Utiliser quand l'utilisateur dit « installe le bibliothécaire », « tu ne regardes pas mes notes », « brique ». Pas pour le moteur de recherche lui-même (utiliser recherche-par-le-sens)."
---
# Installer le Bibliothécaire

## Pourquoi
Dans le système d'origine, Claude répondait avec du savoir général alors que le vault contenait la vraie scène, le vrai client, la vraie phrase. Il fallait lui rappeler à chaque fois de chercher. Le mode Bibliothécaire, injecté par un hook au début de chaque session, a réglé ça : Claude fouille trois étagères (le vécu, le principe, la source), remarque laquelle est vide et le dit au lieu de boucher le trou avec une phrase générique.

## Prérequis
- architecture-vault et memoire-fichiers faits.
- Node.js installé (pour les hooks). Windows : `winget install OpenJS.NodeJS.LTS`. Mac : `brew install node`. Vérifie avec `node --version`.
- Fichiers du socle de ce repo, déjà écrits : `.claude/skills/bibliothecaire/SKILL.md`, `.claude/hooks/bibliothecaire-activate.js`, `.claude/hooks/liens-wiki-check.js`, `.claude/hooks/anti-suppression.js`, `.claude/settings.hooks.json`, `.claude/commands/cerveau.md`. Ne les réécris pas : copie-les.

## Interview
Lis d'abord : `.claude/settings.json` du vault (hooks déjà présents ?), `wiki/maps/architecture.md` (noms des tiroirs).

Puis demande :
1. « Où sont tes vraies histoires de terrain ? » (fiches clients, transcriptions d'appels, journal). Ce sera l'étagère VÉCU.
2. « Où sont tes méthodes et tes principes ? » Étagère PRINCIPE.
3. « Quelles sources fais-tu autorité ? » (livres, auteurs, documents internes). Étagère SOURCE.
4. « Y a-t-il un dossier que je ne dois jamais citer ? » (privé). Il sera exclu.

Range la carte des étagères dans `wiki/maps/etageres.md` (trois sections, chacune avec les dossiers concernés et 3 liens).

## Construire
1. **Copier le socle (3 min).** Depuis ce repo vers le vault : `.claude/skills/bibliothecaire/`, les trois hooks de `.claude/hooks/`, `.claude/commands/cerveau.md`.
2. **Adapter les étagères (5 min).** Dans le `SKILL.md` du bibliothécaire copié, remplace les exemples de dossiers des trois étagères par ceux de l'interview. Garde tout le reste tel quel.
3. **Brancher les hooks (5 min).** Fusionne le contenu de `.claude/settings.hooks.json` dans `.claude/settings.json` du vault. Si le fichier existe déjà, ajoute les entrées dans les tableaux `SessionStart`, `PreToolUse` et `PostToolUse` existants sans en retirer. Sous Windows, la commande `node "$CLAUDE_PROJECT_DIR"/.claude/hooks/...` marche dans Claude Code tel quel ; si elle échoue, remplace `$CLAUDE_PROJECT_DIR` par le chemin absolu du vault entre guillemets.
4. **Vérifier chaque hook à la main (5 min).**
   ```bash
   echo '{}' | node .claude/hooks/bibliothecaire-activate.js
   echo '{"tool_name":"Bash","tool_input":{"command":"rm -rf wiki"}}' | node .claude/hooks/anti-suppression.js; echo "code $?"
   ```
   Le premier affiche un JSON contenant « MODE BIBLIOTHÉCAIRE ». Le second sort le code 2 (commande bloquée).
5. **Règle dans le cœur (2 min).** Ajoute au `CLAUDE.md` : « Avant de produire, consulte le wiki : les vraies scènes battent les inventées. Bibliothécaire toujours actif, coupé seulement sur « stop bibliothécaire ». »
6. **Route (1 min).** Dans `wiki/maps/routage.md`, la ligne « cherche dans mes notes » pointe vers `/cerveau`.

## Test
Redémarre Claude Code dans le vault et pose une question métier dont la réponse est dans une note précise. Claude répond en citant cette note par son chemin, et nomme une étagère vide s'il y en a une. Et l'écriture d'une page wiki avec un seul lien déclenche le rappel des 3 liens.

## Pièges vécus
- Hook injecté mais skill trop long : il mangeait le contexte de chaque session. Garde le texte du bibliothécaire court (une page).
- Réponses qui déversaient dix fiches brutes : la règle « réponds, ne déverse pas » est dans le skill. Une liste brute seulement avec `/cerveau` ou sur demande.
- Phrases attribuées à la personne alors qu'elles venaient d'un document : la règle « qui a dit quoi » sépare ses mots, ceux des sources et les déductions de Claude.
- Hook qui plante et bloque la session : les hooks du socle sortent toujours 0 en cas d'erreur interne, garde ce comportement si tu les modifies.

## Entretien dans le temps
Quand une réponse rate une note qui existait, ajoute la question au test d'or de recherche-par-le-sens. Quand un nouveau tiroir apparaît, mets à jour `wiki/maps/etageres.md` et le skill.

## Après
Coche la ligne `bibliothecaire-installer` dans `wiki/maps/parcours.md`, entrée dans `log.md`, puis propose recherche-par-le-sens.
