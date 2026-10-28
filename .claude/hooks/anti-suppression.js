#!/usr/bin/env node
// Hook PreToolUse (Bash) : bloque les commandes qui détruisent du travail sans retour.
// Sortie 2 = commande bloquée, le message part à Claude. Erreur interne = on laisse passer.
'use strict';

const DANGER = new RegExp([
  String.raw`\brm\s+-[^\s]*[rR][^\s]*f`, String.raw`\brm\s+-[^\s]*f[^\s]*[rR]`,
  String.raw`\bRemove-Item\b.*-Recurse`,
  String.raw`\bgit\s+reset\s+.*--hard`, String.raw`\bgit\s+clean\s+-[^\s]*f`,
  String.raw`\bgit\s+checkout\s+\.(\s|$)`, String.raw`\bgit\s+restore\s+\.(\s|$)`,
  String.raw`\bgit\s+branch\s+-D\b`, String.raw`\bgit\s+push\s+.*--force`,
  String.raw`\bdd\s+.*of=`, String.raw`\bshred\s`, String.raw`\bmkfs\.`,
].join('|'));

function check(cmd) {
  if (!cmd || /\bFORCE_DESTRUCTIVE=1\b/.test(cmd)) return null;
  return DANGER.test(cmd) ? cmd : null;
}

if (require.main === module) {
  let input = '';
  const t = setTimeout(() => process.exit(0), 3000);
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', c => input += c);
  process.stdin.on('end', () => {
    clearTimeout(t);
    try {
      const data = JSON.parse(input);
      const blocked = check((data.tool_input && data.tool_input.command) || '');
      if (!blocked) process.exit(0);
      process.stderr.write(
`Commande destructrice bloquée : ${blocked}

Alternatives sûres :
- au lieu de supprimer un dossier : mkdir -p .claude/corbeille && mv <dossier> .claude/corbeille/
- au lieu de git reset --hard ou git checkout . : git stash push -m "sauvegarde auto"
- au lieu de git clean -fd : git stash push -u -m "sauvegarde auto"
Si c'est vraiment nécessaire : demande d'abord l'accord explicite de la personne que tu sers dans la conversation,
puis relance avec FORCE_DESTRUCTIVE=1 devant la commande (une seule fois).`);
      process.exit(2);
    } catch (e) { process.exit(0); }
  });
}

module.exports = { check };
