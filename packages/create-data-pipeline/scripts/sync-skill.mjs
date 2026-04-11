#!/usr/bin/env node

/**
 * sync-skill.mjs — Sync latest source code from project to skill package.
 *
 * Run this before `npm publish` to ensure the package has the latest code.
 *
 * Usage:
 *   node scripts/sync-skill.mjs
 */

import { cpSync, mkdirSync, existsSync } from 'node:fs';
import { resolve, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const pkgRoot = resolve(__dirname, '..');
const projectRoot = resolve(pkgRoot, '..', '..');
const skillDir = resolve(pkgRoot, 'skill');

const copies = [
  // tools
  { from: 'tools/pipeline_ingest.py', to: 'tools/pipeline_ingest.py' },
  { from: 'tools/pipeline_query.py', to: 'tools/pipeline_query.py' },
  { from: 'tools/pipeline_lint.py', to: 'tools/pipeline_lint.py' },
  { from: 'tools/pipeline_graph.py', to: 'tools/pipeline_graph.py' },
  { from: 'tools/pipeline_config.py', to: 'tools/pipeline_config.py' },
  { from: 'tools/build_graph.py', to: 'tools/build_graph.py' },
  // core
  { from: 'core/llm_config.py', to: 'core/llm_config.py' },
  { from: 'core/retrieval.py', to: 'core/retrieval.py' },
  { from: 'core/wikilink.py', to: 'core/wikilink.py' },
  { from: 'core/export.py', to: 'core/export.py' },
];

const dirCopies = [
  { from: 'backend/processors', to: 'backend/processors' },
];

console.log('🔄 Syncing source files to skill package...\n');

for (const { from, to } of copies) {
  const src = resolve(projectRoot, from);
  const dst = resolve(skillDir, to);
  mkdirSync(dirname(dst), { recursive: true });
  if (existsSync(src)) {
    cpSync(src, dst, { force: true });
    console.log(`  ✓ ${from}`);
  } else {
    console.log(`  ⚠ ${from} (not found, skipped)`);
  }
}

for (const { from, to } of dirCopies) {
  const src = resolve(projectRoot, from);
  const dst = resolve(skillDir, to);
  mkdirSync(dst, { recursive: true });
  if (existsSync(src)) {
    cpSync(src, dst, { recursive: true, force: true });
    console.log(`  ✓ ${from}/`);
  }
}

console.log('\n✅ Sync complete.');
