#!/usr/bin/env node
// Hook SessionStart : injecte le skill Bibliothécaire au début de chaque session.
// Ne bloque jamais la session : toute erreur sort en silence avec le code 0.
'use strict';
const fs = require('fs');
const path = require('path');

try {
  const projectDir = process.env.CLAUDE_PROJECT_DIR || process.cwd();
  const skillPath = path.join(projectDir, '.claude', 'skills', 'bibliothecaire', 'SKILL.md');
  if (fs.existsSync(skillPath)) {
    let body = fs.readFileSync(skillPath, 'utf8').replace(/^﻿/, '');
    if (body.startsWith('---')) {
      const end = body.indexOf('\n---', 3);
      if (end !== -1) body = body.slice(end + 4).trim();
    }
    if (body) {
      process.stdout.write(JSON.stringify({
        hookSpecificOutput: { hookEventName: 'SessionStart', additionalContext: body },
      }) + '\n');
    }
  }
} catch (e) { /* silencieux */ }
process.exit(0);
