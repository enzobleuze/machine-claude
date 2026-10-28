#!/usr/bin/env node
// Mémo fidèle avant le compactage automatique, réinjecté juste après.
// Le résumé automatique de Claude Code perd des détails (demandes exactes, fichiers touchés).
// À brancher sur DEUX événements (voir SKILL.md) :
//   PreCompact                          -> lit la transcription, écrit outputs/passation/auto/<session>.md
//   SessionStart (matcher "compact")    -> réinjecte ce mémo dans le contexte
// Zéro appel modèle. Échoue en silence : ne bloque jamais un tour.
'use strict';
const fs = require('fs');
const path = require('path');

const RACINE = process.env.CLAUDE_PROJECT_DIR || '.';
const SORTIE = path.join(RACINE, 'outputs', 'passation', 'auto');
// Identifiants de tâches à repérer (ex. ABC-123). Change le motif selon ton outil de tâches.
const TACHE = new RegExp(process.env.MEMO_MOTIF_TACHE || '\\b[A-Z]{2,5}-\\d+\\b', 'g');

function memo(lignes) {
  const demandes = [], fichiers = [], taches = [];
  let todo = null;
  for (const ligne of lignes) {
    let e;
    try { e = JSON.parse(ligne); } catch (_) { continue; }
    const m = e.message || {};
    const c = m.content;
    if (e.type === 'user' && typeof c === 'string' && !c.startsWith('<')) demandes.push(c.trim().slice(0, 800));
    for (const x of Array.isArray(c) ? c : []) {
      if (e.type === 'user' && x.type === 'text' && !String(x.text).startsWith('<')) demandes.push(String(x.text).trim().slice(0, 800));
      if (x.type === 'tool_use') {
        const i = x.input || {};
        if (['Edit', 'Write', 'MultiEdit', 'NotebookEdit'].includes(x.name) && i.file_path) fichiers.push(i.file_path);
        if (['TodoWrite', 'TaskCreate', 'TaskUpdate'].includes(x.name)) todo = JSON.stringify(i).slice(0, 1500);
      }
    }
    for (const t of ligne.match(TACHE) || []) taches.push(t);
  }
  const uniq = (a, n) => [...new Set(a.reverse())].slice(0, n);
  return [
    '# Mémo de compactage (fidèle, écrit avant le résumé automatique)', '',
    '## Demandes de la personne (mot pour mot, les plus récentes en dernier)',
    ...demandes.slice(-10).map((d) => `- ${d}`), '',
    '## Fichiers modifiés', ...uniq(fichiers, 25).map((f) => `- ${f}`), '',
    '## Tâches citées', uniq(taches, 15).join(', ') || 'aucune', '',
    '## Dernière liste de tâches', todo || 'aucune', '',
  ].join('\n');
}

function principal(d) {
  const sid = String(d.session_id || 'sans-id').replace(/[^\w-]/g, '');
  const fichier = path.join(SORTIE, `${sid}.md`);
  if (d.hook_event_name === 'PreCompact') {
    if (!d.transcript_path || !fs.existsSync(d.transcript_path)) return;
    fs.mkdirSync(SORTIE, { recursive: true });
    fs.writeFileSync(fichier, memo(fs.readFileSync(d.transcript_path, 'utf8').split('\n')));
  } else if (d.hook_event_name === 'SessionStart' && d.source === 'compact' && fs.existsSync(fichier)) {
    process.stdout.write(JSON.stringify({ hookSpecificOutput: {
      hookEventName: 'SessionStart',
      additionalContext: 'Mémo fidèle écrit juste avant le compactage. Il prime sur le résumé pour les demandes exactes :\n\n'
        + fs.readFileSync(fichier, 'utf8') } }));
  }
}

if (process.argv[2] === '--test') {
  const assert = require('assert');
  const t = [
    JSON.stringify({ type: 'user', message: { content: 'Range ma page ABC-12' } }),
    JSON.stringify({ type: 'assistant', message: { content: [{ type: 'tool_use', name: 'Write', input: { file_path: '/v/a.md' } }] } }),
    'pas du json',
  ];
  const s = memo(t);
  assert.ok(s.includes('Range ma page ABC-12'));
  assert.ok(s.includes('/v/a.md'));
  assert.ok(s.includes('ABC-12'));
  console.log('ok');
} else {
  let brut = '';
  process.stdin.on('data', (c) => (brut += c));
  process.stdin.on('end', () => { try { principal(JSON.parse(brut || '{}')); } catch (_) { /* silence */ } });
}
