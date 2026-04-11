<div align="center">

# 🧠 Knowledge Pipline

**别再让 AI 帮你搜索了。让它帮你理解。**

[English](README_EN.md) | 中文

[![GitHub](https://img.shields.io/github/stars/YesIamGodt/knowledge-pipline?style=social)](https://github.com/YesIamGodt/knowledge-pipline)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/npx%20skills%20add-knowledge--pipline-00b894)](https://skills.sh)

把任何文档丢给它 — PDF、图片、视频、Word、Excel — 它不只是"总结"，而是**编译成结构化知识**，自动发现跨文档矛盾、追踪实体演化、构建可交互的知识图谱。

[快速开始](#-快速开始) · [为什么不直接用 ChatGPT](#-为什么不直接用-chatgpt) · [核心能力](#-核心能力) · [使用场景](#-使用场景) · [示例](#-示例)

</div>

---

## 💡 为什么不直接用 ChatGPT？

> "我把 PDF 丢给 ChatGPT 不就行了？"

行。如果你只有一份文档，只问一次。

但当你有 **50 份文档**，跨越 **3 个月**，涉及 **12 个人物** 和 **8 个核心概念** — ChatGPT 给你的是一个聊天记录，Knowledge Pipline 给你的是一座**活的知识库**：

| | ChatGPT / Claude 文件上传（RAG） | Knowledge Pipline |
|---|---|---|
| 📄 读文档 | 每次会话重新上传，不积累 | **一次摄入，永久积累** |
| 🔗 跨文档关联 | 只检索相关片段拼接 | **自动构建实体和概念网络** |
| ⚠️ 矛盾检测 | 不会主动发现矛盾 | **摄入时立即报告冲突** |
| 🔄 知识融合 | 不存在，每次独立检索 | **新文档自动合并到已有页面** |
| 🧭 多源视角 | 只给一个综合答案 | **展示每个源的立场 + 共识与分歧** |
| 📊 可视化 | 无 | **交互式知识图谱（vis.js）** |
| 💾 中间表示 | 黑盒向量，不可浏览 | **结构化 Markdown 维基（Obsidian 兼容）** |

**一句话：ChatGPT 是你的对话工具。Knowledge Pipline 是你的第二大脑。**

### 🎯 真实案例：深层模式挖掘

我们把 18 份真实文档丢进来 — 医学病例报告、计算机硕士论文、Claude Code 源码泄露事件、香港街景照片、音乐会视频 — 领域跨得够远了吧？

然后问一个**没有任何文档直接讨论过**的问题：

> **"AI 在 2026 年真的会引起程序员失业吗？"**

**RAG（ChatGPT/Claude 文件上传）的做法：**
检索和"程序员失业"最相关的文本片段 — 但 18 份文档里没有一份在讨论这个话题。RAG 检索不到相关段落，只能用模型自身知识泛泛而谈。

**Knowledge Pipline 的做法：**

```
你：/pipline-ingest D:\docs\raw
AI：✅ 批量摄入完成
    📝 18 个源文档 → 23 个实体页面 + 36 个概念页面
    ⚠️ 发现 3 处跨源矛盾

你：/pipline-query AI在2026年真的会引起程序员失业吗？详细回答
```

它不检索文本碎片 — 它在已经编译好的**概念网络和实体关系**中发现深层模式：

```markdown
## AI 对程序员就业的影响（基于维基知识库分析）

### 深层模式发现

1. **"可自动化"与"不可自动化"的分界线**
   两篇硕士论文（[[group-fusion-method]] [[gnn-based-multi-behavior]]）的核心工作
   是实现算法：MBWGCN 模型、MaxQ/MaxS 群组融合算法、图神经网络训练流程。
   这些工作的本质是"把数学公式翻译成代码" — 恰恰是 AI 编程工具最擅长的事。
   
   但同一批论文中，**问题的发现和建模** — 比如意识到"需求间的相似度是不对称的"
   （[[不对称相似度]]），比如将推荐系统建模为多行为图结构 — 这种创造性洞察
   目前无法被自动化。

2. **AI 编程工具已经是一门大生意**
   [[Claude Code]] 源码泄露事件揭示：这是一个 ARR 25 亿美元的产品，
   内部有 KAIROS（守护进程）、ULTRAPLAN（云端规划）等未发布功能。
   说明 AI 编程工具不是实验室玩具，而是已经在大规模替代开发工作量。
   
   但泄露事件本身（[[SupplyChainSecurity]]）也证明：生产环境的工程判断 —
   "该不该在 .npmignore 里排除 source map" — 这种上下文感知的决策，AI 自己
   都还会犯错。

3. **跨领域的验证：医学 vs 编程**
   医学病例报告（[[RonT综合征]] [[室性早搏]]）中，临床医生面对心律失常时的
   判断过程 — 联律间期是否固定、是否需要利多卡因 — 完全依赖经验和上下文。
   这与"高级程序员判断系统架构"是同构的：**需要上下文推理的工作不会消失，
   只需要执行的工作会被替代。**

### 综合判断

不会"失业"，但会"分层淘汰"：
- ✅ 共识：算法实现、数据处理等"翻译性编码"将大幅减少（论文编码工作 = AI 最佳替代目标）
- ⚠️ 分歧：问题建模和创造性洞察目前安全（不对称相似度的发现无法自动化）
- ❓ 信号：AI 工具自身仍有工程盲区（source map 泄露 = AI 不能替代工程判断）
```

**为什么 RAG 做不到这一点？**

因为 RAG 的工作方式是"检索文本片段" — 它去向量库里找和"程序员失业"最相似的段落。但这 18 份文档里没有任何段落在讨论程序员失业，RAG 检索不到有用的内容。

Knowledge Pipline 能回答，是因为摄入时已经把文档编译成了**结构化的概念网络**：

- 论文里的 MBWGCN 代码实现 → 概念页面 [[图神经网络]]、[[服务计算]] 
- Claude Code 的 ARR 数据 → 实体页面 [[Claude Code]]、概念页面 [[SupplyChainSecurity]]
- 心律失常的临床判断 → 概念页面 [[RonT综合征]]、[[联律间期]]

查询时，系统不是在文本碎片中搜索 — 它在概念和实体页面之间**推理**：论文的"编码工作"和 Claude Code 的"AI 编程能力"通过概念网络连接在一起，医学的"临床判断"和工程的"架构决策"通过"上下文推理"这个共同特征关联。

**这就是本质区别：RAG 在文档碎片中搜索答案，Knowledge Pipline 在知识体系中推理答案。**

---

## 🚀 快速开始

### 方式一：npx skills add 一键安装（推荐）

```bash
npx skills add YesIamGodt/knowledge-pipline
```

自动安装到 `~/.agents/skills/knowledge-pipline/`（并 symlink 到 `~/.claude/skills/`），Claude Code 启动后立即可用。

#### 安装斜杠命令（重要！）

`npx skills add` 会安装技能文件，但**不会自动注册斜杠命令**。安装后运行：

**Windows（CMD）：**
```cmd
node "%USERPROFILE%\.agents\skills\knowledge-pipline\scripts\install-commands.mjs"
```

**Windows（PowerShell）：**
```powershell
node "$HOME\.agents\skills\knowledge-pipline\scripts\install-commands.mjs"
```

**macOS / Linux：**
```bash
node ~/.agents/skills/knowledge-pipline/scripts/install-commands.mjs
```

这会将五个斜杠命令注册到 `~/.claude/commands/`，让你可以在任何项目中使用 `/pipline-config`、`/pipline-ingest`、`/pipline-query`、`/pipline-graph`、`/pipline-lint`。

### 方式二：手动安装

```bash
git clone https://github.com/YesIamGodt/knowledge-pipline.git
cd knowledge-pipline
node scripts/install-commands.mjs
```

将仓库 clone 到本地，运行安装脚本注册斜杠命令。

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

首次使用时，在 Claude Code 中运行 **`/pipline-config`**，按交互向导配置 LLM API。

或手动创建配置文件：

```json
// ~/.claude/skills/knowledge-pipline/.llm_config.json
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

```
/pipline-ingest /path/to/research-paper.pdf
/pipline-ingest ./meeting-notes.docx
/pipline-ingest ./product-screenshot.png
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

**Knowledge Pipline**：如果"OpenAI"的实体页面已存在，新文档的信息会被**智能合并**进去 — 保留旧信息、追加新发现、标注矛盾。你的知识只增不减。

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

```
/pipline-query "transformer 模型的主要创新是什么？"
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

```
/pipline-graph
```

生成自包含的 `graph.html` — 打开浏览器即可交互探索：
- 节点填充色按类型着色（源 / 实体 / 概念）
- 节点边框色按社区聚类着色（Louvain 检测）
- 边区分显式链接和推断关系
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
/pipline-ingest paper1.pdf     →  "Transformer 用注意力机制取代 RNN"
/pipline-ingest paper2.pdf     →  "BERT 的预训练范式更关键" 
/pipline-ingest paper3.pdf     →  "Scaling Laws 才是根本"
/pipline-query "核心创新是什么？"  →  三篇论文的观点对比 + 共识与分歧
/pipline-graph                  →  概念关系可视化
```

> 读 50 篇论文后，你拥有的不是 50 个文件，而是一座互相交叉引用的知识体系。

### 📊 竞品分析

```
/pipline-ingest openai-blog.md
/pipline-ingest anthropic-report.pdf
/pipline-ingest google-deepmind-paper.pdf
/pipline-query "三家公司在安全方面的策略对比"
→ 自动展示每家公司的立场、共识点和分歧点
```

### 📚 读书笔记

```
/pipline-ingest chapter-01.md   →  主题/人物页面自动创建
/pipline-ingest chapter-02.md   →  新信息合并到已有页面
/pipline-ingest chapter-10.md   →  自动发现前后矛盾
/pipline-query "主角的动机如何演化？"
```

### 🏢 企业知识库

```
/pipline-ingest 会议纪要.docx
/pipline-ingest 客户访谈.pdf
/pipline-ingest 产品路线图.xlsx
/pipline-query "客户最常提到的需求是什么？"
/pipline-lint  →  "项目 X 被 5 个文档提及但没有专属页面"
```

---

## 📝 示例：真实使用流程

### 示例 1：批量摄入 — 一次丢进去，永久积累

```
你：/pipline-ingest D:\docs\raw
AI：✅ 批量摄入完成 (18个文件)
    📄 sources: 硕士论文×4, 安全审计×3, 事件报告×2, RAG技术×1, 照片×3, 视频×1 ...
    🧑 entities: 23 个 (华为云, Anthropic, 林加锋, 汤涛, 南京邮电大学 ...)
    💡 concepts: 36 个 (RAG, 群组融合, 安全审计, 室性早搏, 图神经网络 ...)
    ⚠️ 矛盾: 3 处跨源声明冲突
```

### 示例 2：跨领域查询 — 答案来自你自己的文档

```
你：/pipline-query AI在2026年真的会引起程序员失业吗？
AI：## AI 对程序员就业的影响

    ### 来自维基的直接证据
    1. [[claude-code-leak]]: Claude Code ARR 已达 25 亿美元，AI 编程工具大规模商用
    2. [[group-fusion-method]]: 学术论文的编码工作正是 AI 最擅长替代的部分
    3. [[security-incident-brief]]: 安全审计仍需人工对业务上下文的深度理解
    
    ### 综合判断
    ✅ 共识：初级编码工作将大幅减少
    ⚠️ 分歧：高级系统设计是否受影响
    ❓ 未知：AI 原生开发范式何时成为主流
```

### 示例 3：构建知识图谱

```
你：/pipline-graph
AI：📊 图谱统计:
       提取边: 289 条 (来自 [[wikilinks]])
       推断边: 81 条 (LLM 语义推断)
       总  计: 370 条边, 80 个节点, 6 个社区
    ✅ 图谱构建完成 → 打开 graph/graph.html 查看
```

### 示例 4：维基健康检查

```
你：/pipline-lint
AI：🏥 维基健康报告
    ❌ 断链 2 处: [[不存在的页面]]
    ⚠️ 孤立页面 1 个: concepts/都市景观.md
    💡 建议: "华为" 在 5 个页面被引用但缺少专属实体页面
```

---

## ⚙️ 命令参考

安装后，你将获得 **五个核心斜杠命令**，在 Claude Code 任意项目中可用：

### ⚙️ `/pipline-config` — 配置 LLM API

配置知识管道使用的 LLM API 信息。**首次使用前必须运行。**

```bash
/pipline-config
```

交互向导引导你：
- 选择提供商（OpenAI / 自定义兼容端点 / Ollama）
- 输入 base_url、模型名称、API 密钥
- 配置保存到技能目录下的 `.llm_config.json`

### 📥 `/pipline-ingest` — 摄入文档

将文档摄入到知识维基。支持 PDF、图片、视频、Word、Excel、PPT、HTML、Markdown 等格式。

```bash
/pipline-ingest "D:\docs\research-paper.pdf"
/pipline-ingest "/home/user/meeting-notes.docx"
/pipline-ingest "C:\Users\me\Desktop\screenshot.png"
```

**必须使用绝对路径**。摄入时自动执行：
- 解析多模态内容（文本 + 图片 + 表格）
- 知识融合：新信息合并到已有实体/概念页面
- 主动矛盾检测：与已有 claims 对比，报告冲突
- 更新索引、概览、日志

### 🔍 `/pipline-query` — 查询维基

基于已摄入的文档进行多源聚合查询。

```bash
/pipline-query "transformer 模型的核心创新是什么？"
/pipline-query "各来源对 AI 安全的观点有什么分歧？"
```

查询结果包含：
- **多源视角**：每个源文档对同一问题的不同观点
- **共识与分歧**：多源一致 ✅ / 观点分歧 ⚠️ / 单源独有 ❓
- **[[wikilink]]** 引用到具体页面

### 📊 `/pipline-graph` — 构建知识图谱

生成交互式 vis.js 知识图谱可视化。

```bash
/pipline-graph
```

输出：
- `graph/graph.json` — 节点 + 边 + 社区数据
- `graph/graph.html` — 浏览器打开即可交互探索

### 🏥 `/pipline-lint` — 维基健康检查

检查知识维基的完整性和一致性。

```bash
/pipline-lint
```

检查项：
- **孤立页面** — 无入链的页面
- **断链** — 指向不存在页面的 [[wikilink]]
- **矛盾** — 跨页面声明冲突
- **缺失实体** — 被多次提及但无专属页面
- **数据空白** — 建议补充的新源

### 自然语言触发（也支持）

| 说什么 | 等同于 |
|------|------|
| `配置 LLM API` / `configure` | `/pipline-config` |
| `摄入 <文件>` / `ingest <file>` | `/pipline-ingest` |
| `查询 <问题>` / `query: <question>` | `/pipline-query` |
| `构建图谱` / `build graph` | `/pipline-graph` |
| `检查` / `lint` | `/pipline-lint` |

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
