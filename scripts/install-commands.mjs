#!/usr/bin/env node

/**
 * install-commands.mjs
 *
 * 安装 knowledge-pipline 的斜杠命令到 ~/.claude/commands/
 * 使 /pipeline-ingest, /pipeline-query, /pipeline-graph, /pipeline-lint 全局可用
 *
 * 用法：
 *   node scripts/install-commands.mjs
 *   # 或者在 npx skills add 之后：
 *   node ~/.agents/skills/knowledge-pipline/scripts/install-commands.mjs
 */

import { existsSync, mkdirSync, copyFileSync, readdirSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Find commands source directory
// npx skills add strips .claude/ dir, so we look in commands/ first
const repoRoot = join(__dirname, '..');
let commandsSource = join(repoRoot, 'commands');
if (!existsSync(commandsSource)) {
  commandsSource = join(repoRoot, '.claude', 'commands');
}

// Target: ~/.claude/commands/
const targetDir = join(homedir(), '.claude', 'commands');

const commandFiles = [
  'pipeline-ingest.md',
  'pipeline-query.md',
  'pipeline-graph.md',
  'pipeline-lint.md',
  'pipeline-config.md',
];

console.log('');
console.log('  📦 knowledge-pipline — 安装斜杠命令');
console.log('  ────────────────────────────────────────');
console.log('');

// Ensure target directory exists
if (!existsSync(targetDir)) {
  mkdirSync(targetDir, { recursive: true });
}

let installed = 0;

for (const file of commandFiles) {
  const src = join(commandsSource, file);
  const dst = join(targetDir, file);

  if (!existsSync(src)) {
    console.log(`  ⚠️  未找到: ${file}`);
    continue;
  }

  copyFileSync(src, dst);
  const cmdName = file.replace('.md', '');
  console.log(`  ✅ /${cmdName}`);
  installed++;
}

console.log('');
console.log(`  安装完成！${installed} 个斜杠命令已添加到 ${targetDir}`);
console.log('');
console.log('  现在可以在 Claude Code 中使用：');
console.log('    /pipeline-config                          # 配置 LLM API');
console.log('    /pipeline-ingest "D:\\path\\to\\document.pdf"  # 摄入文档');
console.log('    /pipeline-query "你的问题"                   # 查询');
console.log('    /pipeline-graph                            # 构建知识图谱');
console.log('    /pipeline-lint                             # 检查维基');
console.log('');
