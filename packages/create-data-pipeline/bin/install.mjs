#!/usr/bin/env node

/**
 * create-data-pipeline
 *
 * Install the data-pipeline skill for Claude Code.
 *
 * Usage:
 *   npx create-data-pipeline
 *   npx create-data-pipeline --target ~/.claude/skills/data-pipeline
 */

import { existsSync, mkdirSync, cpSync, readdirSync, statSync } from 'node:fs';
import { resolve, join, dirname } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath } from 'node:url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// ─── Parse arguments ────────────────────────────────────────
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
  create-data-pipeline — Install the data-pipeline skill for Claude Code

  Usage:
    npx create-data-pipeline [options]

  Options:
    --target <path>   Custom install directory (default: ~/.claude/skills/data-pipeline)
    --force           Overwrite existing installation
    --help            Show this help message
`);
  process.exit(0);
}

const forceInstall = args.includes('--force');
const targetIdx = args.indexOf('--target');
const customTarget = targetIdx !== -1 ? args[targetIdx + 1] : null;

// ─── Determine target directory ─────────────────────────────
const defaultTarget = join(homedir(), '.claude', 'skills', 'data-pipeline');
const targetDir = customTarget ? resolve(customTarget) : defaultTarget;

// ─── Source skill directory ─────────────────────────────────
const skillSource = resolve(__dirname, '..', 'skill');

if (!existsSync(skillSource)) {
  console.error('❌ Skill source directory not found. Package may be corrupted.');
  process.exit(1);
}

// ─── Pre-flight checks ─────────────────────────────────────
console.log('');
console.log('  📦 data-pipeline — 多模态知识管道技能');
console.log('  ────────────────────────────────────────');
console.log('');

if (existsSync(targetDir) && !forceInstall) {
  // Check if it's a real installation (has SKILL.md)
  if (existsSync(join(targetDir, 'SKILL.md'))) {
    console.log(`  ⚠️  已检测到现有安装: ${targetDir}`);
    console.log('');
    console.log('  使用 --force 覆盖现有安装:');
    console.log('    npx create-data-pipeline --force');
    console.log('');
    process.exit(0);
  }
}

// ─── Install ────────────────────────────────────────────────
console.log(`  📁 安装目标: ${targetDir}`);
console.log('');

try {
  // Create target directory
  mkdirSync(targetDir, { recursive: true });

  // Copy skill files recursively
  cpSync(skillSource, targetDir, {
    recursive: true,
    force: true,
  });

  // Ensure wiki directories exist
  const wikiDirs = [
    'wiki',
    'wiki/sources',
    'wiki/entities',
    'wiki/concepts',
    'wiki/syntheses',
    'graph',
    'raw',
  ];

  for (const dir of wikiDirs) {
    const dirPath = join(targetDir, dir);
    if (!existsSync(dirPath)) {
      mkdirSync(dirPath, { recursive: true });
    }
  }

  // Create empty wiki files if they don't exist
  const { writeFileSync } = await import('node:fs');

  const wikiFiles = {
    'wiki/index.md': `# Wiki Index

## Overview
- [概览](overview.md) — 活体综合内容

## Sources

## Entities

## Concepts

## Syntheses
`,
    'wiki/log.md': `# Wiki Log\n`,
    'wiki/overview.md': `---
title: "Overview"
type: synthesis
tags: []
sources: []
last_updated: ${new Date().toISOString().slice(0, 10)}
---

# 知识概览

尚无摄入的文档。使用 \`/pipeline-ingest <文件路径>\` 开始摄入。
`,
  };

  for (const [file, content] of Object.entries(wikiFiles)) {
    const filePath = join(targetDir, file);
    if (!existsSync(filePath)) {
      writeFileSync(filePath, content, 'utf-8');
    }
  }

  // ─── Count installed files ──────────────────────────────
  function countFiles(dir) {
    let count = 0;
    if (!existsSync(dir)) return 0;
    for (const entry of readdirSync(dir)) {
      const full = join(dir, entry);
      if (statSync(full).isDirectory()) {
        count += countFiles(full);
      } else {
        count++;
      }
    }
    return count;
  }

  const fileCount = countFiles(targetDir);

  // ─── Success output ─────────────────────────────────────
  console.log('  ✅ 安装成功！');
  console.log('');
  console.log(`  📄 共 ${fileCount} 个文件`);
  console.log(`  📁 ${targetDir}`);
  console.log('');
  console.log('  ────────────────────────────────────────');
  console.log('  📋 下一步:');
  console.log('');
  console.log('  1. 安装 Python 依赖:');
  console.log('     pip install openai pymupdf python-docx openpyxl python-pptx beautifulsoup4 pillow');
  console.log('');
  console.log('  2. 在 Claude Code 中配置 LLM API:');
  console.log('     对 Claude 说: "配置 LLM API" 或运行:');
  console.log(`     python ${join(targetDir, 'tools', 'pipeline_config.py')}`);
  console.log('');
  console.log('  3. 开始使用:');
  console.log('     对 Claude 说: "摄入 /path/to/document.pdf"');
  console.log('     对 Claude 说: "查询 主要主题是什么？"');
  console.log('     对 Claude 说: "检查维基"');
  console.log('     对 Claude 说: "构建知识图谱"');
  console.log('');

} catch (err) {
  console.error(`  ❌ 安装失败: ${err.message}`);
  process.exit(1);
}
