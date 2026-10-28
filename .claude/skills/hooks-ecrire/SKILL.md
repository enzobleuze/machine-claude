---
name: hooks-ecrire
description: "Apprend à écrire, brancher et tester un hook Claude Code (petit script lancé automatiquement avant ou après une action), et installe les hooks utiles en plus du socle : compteur de skills, mémo de compactage, gardes sur mesure. Utiliser quand l'utilisateur dit « à chaque fois que », « empêche Claude de », « je veux que ce soit automatique », « crée un hook ». Pas pour les permissions simples (utiliser settings-permissions)."
---
# Écrire et brancher des hooks

## Pourquoi
Une règle écrite dans CLAUDE.md est une consigne : Claude peut l'oublier. Un hook est un script que Claude Code lance lui-même à chaque événement : il ne s'oublie pas. Dans le système d'origine, les règles les plus graves (ne jamais supprimer du travail, ne pas écrire dans les zones privées, relier chaque page du wiki, activer le mode bibliothécaire) ont toutes fini en hook, après avoir été violées malgré une ligne dans le cœur. Le principe retenu : une règle violée deux fois descend en hook.

## Prérequis
- coeur-claude-md fait.
- Node installé (`node --version`). Sans Node, guide l'installation (nodejs.org, version LTS).
- Le socle a déjà branché trois hooks : bibliothécaire (début de session), anti-suppression (avant chaque commande), liens wiki (après chaque écriture). Ne les réécris pas : lis-les dans `.claude/hooks/` comme exemples.

## Interview
Lis d'abord : `.claude/settings.json` (clé `hooks`), le dossier `.claude/hooks/`, les fichiers mémoire `feedback_*` (une règle répétée deux fois est candidate), `log.md` (incidents).

Puis demande :
1. « Y a-t-il une chose que Claude a faite alors que tu lui avais dit de ne pas la faire ? » (candidat hook de garde PreToolUse).
2. « Y a-t-il une chose que tu dois rappeler au début de chaque conversation ? » (candidat SessionStart).
3. « Y a-t-il un contrôle que tu fais à la main après que Claude a écrit un fichier ? » (candidat PostToolUse).
4. « Tu veux savoir quelles commandes tu utilises vraiment ? » (compteur de skills, conseillé).
5. « Les longues conversations perdent-elles des détails après le résumé automatique ? » (mémo de compactage).

Range chaque besoin retenu dans `wiki/maps/hooks.md` (une ligne : événement, ce que le hook fait, fichier).

## Construire

1. **Comprendre les événements (5 min).** Claude explique en une ligne chacun des événements utiles :
   | Événement | Quand | Usage typique |
   |:-|:-|:-|
   | `SessionStart` | début de conversation (`source` : startup, resume, clear, compact) | injecter un rappel ou un état |
   | `UserPromptSubmit` | chaque message de la personne | compter, ajouter un contexte |
   | `PreToolUse` | avant un outil (`matcher` : Bash, Write, Edit, Skill…) | bloquer une action dangereuse |
   | `PostToolUse` | après un outil | vérifier ce qui vient d'être écrit |
   | `PreCompact` | avant le résumé automatique | sauver ce qui va se perdre |
   | `Stop` | fin d'un tour | son, notification (attention au bruit) |
   Pour la liste exacte de ta version : `/hooks` dans Claude Code, ou la page officielle « hooks » de la documentation.

2. **Le contrat d'un hook (5 min).** Claude Code envoie un JSON sur l'entrée standard (`session_id`, `transcript_path`, `cwd`, `hook_event_name`, `tool_name`, `tool_input`, `prompt` selon l'événement). Le script répond par son code de sortie :
   - `0` : on continue. Pour `SessionStart` et `UserPromptSubmit`, ce qui sort sur stdout s'ajoute au contexte de Claude (texte simple, ou JSON `{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"..."}}`).
   - `2` : on bloque (PreToolUse) ou on signale (PostToolUse) ; le texte de stderr part à Claude, qui peut corriger.
   - Toute erreur interne du hook doit sortir `0` : un hook cassé ne bloque jamais la session.

3. **Écrire le hook depuis le gabarit (15 min).** Claude copie `outils/gabarit-hook.js` vers `.claude/hooks/<nom>.js`, remplace la fonction `regle()` et le `MESSAGE`, puis ajoute ses cas dans le bloc `--test`. Garde chaque hook sur un seul travail, en Node sans dépendance, avec une limite de 3 secondes.

4. **Brancher dans settings.json (5 min).** Claude ajoute le bloc sous la clé `hooks` de `.claude/settings.json`, sans effacer ceux qui existent :
   ```json
   "PreToolUse": [
     { "matcher": "Write|Edit", "hooks": [
       { "type": "command", "command": "node \"$CLAUDE_PROJECT_DIR\"/.claude/hooks/<nom>.js", "timeout": 5 } ] }
   ]
   ```
   `$CLAUDE_PROJECT_DIR` marche sous Windows aussi, entouré de guillemets comme ici. Un hook pour tous les projets va dans `~/.claude/settings.json`.

5. **Tester hors session (5 min).** Claude lance l'auto-test (`node .claude/hooks/<nom>.js --test` affiche `ok`), puis un vrai JSON :
   - Mac/Linux et Git Bash : `echo '{"tool_name":"Write","tool_input":{"file_path":"wiki/clients/x.md"}}' | node .claude/hooks/<nom>.js; echo $?`
   - PowerShell : `'{"tool_name":"Write","tool_input":{"file_path":"wiki/clients/x.md"}}' | node .claude/hooks/<nom>.js; $LASTEXITCODE`
   Le code attendu est 2 pour un cas interdit, 0 pour un cas permis.

6. **Le compteur de skills (10 min, conseillé).** Claude copie `outils/compteur-skills.js` dans `.claude/hooks/` et le branche deux fois : `PreToolUse` avec `"matcher": "Skill"` et `UserPromptSubmit` sans matcher. Après un mois, `outputs/skill-usage/usage.jsonl` dit quelles commandes ne servent jamais (voir ameliorer-les-skills).

7. **Le mémo de compactage (10 min, si la personne fait de longues conversations).** Claude copie `outils/memo-compactage.js` et le branche sur `PreCompact` (sans matcher) et sur `SessionStart` avec `"matcher": "compact"`. Il adapte `MEMO_MOTIF_TACHE` au format des identifiants de tâches de la personne (variable d'environnement, ou la ligne du motif).

8. **Recharger (2 min).** Les hooks se lisent au démarrage : la personne ferme et rouvre Claude Code, ou Claude vérifie dans `/hooks` que le nouveau hook apparaît.

## Test
Dans une vraie session, Claude tente l'action que le nouveau hook doit bloquer (par exemple écrire un fichier vide dans la zone protégée). Le hook la bloque et Claude affiche son message. L'auto-test `--test` de chaque hook installé affiche `ok`.

## Pièges vécus
- **Le hook qui casse la session.** Un hook qui plante en sortant 2 bloque tout. D'où la règle : `try/catch` autour de tout, sortie 0 sur erreur, délai maximum.
- **Le hook trop bavard.** Un hook de fin de tour qui parle à chaque réponse a été retiré : sur des sessions de contenu, il noyait tout. Un hook parle seulement quand il a quelque chose d'utile à dire.
- **Le sentinelle oublié.** Un hook qui injecte un rappel à chaque message gonfle le contexte. Pour un rappel, utilise `SessionStart` ou une mémoire « déjà dit » par session (fichier temporaire par `session_id`).
- **Les hooks de démarrage qui cassent le cache.** Une sortie qui change à chaque lancement (une heure, un compteur) oblige les appels automatiques à tout repayer. Pas d'heure ni de nombre changeant dans ce qu'un hook injecte au démarrage.
- **Les doublons de plugins.** Des plugins installés ajoutent leurs propres hooks. Avant d'ajouter le tien, regarde `/hooks` pour ne pas faire deux fois le même travail.
- **Windows et `bash`.** Un hook en `.sh` ne marche que si Git Bash est là. Le Node marche partout : préfère-le.

## Entretien dans le temps
- Chaque nouvelle règle violée deux fois : Claude propose un hook, montre son code, attend le oui.
- Une fois par trimestre, Claude relit `/hooks` et `wiki/maps/hooks.md` : un hook qui ne sert plus se débranche (on garde le fichier).

## Après
Coche la ligne `hooks-ecrire` dans `wiki/maps/parcours.md`, une ligne dans `log.md`, la liste à jour dans `wiki/maps/hooks.md`, puis propose la brique suivante : settings-permissions.
