<div align="center">

# 🧠 Knowledge Pipeline

**你的文档不该只是"被总结"。它们该被编译成一座可推理的知识体系。**

[English](README_EN.md) | 中文

[![GitHub](https://img.shields.io/github/stars/YesIamGodt/knowledge-pipline?style=social)](https://github.com/YesIamGodt/knowledge-pipline)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/npx%20skills%20add-knowledge--pipline-00b894)](https://skills.sh)

一个 Claude Code 技能 — 把 PDF、图片、Word、Excel、视频丢给它，自动编译成结构化 Markdown 维基 + 交互式知识图谱。  
跨文档矛盾检测、知识融合、深度推理链 — 不只是检索，而是**推理**。

[快速开始](#-快速开始) · [Live PPT 旗舰功能](#-live-ppt--知识驱动的演示文稿旗舰功能) · [谁需要这个](#-谁需要这个) · [对比竞品](#-对比竞品) · [核心能力](#-核心能力)

</div>

---

## 📑 Live PPT — 知识驱动的演示文稿（🚀 旗舰功能）

> **问题**：Gemini、GPT、Gamma 这些工具能生成漂亮幻灯片。但把一份 200 页审计报告丢给它们？它们只会泛泛而谈。因为它们不"理解"你的文档 — 只是在拼凑模型通用知识。
>
> **解决**：`/pipeline-ppt` 的输入不是一句提示词 — 是你的**整座知识库**。18 份文档编译成的实体网络、概念关系、矛盾检测结果，全部成为幻灯片的内容来源。

```
/pipeline-ppt "AI安全趋势分析"
/pipeline-ppt "竞品对比" --template 3 --pages 10
```

**核心能力**：
- 🧠 **知识库驱动** — 自动从 wiki 实体/概念/矛盾中提取要点，不是从通用知识里编
- 🎨 **8 种内置模板** — 覆盖商务、科技、学术等场景，一键选择
- 📤 **PPTX 导出** — 浏览器一键导出，文本可编辑（不是截图）
- ✏️ **自然语言编辑** — "第 3 页加一个竞品对比表格"，实时更新，不破坏其他页
- 📖 **来源可追溯** — 每张幻灯片标注知识来源，支持审计
- 📐 **智能排版** — 内容过多自动缩放，不会溢出截断
- ⌨️ **键盘导航** — ←→ 翻页 · F 全屏 · Home/End 首尾页

> **别人用 AI 做"好看的幻灯片"。你用 Knowledge Pipeline 做"有洞察的分析报告"。**

---

## 🎯 谁需要这个？

> 如果你遇到以下场景，Knowledge Pipeline 就是为你设计的。

### 场景一：文档越多，你越迷茫

你读了 30 篇论文，记了笔记、标注了重点 — 但三个月后想找"A 和 B 论文对某问题到底有没有矛盾"时，你只能一篇篇重新翻。**ChatGPT 和 NotebookLM 解决不了这个问题 — 它们是无状态的，每次会话从零开始。**

→ Knowledge Pipeline 每次摄入自动合并到已有知识网络，累积不丢失，矛盾检测实时触发。

### 场景二：你的问题跨越多份文档、多个领域

你想知道"这 5 份审计报告的安全策略有什么异同？"或者"医学文献里的临床判断模式，与工程架构决策有什么共通之处？" — 答案分散在不同文档中，没有任何一篇在直接讨论你的问题。

→ RAG 只能检索文本片段拼接。Knowledge Pipeline 在编译好的概念网络中**推理出答案**，即使没有文档直接讨论这个话题。

### 场景三：你需要透明可审计的知识中间层

你不信任黑盒向量数据库 — 你需要看到知识是怎么组织的，需要能浏览每个实体和概念页面，需要手动修正 AI 的判断。

→ 所有知识存储为结构化 Markdown（Obsidian 兼容），可浏览、可编辑、可版本控制。没有黑盒。

### 场景四：你需要本地化 + 完全可控

你不想把数据发到 Google 或 OpenAI 的服务器。你需要选择自己的 LLM 提供商，甚至用本地 Ollama。

→ 完全本地运行，支持任何 OpenAI 兼容 API（DeepSeek、火山引擎、Together AI、Ollama 等）。

---

## ⚔️ 对比竞品

### vs ChatGPT / Claude 文件上传

| | ChatGPT / Claude 文件上传 | Knowledge Pipeline |
|---|---|---|
| 📄 知识积累 | 每次会话重新上传，不积累 | **一次摄入，永久积累** |
| 🔗 跨文档关联 | 只检索相关片段拼接 | **自动构建实体和概念网络** |
| ⚠️ 矛盾检测 | 不会主动发现矛盾 | **摄入时立即报告冲突** |
| 🔄 知识融合 | 不存在，每次独立 | **新文档自动合并到已有页面** |
| 🧭 多源视角 | 只给一个综合答案 | **展示每个源的立场 + 共识与分歧** |
| 💾 中间表示 | 黑盒，用户不可见 | **Markdown 维基，可浏览可编辑** |

### vs Google NotebookLM

| | NotebookLM | Knowledge Pipeline |
|---|---|---|
| 🌐 运行位置 | Google 云端，数据上传到 Google | **本地运行，数据不出机** |
| 🔧 LLM 选择 | 仅 Google Gemini | **任意 OpenAI 兼容 API / 本地 Ollama** |
| ⚠️ 矛盾检测 | 无 | **主动跨源矛盾检测** |
| 🔗 知识融合 | 无，源文档独立 | **自动实体/概念合并** |
| 📊 知识图谱 | 无 | **交互式 vis.js 图谱 + 社区检测** |
| 🧠 推理链 | 无 | **BFS 深度推理链 + 可视化** |
| 📁 可导出性 | 锁定在 Google 生态 | **纯 Markdown 文件，Obsidian/Git 兼容** |
| 📦 格式支持 | PDF、文本、网页 | **PDF/图片/视频/Word/Excel/PPT/HTML** |

### vs 传统 RAG（LangChain / LlamaIndex）

| | 传统 RAG | Knowledge Pipeline |
|---|---|---|
| 工作原理 | 切片 → 向量化 → 检索相似片段 | **编译 → 结构化知识网络 → 推理** |
| 回答依据 | 文本碎片相似度匹配 | **概念网络中的关系推理** |
| 跨文档能力 | 弱 — 只是把更多碎片扔进上下文 | **强 — 实体/概念页面跨源自动合并** |
| 矛盾处理 | 不感知，可能给出矛盾答案 | **主动检测并报告** |
| 中间表示 | 向量数据库（不可读） | **Markdown 维基（人类可读可编辑）** |
| 开发成本 | 需要写代码搭 pipeline | **5 个斜杠命令，零代码** |
| 新文档适配 | 需要重新索引 | **增量摄入，自动融合** |

**一句话总结：**
- **ChatGPT/Claude** = 对话工具，每次从零开始
- **NotebookLM** = 文档阅读器，单项目单次使用，锁定 Google
- **传统 RAG** = 搜索引擎，在碎片中查找
- **Knowledge Pipeline** = 知识编译器，把文档编译成可推理的知识体系

### vs AI PPT 工具（Gemini / GPT / Gamma / Beautiful.ai）

> 为什么单独拎出来比？因为"AI 做 PPT"是当前最火的应用场景之一，但市面上的工具都**解决错了问题** — 它们在比谁的模板更好看，而不是比谁的内容更有深度。

| | Gemini / GPT / Gamma 等 | Knowledge Pipeline LivePPT |
|---|---|---|
| 📄 内容来源 | 用户输入的一句提示词 | **知识库：多份文档 → 实体网络 → 概念图谱** |
| 🧠 分析深度 | 模型通用知识，泛泛而谈 | **你自己文档中的真实数据和洞察** |
| ⚠️ 矛盾处理 | 不感知，可能自相矛盾 | **自动检测跨源矛盾，标注分歧** |
| 📖 来源追溯 | 无来源标注 | **每页标注 Wiki 来源，老板问"依据呢"你有答案** |
| ✏️ 编辑方式 | 重新生成整副幻灯片 | **自然语言逐页实时编辑，不破坏其他页** |
| 📤 导出 | PDF / 图片（不可编辑） | **PPTX（可编辑文本框 + 高清背景图）** |
| 🎨 模板 | 平台固定模板 | **8 种内置主题，一键选择** |
| 💰 成本 | $20–40/月订阅 | **免费开源，用自己的 LLM** |

**AI PPT 工具给你"漂亮的幻灯片"。Knowledge Pipeline 给你"有深度的分析报告"。**

---

## 🎯 30 秒看懂核心价值

```
你：丢进去 18 份文档（论文 + 审计报告 + 新闻 + 照片 + 视频）
AI：✅ 编译完成 → 23 个实体页面 + 36 个概念页面 + 3 处矛盾

你：问一个没有任何文档直接讨论的问题 —
    "AI 在 2026 年真的会引起程序员失业吗？"

RAG 做法：搜索"程序员失业"相关文本碎片 → 找不到 → 用自身知识泛泛而谈
KP 做法：在概念网络中推理 →
    • 论文的"算法编码"+ Claude Code 的"25亿美元 ARR" → AI 正在大规模替代编码工作
    • 论文的"不对称相似度发现"= 创造性洞察 → 无法被自动化
    • 医学的"临床判断"≈ 工程的"架构决策" → 需要上下文推理的工作不会消失

结论：不是"失业"，而是"分层淘汰" — 带引用、带推理链、带知识图谱可视化
```

**本质区别：RAG 在文档碎片中搜索答案，Knowledge Pipeline 在知识体系中推理答案。**

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

这会将五个斜杠命令注册到 `~/.claude/commands/`，让你可以在任何项目中使用 `/pipeline-config`、`/pipeline-ingest`、`/pipeline-query`、`/pipeline-graph`、`/pipeline-lint`。

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

首次使用时，在 Claude Code 中运行 **`/pipeline-config`**，按交互向导配置 LLM API。

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
/pipeline-ingest /path/to/research-paper.pdf
/pipeline-ingest ./meeting-notes.docx
/pipeline-ingest ./product-screenshot.png
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

```
/pipeline-query "transformer 模型的主要创新是什么？"
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
/pipeline-graph
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
/pipeline-ingest paper1.pdf     →  "Transformer 用注意力机制取代 RNN"
/pipeline-ingest paper2.pdf     →  "BERT 的预训练范式更关键" 
/pipeline-ingest paper3.pdf     →  "Scaling Laws 才是根本"
/pipeline-query "核心创新是什么？"  →  三篇论文的观点对比 + 共识与分歧
/pipeline-graph                  →  概念关系可视化
```

> 读 50 篇论文后，你拥有的不是 50 个文件，而是一座互相交叉引用的知识体系。

### 📊 竞品分析

```
/pipeline-ingest openai-blog.md
/pipeline-ingest anthropic-report.pdf
/pipeline-ingest google-deepmind-paper.pdf
/pipeline-query "三家公司在安全方面的策略对比"
→ 自动展示每家公司的立场、共识点和分歧点
```

### 📚 读书笔记

```
/pipeline-ingest chapter-01.md   →  主题/人物页面自动创建
/pipeline-ingest chapter-02.md   →  新信息合并到已有页面
/pipeline-ingest chapter-10.md   →  自动发现前后矛盾
/pipeline-query "主角的动机如何演化？"
```

### 🏢 企业知识库

```
/pipeline-ingest 会议纪要.docx
/pipeline-ingest 客户访谈.pdf
/pipeline-ingest 产品路线图.xlsx
/pipeline-query "客户最常提到的需求是什么？"
/pipeline-lint  →  "项目 X 被 5 个文档提及但没有专属页面"
```

---

## 📝 示例：真实使用流程

### 示例 1：批量摄入 — 一次丢进去，永久积累

```
你：/pipeline-ingest D:\docs\raw
AI：✅ 批量摄入完成 (18个文件)
    📄 sources: 硕士论文×4, 安全审计×3, 事件报告×2, RAG技术×1, 照片×3, 视频×1 ...
    🧑 entities: 23 个 (华为云, Anthropic, 林加锋, 汤涛, 南京邮电大学 ...)
    💡 concepts: 36 个 (RAG, 群组融合, 安全审计, 室性早搏, 图神经网络 ...)
    ⚠️ 矛盾: 3 处跨源声明冲突
```

### 示例 2：跨领域查询 — 答案来自你自己的文档

```
你：/pipeline-query AI在2026年真的会引起程序员失业吗？
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
你：/pipeline-graph
AI：📊 图谱统计:
       提取边: 289 条 (来自 [[wikilinks]])
       推断边: 81 条 (LLM 语义推断)
       总  计: 370 条边, 80 个节点, 6 个社区
    ✅ 图谱构建完成 → 打开 graph/graph.html 查看
```

### 示例 4：维基健康检查

```
你：/pipeline-lint
AI：🏥 维基健康报告
    ❌ 断链 2 处: [[不存在的页面]]
    ⚠️ 孤立页面 1 个: concepts/都市景观.md
    💡 建议: "华为" 在 5 个页面被引用但缺少专属实体页面
```

### 示例 5：一句话生成 Live PPT

```
你：/pipeline-ppt "AI安全趋势分析" --theme apple
AI：📑 Live PPT Generator
    📚 Reading 18 sources, 23 entities, 36 concepts
    🧠 Generated 10 slides
    ✅ Saved to graph/liveppt.html
    🌐 Opened in browser

→ 打开浏览器即可演示：←→翻页 · F全屏 · 5种主题实时切换
→ 每页底部标注 Wiki 来源，可追溯
→ 自包含 HTML，直接发给同事
```

---

## ⚙️ 命令参考

安装后，你将获得 **六个核心斜杠命令**，在 Claude Code 任意项目中可用：

### ⚙️ `/pipeline-config` — 配置 LLM API

配置知识管道使用的 LLM API 信息。**首次使用前必须运行。**

```bash
/pipeline-config
```

交互向导引导你：
- 选择提供商（OpenAI / 自定义兼容端点 / Ollama）
- 输入 base_url、模型名称、API 密钥
- 配置保存到技能目录下的 `.llm_config.json`

### 📥 `/pipeline-ingest` — 摄入文档

将文档摄入到知识维基。支持 PDF、图片、视频、Word、Excel、PPT、HTML、Markdown 等格式。

```bash
/pipeline-ingest "D:\docs\research-paper.pdf"
/pipeline-ingest "/home/user/meeting-notes.docx"
/pipeline-ingest "C:\Users\me\Desktop\screenshot.png"
```

**必须使用绝对路径**。摄入时自动执行：
- 解析多模态内容（文本 + 图片 + 表格）
- 知识融合：新信息合并到已有实体/概念页面
- 主动矛盾检测：与已有 claims 对比，报告冲突
- 更新索引、概览、日志

### 🔍 `/pipeline-query` — 查询维基

基于已摄入的文档进行多源聚合查询。

```bash
/pipeline-query "transformer 模型的核心创新是什么？"
/pipeline-query "各来源对 AI 安全的观点有什么分歧？"
```

查询结果包含：
- **多源视角**：每个源文档对同一问题的不同观点
- **共识与分歧**：多源一致 ✅ / 观点分歧 ⚠️ / 单源独有 ❓
- **[[wikilink]]** 引用到具体页面

### 📊 `/pipeline-graph` — 构建知识图谱

生成交互式 vis.js 知识图谱可视化。

```bash
/pipeline-graph
```

输出：
- `graph/graph.json` — 节点 + 边 + 社区数据
- `graph/graph.html` — 浏览器打开即可交互探索

### 📑 `/pipeline-ppt` — 生成 Live PPT

基于知识维基自动生成交互式 HTML 演示文稿。

```bash
/pipeline-ppt "AI安全趋势分析"
/pipeline-ppt "竞品对比" --theme apple --pages 10
/pipeline-ppt "项目总结" --sources claude-code-leak,rag-tech --open
```

参数：
- `--pages N` — 指定幻灯片数量（默认自动）
- `--theme` — dark / light / apple / warm / minimal
- `--sources` — 指定使用的源文档（逗号分隔 slug）
- `--open` — 生成后自动在浏览器打开

输出：`graph/liveppt.html` — 自包含 HTML，发给任何人直接打开。

### 🏥 `/pipeline-lint` — 维基健康检查

检查知识维基的完整性和一致性。

```bash
/pipeline-lint
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
| `配置 LLM API` / `configure` | `/pipeline-config` |
| `摄入 <文件>` / `ingest <file>` | `/pipeline-ingest` |
| `查询 <问题>` / `query: <question>` | `/pipeline-query` |
| `构建图谱` / `build graph` | `/pipeline-graph` |
| `做PPT` / `生成演示` / `make ppt` | `/pipeline-ppt` |
| `检查` / `lint` | `/pipeline-lint` |

### Python CLI

也可脱离 Claude Code 独立使用：

```bash
python tools/pipeline_ingest.py <file>            # 摄入
python tools/pipeline_query.py "<question>"        # 查询
python tools/pipeline_query.py "<q>" --auto-save   # 查询并自动保存
python tools/pipeline_query.py "<q>" --rc          # 深度推理链查询
python tools/pipeline_lint.py                      # 检查
python tools/build_graph.py                        # 构建图谱
python tools/pipeline_ppt.py "主题" --open          # 生成 Live PPT
python tools/pipeline_config.py                    # 配置
```

#### 🧠 深度推理链 (`--reasoning-chain` / `--rc`)

在查询时加上 `--rc` 标志，会基于知识图谱进行 **BFS 路径搜索**，展示知识节点之间的推理路径：

```bash
python tools/pipeline_query.py "不对称相似度和群组融合有什么关系？" --rc
```

效果：
- **终端**：输出带有 emoji 类型标签的推理链（💡概念 → 📄源 → 🏢实体）
- **浏览器**：自动生成并打开 `graph/reasoning.html`，包含交互式推理子图 + 综合答案面板

> 在 `/pipeline-query` 斜杠命令中，当你提到"推理链"、"推理路径"、"深度分析"等关键词时，agent 会自动添加此标志。

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
