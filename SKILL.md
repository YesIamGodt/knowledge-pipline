---
name: knowledge-pipline
description: "多模态知识管道技能 — 摄入文档(PDF/图片/视频/Office)到持久化知识维基，支持知识融合、跨源矛盾检测、多源聚合查询、知识图谱构建。当用户提到摄入文档、构建知识库、查询维基、检查一致性、构建知识图谱、文档分析、多模态理解、数据管道等需求时触发此技能。即使用户没有明确说 pipeline 或 knowledge-pipline，只要涉及将文档转化为结构化知识、跨文档分析对比、或知识图谱可视化，都应触发此技能。"
---

# Knowledge Pipeline — 多模态知识管道

将任意格式文档摄入为持久化结构化知识维基，支持知识融合、跨源矛盾检测、多源聚合查询。

## 核心能力

| 能力 | 说明 |
|------|------|
| **多模态摄入** | PDF、图片、视频、Word、Excel、PPT、HTML、Markdown |
| **知识融合** | 新文档摄入时自动与已有实体/概念页合并，而非覆盖 |
| **主动矛盾检测** | 摄入后自动对比新旧 claims，报告跨源冲突 |
| **跨源聚合查询** | 查询时展示多源视角、共识与分歧 |
| **知识图谱** | 自动构建交互式 vis.js 可视化图谱 |

---

## 斜杠命令

| 命令 | 说明 |
|------|------|
| `/pipeline-ingest <文件路径>` | 摄入文档到知识维基 |
| `/pipeline-query <问题>` | 多源聚合查询 |
| `/pipeline-lint` | 检查孤立页面、断链、矛盾 |
| `/pipeline-graph` | 构建交互式知识图谱 |
| `/pipeline-config` | 配置 LLM API |

---

## 维基目录

数据统一存放在技能安装目录下（`~/.claude/skills/knowledge-pipline/`）：

```
~/.claude/skills/knowledge-pipline/
├── SKILL.md              # 本文件
├── tools/                # Python 管道脚本
│   ├── pipeline_ingest.py
│   ├── pipeline_query.py
│   ├── pipeline_lint.py
│   ├── pipeline_graph.py
│   ├── pipeline_config.py
│   └── build_graph.py
├── core/                 # 核心模块
│   ├── llm_config.py     # LLM API 配置管理
│   ├── retrieval.py      # BM25 检索引擎
│   ├── wikilink.py       # Wikilink 解析器
│   └── export.py         # 导出功能
├── backend/              # 文件处理器
│   └── processors/       # PDF/图片/视频/Office 处理器
├── .claude/
│   └── commands/         # 斜杠命令定义
│       ├── pipeline-ingest.md
│       ├── pipeline-query.md
│       ├── pipeline-lint.md
│       ├── pipeline-graph.md
│       └── pipeline-config.md
├── wiki/                 # 知识维基（自动创建）
│   ├── index.md
│   ├── log.md
│   ├── overview.md
│   ├── claims.json
│   ├── sources/
│   ├── entities/
│   ├── concepts/
│   └── syntheses/
├── graph/                # 知识图谱输出
│   ├── graph.json
│   └── graph.html
└── raw/                  # 可选：源文档存放
```

---

## LLM 配置（首次使用前必须完成）

运行任何管道命令前，先检查 `.llm_config.json` 是否存在。如果未配置，执行配置向导。

### 配置文件路径

按优先级查找：
1. 技能目录下的 `.llm_config.json`
2. 当前工作目录下的 `.llm_config.json`
3. `LLM_CONFIG_JSON` 环境变量指定的路径

### 配置向导

```bash
python tools/pipeline_config.py
```

或手动创建 `.llm_config.json`：
```json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

常见提供商：

| 提供商 | base_url | 模型示例 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| 火山引擎 | `https://ark.cn-beijing.volces.com/api/coding/v3` | doubao-seed-2-0-pro-260215 |
| Ollama | `http://localhost:11434/v1` | llama3.2 |

---

## 文件路径解析规则

当用户指定文件路径时：

1. **绝对路径**（如 `D:\docs\report.pdf`）→ 直接使用
2. **以 `raw/` 开头** → 相对于技能目录的 `raw/`
3. **其他相对路径** → 相对于当前工作目录（CWD）

---

## 命令：摄入文档

**触发**：用户说“摄入”、“ingest”、“导入文档”、“分析这个文件”等，或使用 `/pipeline-ingest`

### 用法
```
/pipeline-ingest raw/report.pdf
/pipeline-ingest D:\docs\meeting-notes.docx
摄入 ./my-image.jpg
```

### 执行方式

**始终优先使用 Python 脚本**：
```bash
python <skill-dir>/tools/pipeline_ingest.py <文件路径>
```

**PDF 策略**（通过环境变量控制）：
- `PIPELINE_PDF_STRATEGY=balanced`（默认）：文本 + 多图智能理解
- `PIPELINE_PDF_STRATEGY=accurate`：偏准确率（扫描件）
- `PIPELINE_PDF_STRATEGY=fast`：纯文本提取

**图片处理**：优先用 Claude 多模态视觉直接理解；失败时降级到 Python OCR

**视频处理**：OpenCV 关键帧提取 → 多模态 LLM 理解 → 音频转写（如有 ffmpeg）

### 知识融合（核心差异化能力）

摄入时，如果目标实体/概念页面已存在：
- **不会覆盖**，而是用 LLM 合并新旧内容
- 保留已有信息，追加新源信息
- 矛盾处两者都保留，标注 `⚠️ 矛盾`
- 自动更新 frontmatter 的 `sources` 列表

### 主动矛盾检测

摄入完成后自动执行：
- 将新 claims 与 `claims.json` 中所有已有 claims 对比
- 输出跨源矛盾报告和跨源佐证
- 自动记录到 `wiki/log.md`

### 完整流程
1. 处理源文件（多模态）
2. 读取 wiki/index.md 和 overview.md 获取上下文
3. 写入 wiki/sources/<slug>.md
4. **知识融合：合并或创建**实体/概念页面
5. 更新 index.md 和 overview.md
6. 保存 key claims 到 claims.json
7. **主动矛盾检测**：对比新旧 claims
8. 追加 log.md

如果 Python 脚本失败，回退到 Claude 内置能力手动执行上述步骤。

---

## 命令：查询维基

**触发**：用户提问关于已摄入内容的问题、“query”、“查询”等，或使用 `/pipeline-query`

### 用法
```
/pipeline-query transformer 模型的主要创新是什么？
/pipeline-query 所有来源中提到的安全风险
查询 "AI 对就业的影响"
```

### 执行方式
```bash
python <skill-dir>/tools/pipeline_query.py "问题内容"
python <skill-dir>/tools/pipeline_query.py "问题" --auto-save
```

### 跨源聚合（核心差异化能力）

查询结果包含：
- **多源视角**：每个源对同一问题的不同观点
- **共识与分歧**：
  - ✅ 多源共识：多个源一致同意的观点
  - ⚠️ 观点分歧：各源存在不同看法
  - ❓ 单源独有：仅在一个源中出现的论点
- **[[wikilink]]** 引用到具体页面

### 步骤
1. BM25 检索 + 关键词匹配找到相关页面
2. 加载 claims.json 构建跨源视角上下文
3. LLM 综合答案（含多源视角和共识分歧分析）
4. 询问用户是否保存到 wiki/syntheses/

---

## 命令：检查维基

**触发**：用户说“lint”、“检查”、“审计维基”等，或使用 `/pipeline-lint`

### 用法
```
/pipeline-lint
检查维基
lint
```

### 执行方式
```bash
python <skill-dir>/tools/pipeline_lint.py
```

### 检查项
- **孤立页面**：无入链 [[wikilinks]]
- **断链**：指向不存在页面的 [[WikiLink]]
- **矛盾**：跨页面声明冲突（含 claims.json 交叉验证）
- **过时摘要**：新源摄入后未更新的页面
- **缺失实体**：3+ 页面提及但无专属页面的实体
- **数据空白**：建议补充的新源

输出报告后询问是否保存到 wiki/lint-report.md。

---

## 命令：构建知识图谱

**触发**：用户说“build graph”、“构建图谱”、“知识图谱”等，或使用 `/pipeline-graph`

### 用法
```
/pipeline-graph
构建知识图谱
build graph
```

### 执行方式
```bash
python <skill-dir>/tools/build_graph.py --open
```

### 输出
- `graph/graph.json`：节点 + 边 + 社区数据
- `graph/graph.html`：自包含 vis.js 交互式可视化

### 备选方案
如果 Python 不可用，手动：
1. Grep 提取所有 [[wikilinks]]
2. 构建节点/边列表
3. 生成 graph.json + graph.html

---

## 命令：配置 LLM

**触发**：用户说"配置"、"config"、"设置 API"等，或使用 `/pipeline-config`

### 执行方式
```bash
python <skill-dir>/tools/pipeline_config.py
```

或通过交互式问答收集 base_url、model、api_key 后写入 `.llm_config.json`。

---

## 页面格式

每个维基页面使用 YAML frontmatter：

```yaml
---
title: "页面标题"
type: source | entity | concept | synthesis
tags: []
sources: []
last_updated: YYYY-MM-DD
---
```

使用 `[[PageName]]` wikilinks 链接其他页面。

### 命名规范
- Source slug: `kebab-case.md`
- Entity 页面: `TitleCase.md`（如 `OpenAI.md`、`华为云.md`）
- Concept 页面: `TitleCase.md`（如 `RAG.md`、`知识融合.md`）

---

## 设计理念

**持久化知识积累** vs RAG 查询时推导：

| 特性 | 传统 RAG | Knowledge Pipeline |
|------|----------|-------------------|
| 知识存储 | 向量数据库（无结构） | 结构化维基页面 |
| 新文档摄入 | 追加嵌入 | **知识融合**（合并已有页面） |
| 矛盾处理 | 无感知 | **主动检测并报告** |
| 查询 | 相似性检索 | **多源聚合 + 共识分歧分析** |
| 可解释性 | 黑盒 | Wikilinks + 引用溯源 |
| 可视化 | 无 | 交互式知识图谱 |
