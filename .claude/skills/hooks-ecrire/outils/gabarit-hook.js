#!/usr/bin/env node
// Gabarit de hook Claude Code (Node, sans dépendance). Copie ce fichier, renomme-le, change REGLE et MESSAGE.
// Événement visé : PreToolUse (avant un outil). Claude Code envoie un JSON sur l'entrée standard :
//   { session_id, transcript_path, cwd, hook_event_name, tool_name, tool_input: {...} }
// Sorties : code 0 = on laisse passer ; code 2 = on bloque, le texte de stderr part à Claude.
// Règle d'or : une erreur interne du hook laisse TOUJOURS passer (un hook cassé ne doit jamais bloquer la session).
'use strict';

// À ADAPTER : ce que le hook surveille. Ici : écrire dans un dossier protégé.
const PROTEGE = /(^|[\\/])wiki[\\/](finances|clients)[\\/]/i;

function regle(data) {
  const outil = data.tool_name || '';
  const entree = data.tool_input || {};
  if (!/^(Write|Edit|MultiEdit)$/.test(outil)) return null;
  const chemin = entree.file_path || '';
  return PROTEGE.test(chemin) ? `écriture dans une zone protégée : ${chemin}` : null;
}

const MESSAGE = (raison) =>
`Action bloquée par un hook : ${raison}
Demande d'abord l'accord explicite de la personne dans la conversation, puis explique-lui pourquoi tu dois écrire ici.`;

function main() {
  let brut = '';
  const garde = setTimeout(() => process.exit(0), 3000); // jamais plus de 3 s
  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (c) => (brut += c));
  process.stdin.on('end', () => {
    clearTimeout(garde);
    try {
      const raison = regle(JSON.parse(brut || '{}'));
      if (!raison) process.exit(0);
      process.stderr.write(MESSAGE(raison));
      process.exit(2);
    } catch (e) {
      process.exit(0);
    }
  });
}

// Auto-test : node gabarit-hook.js --test  (doit afficher « ok »)
if (process.argv[2] === '--test') {
  const assert = require('assert');
  assert.ok(regle({ tool_name: 'Write', tool_input: { file_path: 'C:/v/wiki/clients/a.md' } }));
  assert.ok(regle({ tool_name: 'Edit', tool_input: { file_path: '/v/wiki/finances/b.md' } }));
  assert.strictEqual(regle({ tool_name: 'Write', tool_input: { file_path: '/v/wiki/maps/c.md' } }), null);
  assert.strictEqual(regle({ tool_name: 'Bash', tool_input: { command: 'ls' } }), null);
  console.log('ok');
} else if (require.main === module) {
  main();
}

module.exports = { regle };
