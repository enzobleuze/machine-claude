#!/usr/bin/env node
// Hook qui compte l'usage des skills et des commandes, pour repérer les commandes mortes.
// À brancher sur DEUX événements (voir SKILL.md) :
//   PreToolUse avec matcher "Skill"  -> Claude a lancé un skill seul (via = "claude")
//   UserPromptSubmit                 -> la personne a tapé /commande (via = "humain")
// Écrit une ligne JSON par usage dans outputs/skill-usage/usage.jsonl. Ne bloque jamais.
'use strict';
const fs = require('fs');
const path = require('path');

function lire(d) {
  if (d.tool_name === 'Skill' && d.tool_input) return { skill: d.tool_input.skill, via: 'claude' };
  if (typeof d.prompt === 'string') {
    const m = d.prompt.trim().match(/^\/([\w:.-]+)/);
    if (m) return { skill: m[1], via: 'humain' };
  }
  return null;
}

if (process.argv[2] === '--test') {
  const assert = require('assert');
  assert.deepStrictEqual(lire({ tool_name: 'Skill', tool_input: { skill: 'reprise' } }), { skill: 'reprise', via: 'claude' });
  assert.deepStrictEqual(lire({ prompt: '  /idee acheter un micro' }), { skill: 'idee', via: 'humain' });
  assert.strictEqual(lire({ prompt: 'bonjour' }), null);
  console.log('ok');
} else {
  let brut = '';
  process.stdin.on('data', (c) => (brut += c));
  process.stdin.on('end', () => {
    try {
      const d = JSON.parse(brut || '{}');
      const u = lire(d);
      if (!u || !u.skill) return;
      const dir = path.join(process.env.CLAUDE_PROJECT_DIR || '.', 'outputs', 'skill-usage');
      fs.mkdirSync(dir, { recursive: true });
      fs.appendFileSync(path.join(dir, 'usage.jsonl'),
        JSON.stringify({ ts: new Date().toISOString(), skill: u.skill, via: u.via, session: d.session_id }) + '\n');
    } catch (e) { /* un compteur raté ne bloque jamais la session */ }
  });
}
