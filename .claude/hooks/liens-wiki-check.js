#!/usr/bin/env node
// Hook PostToolUse (Write|Edit) : une page wiki/*.md doit porter au moins 3 [[liens]]
// vers d'autres pages (hors elle-même, index et log). Sinon sortie 2 : Claude ajoute les liens.
// Exclus : dossiers /archive/ et fichiers _index.md. Erreur interne = silencieux.
'use strict';
const fs = require('fs');
const path = require('path');

function countLinks(content, selfName) {
  const re = /\[\[([^\]|#]+)/g;
  let n = 0, m;
  while ((m = re.exec(content)) !== null) {
    const base = m[1].trim().replace(/\\/g, '/').split('/').pop().toLowerCase().replace(/\.md$/, '');
    if (base && base !== selfName && !['index', '_index', 'log'].includes(base)) n++;
  }
  return n;
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
      if (data.tool_name !== 'Write' && data.tool_name !== 'Edit') process.exit(0);
      const file = (data.tool_input && data.tool_input.file_path) || '';
      const norm = file.replace(/\\/g, '/');
      if (!/\/wiki\//.test(norm) || !norm.endsWith('.md')) process.exit(0);
      if (/\/archive\//.test(norm) || /\/_index\.md$/i.test(norm)) process.exit(0);
      const n = countLinks(fs.readFileSync(file, 'utf8'), path.basename(norm, '.md').toLowerCase());
      if (n >= 3) process.exit(0);
      process.stderr.write(`Page wiki avec ${n} lien(s) [[...]] (moins de 3). Ajoute des liens vers des pages `
        + 'existantes et une entrée dans index.md ou la map parente (règle de fin de session).');
      process.exit(2);
    } catch (e) { process.exit(0); }
  });
}

module.exports = { countLinks };
