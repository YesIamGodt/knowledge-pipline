# LLM Pipeline Agent — 架构和工作流说明

这个维基完全由 Claude Code 维护。不需要 API 密钥或 Python 脚本 — 只需在 Claude Code 中打开此仓库并与它对话即可。

---

## LLM 配置检查（关键 - 第一步）

**在执行任何管道命令之前，你必须检查 LLM 是否已配置：**

1. 检查 `.llm_config.json` 是否存在：
   - **如果存在**：读取并验证它包含 `base_url`、`model`、`api_key`
   - **如果不存在**：继续下面的配置提示

2. 同时检查 `.claude_settings.json` 是否存在（可选，用于 Python 工具）：
   - 如果 Python 工具命令需要但找不到 Python，同样需要配置

### 配置提示

当用户在没有配置的情况下运行 `/pipeline-ingest`、`/pipeline-query`、`/pipeline-graph`、`/pipeline-ppt`（任何依赖 LLM 的命令）时：

1. **显示清晰的消息：**
   ```
   ⚠️ LLM 未配置。要使用维基命令，您需要配置您的 LLM API。
   ```

2. **询问用户是否需要运行配置：**
   - **问题**：“是否需要运行 `/pipeline-config` 进行配置？”
   - **选项**：「是，运行配置」、「否，稍后再说」

3. **如果用户选择「是」：**
   - 立即执行 `/pipeline-config` 命令
   - 配置完成后，询问用户是否继续执行原始命令

4. **如果用户选择「否」：**
   - 提示用户稍后可以随时运行 `/pipeline-config` 进行配置
   - 停止执行当前命令

### 配置文件格式

`.llm_config.json`:
```json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

### 快速参考：常见提供商

| 提供商 | 基础 URL | 模型示例 |
|--------|----------|---------------|
| OpenAI | https://api.openai.com/v1 | gpt-4o-mini |
| DeepSeek | https://api.deepseek.com/v1 | deepseek-chat |
| Together AI | https://api.together.xyz/v1 | meta-llama/Llama-3-8b-chat-hf |
| Ollama (本地) | http://localhost:11434/v1 | llama3.2 |

---

## 管道配置

触发方式：*"重新配置 LLM"* 或 `/pipeline-config`

**功能**: 重新配置 LLM API 信息，支持以下提供商：

1. **OpenAI** - 默认选项 (https://api.openai.com/v1)
2. **自定义 OpenAI 兼容端点** - 如 DeepSeek、Together AI、Anthropic 等
3. **Ollama** - 本地模型服务 (http://localhost:11434/v1)

**配置流程**:
1. 显示当前配置状态（如果已配置）
2. 使用 AskUserQuestion 收集新的配置信息
3. 验证配置的正确性
4. 保存到 `.llm_config.json`
5. 更新环境变量以立即生效
6. 验证新配置是否正常工作

---

## 斜杠命令 (Claude Code)

| 命令 | 用法 |
|---|---|
| `/pipeline-config` | `重新配置 LLM API` |
| `/pipeline-ingest` | `摄入 raw/my-article.md` |
| `/pipeline-query` | `query: 主要主题是什么？` |
| `/pipeline-lint` | `检查维基` |
| `/pipeline-graph` | `构建知识图谱` |
| `/pipeline-ppt` | `生成 Live PPT 演示文稿` |

或者直接用自然语言描述你的需求：
- *"摄入这个文件：raw/papers/attention-is-all-you-need.md"*
- *"维基里关于 transformer 模型的内容是什么？"*
- *"检查维基中的孤立页面和矛盾之处"*
- *"构建图谱并告诉我与 RAG 相关的内容"*
- *"帮我做一个安全分析的 PPT"*

Claude Code 会自动读取此文件并按照下面的工作流执行。

---

## 目录结构

```
raw/          # 不可变的源文档 — 不要修改这些
wiki/         # Claude 完全拥有这一层
  index.md    # 所有页面的目录 — 每次摄入时更新
  log.md      # 仅追加的时间顺序记录
  overview.md # 跨所有源的活体综合内容
  sources/    # 每个源文档一个摘要页面
  entities/   # 人物、公司、项目、产品
  concepts/   # 思想、框架、方法、理论
  syntheses/  # 保存的查询答案
graph/        # 自动生成的图谱数据
tools/        # 可选的独立 Python 脚本（需要 LLM API 密钥）
```

---

## 页面格式

每个维基页面都使用以下 frontmatter：

```yaml
---
title: "Page Title"
type: source | entity | concept | synthesis
tags: []
sources: []       # list of source slugs that inform this page
last_updated: YYYY-MM-DD
---
```

Use `[[PageName]]` wikilinks to link to other wiki pages.

---

## 摄入工作流

触发方式：*"摄入 <文件>"* 或 `/pipeline-ingest`

**前置条件**：运行 LLM 配置检查（见上文）。如果未配置，请先完成配置。

步骤（按顺序）：
1. **处理源文件**（支持多种格式）：
   - **文本文件** (.md, .txt): 直接读取
   - **PDF 文档** (.pdf): 使用 pypdf 提取文本
   - **Word 文档** (.docx): 使用 python-docx 提取文本和表格
   - **Excel 表格** (.xlsx): 使用 openpyxl 提取工作表为表格
   - **PowerPoint** (.pptx): 提取幻灯片内容
   - **HTML 文件** (.html, .htm): 使用 BeautifulSoup/Trafilatura 提取主要内容
   - **图片** (.jpg, .png, .webp): **首先使用 Read 工具**（Claude Code 内置多模态视觉 — 直接理解图片内容）。只有当 Read 工具失败时才降级到 Python OCR。

   **图片处理（重要 — 始终按此顺序执行）**：
   1. 使用 **Read 工具** 读取图片文件路径 — Claude Code 可以原生"看到"并描述图片
   2. 阅读图片描述并转录所有可见文字
   3. 注意关键视觉元素：人物、地点、物体、UI 布局、文档、图表等
   4. 只有当 Read 工具失败时，才回退到 `FileProcessor` / PaddleOCR

   **Python 处理器回退方案**：
   ```python
   from backend.processors import FileProcessor
   
   processor = FileProcessor()
   result = processor.process(file_path)
   content = result.content  # 提取的文本
   metadata = result.metadata  # 文件信息
   tables = result.tables  # 提取的表格（如果有）
   ```

2. 读取 `wiki/index.md` 和 `wiki/overview.md` 获取当前维基上下文
3. 编写 `wiki/sources/<slug>.md` — 使用下面的源页面格式
4. 更新 `wiki/index.md` — 在 Sources 部分添加条目
5. 更新 `wiki/overview.md` — 如有需要，修订综合内容
6. 更新/创建关键人物、公司、项目提及的实体页面
7. 更新/创建关键思想和框架的概念页面
8. 标记与现有维基内容的任何矛盾
9. 追加到 `wiki/log.md`：`## [YYYY-MM-DD] ingest | <标题>`

### 源页面格式

```markdown
---
title: "Source Title"
type: source
tags: []
date: YYYY-MM-DD
source_file: raw/...
---

## Summary
2–4 sentence summary.

## Key Claims
- Claim 1
- Claim 2

## Key Quotes
> "Quote here" — context

## Connections
- [[EntityName]] — how they relate
- [[ConceptName]] — how it connects

## Contradictions
- Contradicts [[OtherPage]] on: ...
```

---

## 查询工作流

触发方式：*"query: <问题>"* 或 `/pipeline-query`

**前置条件**：运行 LLM 配置检查（见上文）。如果未配置，请先完成配置。

步骤：
1. 读取 `wiki/index.md` 识别相关页面
2. 使用 Read 工具读取这些页面
3. 使用 `[[页面名称]]` wikilinks 作为内联引用综合答案
4. 询问用户是否要将答案保存为 `wiki/syntheses/<slug>.md`

---

## 检查工作流

触发方式：*"检查维基"* 或 `/pipeline-lint`

使用 Grep 和 Read 工具检查：
- **孤立页面** — 没有其他页面的入站 `[[链接]]` 的维基页面
- **损坏的链接** — 指向不存在页面的 `[[WikiLinks]]`
- **矛盾之处** — 跨页面的冲突声明
- **过时的摘要** — 在新源之后未更新的页面
- **缺失的实体页面** — 在 3+ 页面中提及但没有自己页面的实体
- **数据空白** — 维基无法回答的问题；建议新源

输出检查报告并询问用户是否要将其保存到 `wiki/lint-report.md`。

---

## 图谱工作流

触发方式：*"构建知识图谱"* 或 `/pipeline-graph`

**前置条件**：运行 LLM 配置检查（见上文）。如果未配置，请先完成配置。

当用户要求构建图谱时，运行 `tools/build_graph.py`，它会：
- 第一遍：解析所有 `[[wikilinks]]` → 确定性的 `EXTRACTED` 边
- 第二遍：推断隐含关系 → 带置信度分数的 `INFERRED` 边
- 运行 Louvain 社区检测
- 输出 `graph/graph.json` + `graph/graph.html`

**IMPORTANT**: 使用配置的 Python 路径来运行：
1. 首先检查 `.claude_settings.json` 中的 `python_path` 配置
2. 如果没有配置，提示用户运行 `/pipeline-config` 配置 Python 路径
3. 如果配置了但无法运行，使用 Claude Code 手动构建图谱：
   - 读取所有维基页面
   - 识别所有 `[[wikilinks]]`
   - 构建节点和边列表
   - 直接生成 `graph/graph.json` 和 `graph/graph.html`

---

## 命名规范

- 源 slug：与源文件名匹配的 `kebab-case`
- 实体页面：`TitleCase.md`（例如 `OpenAI.md`、`SamAltman.md`）
- 概念页面：`TitleCase.md`（例如 `ReinforcementLearning.md`、`RAG.md`）
- 源页面：`kebab-case.md`

## 索引格式

```markdown
# Wiki Index

## Overview
- [概览](overview.md) — 活体综合内容

## Sources
- [源标题](sources/slug.md) — 单行摘要

## Entities
- [实体名称](entities/EntityName.md) — 单行描述

## Concepts
- [概念名称](concepts/ConceptName.md) — 单行描述

## Syntheses
- [分析标题](syntheses/slug.md) — 它回答的问题
```

## 日志格式

每个条目以 `## [YYYY-MM-DD] <操作> | <标题>` 开头，以便用 grep 解析：

```
grep "^## \[" wiki/log.md | tail -10
```

操作：`ingest`、`query`、`lint`、`graph`
