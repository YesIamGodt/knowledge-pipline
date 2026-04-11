# create-data-pipeline

一键安装 **data-pipeline** 技能到 Claude Code。

## 安装

```bash
npx create-data-pipeline
```

### 选项

```bash
npx create-data-pipeline --force          # 覆盖已有安装
npx create-data-pipeline --target ./my-dir  # 自定义安装路径
```

## 安装后配置

### 1. Python 依赖

```bash
pip install openai pymupdf python-docx openpyxl python-pptx beautifulsoup4 pillow
# 可选：视频处理
pip install opencv-python
```

### 2. LLM API 配置

在 Claude Code 中说："配置 LLM API"，或手动创建 `~/.claude/skills/data-pipeline/.llm_config.json`：

```json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

## 使用

在 Claude Code 中用自然语言触发：

| 说什么 | 做什么 |
|--------|--------|
| "摄入 /path/to/document.pdf" | 摄入文档到知识维基 |
| "查询 主要主题是什么？" | 查询并多源聚合回答 |
| "检查维基" | 检查孤立页面、断链、矛盾 |
| "构建知识图谱" | 生成交互式知识图谱 |

## 核心能力

- **多模态摄入** — PDF、图片、视频、Word、Excel、PPT、HTML、Markdown
- **知识融合** — 新文档与已有页面智能合并，不覆盖
- **主动矛盾检测** — 摄入后自动对比跨源声明
- **跨源聚合查询** — 多源视角 + 共识与分歧分析
- **知识图谱** — vis.js 交互式可视化

## 开发

同步最新代码到包目录：

```bash
node scripts/sync-skill.mjs
```

发布到 npm：

```bash
cd packages/create-data-pipeline
node scripts/sync-skill.mjs
npm publish
```
