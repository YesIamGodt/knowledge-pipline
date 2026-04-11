<div align="center">

# 🧠 Knowledge Pipeline

**别再让 AI 帮你搜索了。让它帮你理解。**

[![npm](https://img.shields.io/npm/v/create-data-pipeline?color=%2300b894&label=npx)](https://www.npmjs.com/package/create-data-pipeline)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

把任何文档丢给它 — PDF、图片、视频、Word、Excel — 它不只是"总结"，而是**编译成结构化知识**，自动发现跨文档矛盾、追踪实体演化、构建可交互的知识图谱。

[快速开始](#-快速开始) · [为什么不直接用 ChatGPT](#-为什么不直接用-chatgpt) · [核心能力](#-核心能力) · [使用场景](#-使用场景) · [示例](#-示例)

</div>

---

## 💡 为什么不直接用 ChatGPT？

> "我把 PDF 丢给 ChatGPT 不就行了？"

行。如果你只有一份文档，只问一次。

但当你有 **50 份文档**，跨越 **3 个月**，涉及 **12 个人物** 和 **8 个核心概念** — ChatGPT 给你的是一个聊天记录，Knowledge Pipeline 给你的是一座**活的知识库**：

| | ChatGPT / Claude 直接问 | Knowledge Pipeline |
|---|---|---|
| 📄 读文档 | 每次会话重新上传 | **一次摄入，永久积累** |
| 🔗 跨文档关联 | 你自己拼凑 | **自动构建实体和概念网络** |
| ⚠️ 矛盾检测 | 从不告诉你 | **摄入时立即报告冲突** |
| 🔄 知识融合 | 不存在 | **新文档自动合并到已有页面** |
| 🧭 多源视角 | 只给一个答案 | **展示每个源的立场 + 共识与分歧** |
| 📊 可视化 | 无 | **交互式知识图谱（vis.js）** |
| 💾 持久化 | 聊天记录（丢了就没了） | **结构化 Markdown 维基** |

**一句话：ChatGPT 是你的对话工具。Knowledge Pipeline 是你的第二大脑。**

---

## 🚀 快速开始

### 方式一：npx 一键安装（推荐）

```bash
npx create-data-pipeline
```

自动安装到 `~/.claude/skills/data-pipeline/`，Claude Code 启动后立即可用。

### 方式二：手动安装

```bash
git clone https://github.com/YesIamGodt/knowledge-pipeline.git
```

将整个目录复制到 `~/.claude/skills/data-pipeline/`，或者直接在项目目录中使用。

### 前置要求

| 依赖 | 说明 |
|------|------|
| **Python 3.9+** | 核心运行环境 |
| **一个多模态 LLM API** | OpenAI / DeepSeek / 火山引擎 / 本地 Ollama 均可 |
| **Claude Code**（推荐）| 作为 Agent 宿主运行技能 |

```bash
# 安装 Python 依赖
pip install openai pymupdf python-docx openpyxl python-pptx beautifulsoup4 pillow

# 可选：视频处理
pip install opencv-python
```

### 配置 LLM API

首次使用时，在 Claude Code 中说 **"配置 LLM API"**，或手动创建配置文件：

```json
// ~/.claude/skills/data-pipeline/.llm_config.json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-your-key-here"
}
```

<details>
<summary>📋 支持的 LLM 提供商</summary>

| 提供商 | base_url | 模型示例 |
|--------|----------|----------|
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| 火山引擎 | `https://ark.cn-beijing.volces.com/api/coding/v3` | doubao-* |
| Together AI | `https://api.together.xyz/v1` | meta-llama/* |
| Ollama（本地） | `http://localhost:11434/v1` | llama3.2 |

</details>

---

## 🔥 核心能力

### 📥 多模态摄入

```bash
# 在 Claude Code 中直接说：
"摄入 /path/to/research-paper.pdf"
"ingest ./meeting-notes.docx"
"摄入 ./product-screenshot.png"
```

| 格式 | 支持 | 处理方式 |
|------|------|----------|
| 📄 PDF | ✅ | 文本 + 表格 + 图片多模态理解 |
| 🖼️ 图片 | ✅ | Claude 多模态视觉 / OCR |
| 🎬 视频 | ✅ | 关键帧提取 + 画面理解 + 音频转写 |
| 📝 Word | ✅ | 文本 + 表格 + 格式 |
| 📊 Excel | ✅ | 多工作表 + 数据清理 |
| 📽️ PPT | ✅ | 幻灯片内容 + 图片 |
| 🌐 HTML | ✅ | 正文提取 |
| 📄 Markdown/Text | ✅ | 直接读取 |

### 🔗 知识融合

**普通工具**：每次摄入覆盖旧内容。

**Knowledge Pipeline**：如果"OpenAI"的实体页面已存在，新文档的信息会被**智能合并**进去 — 保留旧信息、追加新发现、标注矛盾。你的知识只增不减。

### ⚡ 主动矛盾检测

不等你来问。每次摄入新文档后自动扫描：

```
============================================================
📋 主动矛盾检测报告
============================================================
## ⚠️ 矛盾发现
- [paper-A] "GPT-4 在代码生成任务上准确率 92%" 
  与 [paper-B] "GPT-4 代码生成准确率仅 78%" 矛盾
  — 差异可能源于评估基准不同

## ✅ 跨源佐证
- [paper-A] 和 [report-C] 都提到 "RAG 可降低 40% 幻觉率"
  — 增强该观点可信度
============================================================
```

### 🧭 跨源聚合查询

```bash
"查询 transformer 模型的主要创新是什么？"
```

回答不止给你结论，还展示**多源视角**：

```markdown
## 多源视角
- [[attention-paper]]: 注意力机制是核心创新，取代 RNN
- [[bert-paper]]: 预训练 + 微调范式才是关键贡献
- [[gpt-survey]]: 规模定律（Scaling Laws）更为根本

## 共识与分歧
✅ 多源共识：自注意力机制显著提升并行计算效率（3 源佐证）
⚠️ 观点分歧：核心贡献是架构创新还是训练范式（2 源分歧）
❓ 单源独有：混合专家（MoE）可能是下一代架构（仅 1 源）
```

### 📊 知识图谱

```bash
"构建知识图谱"
```

生成自包含的 `graph.html` — 打开浏览器即可交互探索：
- 节点按类型着色（源 / 实体 / 概念）
- 边区分显式链接和推断关系
- Louvain 社区检测自动聚类
- 支持搜索和缩放

---

## 📂 知识库结构

```
wiki/
├── index.md          # 全局索引 — 每次摄入自动更新
├── overview.md       # 活体综述 — 所有源的综合
├── claims.json       # 主张数据库 — 跨源矛盾检测的基础
├── sources/          # 每个源文档一个摘要页
│   ├── attention-is-all-you-need.md
│   └── quarterly-report-q1.md
├── entities/         # 自动生成的实体页面
│   ├── OpenAI.md
│   └── TransformerModel.md
├── concepts/         # 自动生成的概念页面
│   ├── RAG.md
│   └── KnowledgeFusion.md
└── syntheses/        # 查询答案归档
    └── main-innovations.md
```

用 [Obsidian](https://obsidian.md) 打开 `wiki/` 目录 — `[[wikilinks]]` 原生支持，图谱模式即时可用。

---

## 🎯 使用场景

### 🔬 学术研究

```
摄入 paper1.pdf    →  "Transformer 用注意力机制取代 RNN"
摄入 paper2.pdf    →  "BERT 的预训练范式更关键" 
摄入 paper3.pdf    →  "Scaling Laws 才是根本"
查询 "核心创新是什么？"  →  三篇论文的观点对比 + 共识与分歧
构建知识图谱        →  概念关系可视化
```

> 读 50 篇论文后，你拥有的不是 50 个文件，而是一座互相交叉引用的知识体系。

### 📊 竞品分析

```
摄入 openai-blog.md
摄入 anthropic-report.pdf
摄入 google-deepmind-paper.pdf
查询 "三家公司在安全方面的策略对比"
→ 自动展示每家公司的立场、共识点和分歧点
```

### 📚 读书笔记

```
摄入 chapter-01.md   →  主题/人物页面自动创建
摄入 chapter-02.md   →  新信息合并到已有页面
摄入 chapter-10.md   →  自动发现前后矛盾
查询 "主角的动机如何演化？"
```

### 🏢 企业知识库

```
摄入 会议纪要.docx
摄入 客户访谈.pdf
摄入 产品路线图.xlsx
查询 "客户最常提到的需求是什么？"
lint  →  "项目 X 被 5 个文档提及但没有专属页面"
```

---

## 📝 示例：3 分钟感受效果

在 `raw/examples/` 目录中提供了示例文件，体验完整流程：

### 示例 1：单文档摄入

```bash
python tools/pipeline_ingest.py raw/examples/transformer-overview.md

# 输出：
# ✅ 完成。摄入: Transformer Architecture Overview
# 📝 新建 3 个实体/概念页面
```

### 示例 2：多文档矛盾检测

```bash
# 摄入两篇观点不同的文档
python tools/pipeline_ingest.py raw/examples/ai-optimist.md
python tools/pipeline_ingest.py raw/examples/ai-skeptic.md
# → 主动矛盾检测报告自动输出！
```

### 示例 3：跨源聚合查询

```bash
python tools/pipeline_query.py "AI 对就业市场的影响是什么？" --auto-save
# → 展示两篇文章的不同立场 + 共识与分歧分析
```

### 示例 4：在 Claude Code 中用自然语言

```
你：摄入 raw/examples/transformer-overview.md
AI：✅ 完成。摄入: Transformer Architecture Overview  (总耗时 12.3s)
    📝 新建 3 个实体/概念页面

你：查询 注意力机制为什么重要？
AI：## 注意力机制的重要性
    ...（带 [[wikilink]] 引用的结构化回答）...
    ## 共识与分歧
    ✅ 多源共识：自注意力提升并行效率
    
你：构建知识图谱
AI：✅ 图谱已构建。12 节点，18 边，3 个社区
    → 打开 graph/graph.html 查看
```

---

## ⚙️ 命令参考

| 命令 | 说明 |
|------|------|
| `摄入 <文件>` / `ingest <file>` | 摄入文档到知识维基 |
| `查询 <问题>` / `query: <question>` | 多源聚合查询 |
| `检查` / `lint` | 检查孤立页面、断链、矛盾 |
| `构建图谱` / `build graph` | 生成交互式知识图谱 |
| `配置` / `config` | 配置 LLM API |

### Python CLI

也可脱离 Claude Code 独立使用：

```bash
python tools/pipeline_ingest.py <file>            # 摄入
python tools/pipeline_query.py "<question>"        # 查询
python tools/pipeline_query.py "<q>" --auto-save   # 查询并自动保存
python tools/pipeline_lint.py                      # 检查
python tools/build_graph.py                        # 构建图谱
python tools/pipeline_config.py                    # 配置
```

### 环境变量

```bash
PIPELINE_PDF_STRATEGY=fast|balanced|accurate  # PDF 处理策略
LLM_CONFIG_JSON=/path/to/.llm_config.json     # 自定义配置路径
```

---

## 🏗️ 架构

```
┌─────────────────────────────────────────────────────────┐
│                    用户（自然语言）                        │
├─────────────────────────────────────────────────────────┤
│                    Claude Code Agent                     │
│              读取 SKILL.md / CLAUDE.md 指令               │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  Ingest  │  Query   │   Lint   │  Graph   │   Config     │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│  BM25 检索 │ Wikilink 解析 │ Claims DB │ 知识融合引擎    │
├─────────────────────────────────────────────────────────┤
│  多模态处理器（PDF / 图片 / 视频 / Office / HTML）        │
├─────────────────────────────────────────────────────────┤
│               LLM API (OpenAI-compatible)                │
└─────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕
    wiki/ (Markdown)    claims.json         graph/graph.html
```

---

## 🤝 贡献

欢迎 PR 和 Issue。

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
