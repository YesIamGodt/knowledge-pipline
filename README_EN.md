<div align="center">

# 🧠 Knowledge Pipline

**Stop asking AI to search for you. Make it understand for you.**

English | [中文](README.md)

[![GitHub](https://img.shields.io/github/stars/YesIamGodt/knowledge-pipline?style=social)](https://github.com/YesIamGodt/knowledge-pipline)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/npx%20skills%20add-knowledge--pipline-00b894)](https://skills.sh)

Throw any document at it — PDF, images, video, Word, Excel — it doesn't just "summarize", it **compiles into structured knowledge**, automatically discovers cross-document contradictions, tracks entity evolution, and builds an interactive knowledge graph.

[Quick Start](#-quick-start) · [Why Not Just Use ChatGPT](#-why-not-just-use-chatgpt) · [Core Capabilities](#-core-capabilities) · [Use Cases](#-use-cases) · [Examples](#-examples)

</div>

---

## 💡 Why Not Just Use ChatGPT?

> "Can't I just toss my PDF into ChatGPT?"

Sure. If you have one document and one question.

But when you have **50 documents** spanning **3 months**, involving **12 people** and **8 core concepts** — ChatGPT gives you a chat log. Knowledge Pipline gives you a **living knowledge base**:

| | ChatGPT / Claude Direct | Knowledge Pipline |
|---|---|---|
| 📄 Read docs | Re-upload every session | **Ingest once, accumulate forever** |
| 🔗 Cross-doc links | You piece it together | **Auto-builds entity & concept networks** |
| ⚠️ Contradiction detection | Never tells you | **Reports conflicts on ingest** |
| 🔄 Knowledge fusion | Doesn't exist | **New docs auto-merge into existing pages** |
| 🧭 Multi-source perspectives | One answer | **Shows each source's stance + consensus & divergence** |
| 📊 Visualization | None | **Interactive knowledge graph (vis.js)** |
| 💾 Persistence | Chat history (gone if lost) | **Structured Markdown wiki** |

**In one sentence: ChatGPT is your chat tool. Knowledge Pipline is your second brain.**

### 🎯 Real-World Case: See the Difference

We ingested 18 real documents — medical case reports, CS master's theses, cloud security audits, a source code leak incident, street photos, a concert video — spanning wildly different domains.

Then asked a question that **no single document directly answers**:

> **"Will AI really cause programmer unemployment in 2026? Give a detailed answer."**

**What ChatGPT does:**
You upload 18 files one by one (or they don't even fit), it reads and forgets, gives you a generic answer. Next time you ask, it remembers nothing.

**What Knowledge Pipline does:**

```
You: /pipline-ingest D:\docs\raw
AI:  ✅ Batch ingest complete
     📝 18 sources → 23 entity pages + 36 concept pages
     ⚠️ Found 3 cross-source contradictions

You: /pipline-query "Will AI really cause programmer unemployment in 2026?"
```

It doesn't answer from thin air — it extracts evidence from **multiple completely different domains** and cross-analyzes:

```markdown
## AI's Impact on Programmer Employment (Based on Wiki Knowledge Base)

### Direct Evidence from the Wiki

1. **Claude Code's Real Capabilities** ([[claude-code-leak]])
   The March 2026 source code leak revealed: Claude Code is already a $2.5B ARR product
   handling complex programming tasks. AI coding tools have entered mass commercialization.

2. **Academic Signals** ([[group-fusion-method]] [[gnn-based-multi-behavior]])
   Two 2023 master's theses still completed algorithm design traditionally,
   but the coding work (data processing, model implementation) is exactly
   what AI excels at replacing.

3. **Enterprise Security Audits Still Need Human Judgment** ([[security-incident-brief]])
   Cloud security incidents involving IAM policy audits and change management
   require deep business context understanding — not replaceable by AI short-term.

4. **Multimodal Understanding Is Maturing** ([[beibei-5-scenic-spot-portrait]]
   [[hong-kong-top-mall-street-scene]] [[juchang-starlight-market-concert]])
   The system successfully understood photos and video content, showing AI's
   capability boundary is expanding from "writing code" to "understanding the world".

### Overall Verdict

Not "unemployment" but "transformation":
- ✅ Consensus: Junior coding work (CRUD, data processing) will significantly decrease
- ⚠️ Divergence: Whether high-level system design will be affected
- ❓ Unknown: When AI-native development paradigms will become mainstream
```

**The key difference:**
- ChatGPT can only give generic answers from its training data
- Knowledge Pipline extracts evidence from **your own documents**, even when those documents are completely unrelated to "programmer unemployment" — it discovers **hidden connections** between Claude Code commercialization data, academic paper coding patterns, and enterprise security audit human requirements

This is the fundamental difference between a "knowledge pipeline" and a "chat tool": **it doesn't answer questions — it finds answers within your knowledge system.**

---

## 🚀 Quick Start

### Option 1: npx skills add (Recommended)

```bash
npx skills add YesIamGodt/knowledge-pipline
```

Auto-installs to `~/.agents/skills/knowledge-pipline/` (symlinked to `~/.claude/skills/`), ready to use once Claude Code starts.

#### Install Slash Commands (Important!)

`npx skills add` installs skill files but **doesn't auto-register slash commands**. After installing, run:

**Windows (CMD):**
```cmd
node "%USERPROFILE%\.agents\skills\knowledge-pipline\scripts\install-commands.mjs"
```

**Windows (PowerShell):**
```powershell
node "$HOME\.agents\skills\knowledge-pipline\scripts\install-commands.mjs"
```

**macOS / Linux:**
```bash
node ~/.agents/skills/knowledge-pipline/scripts/install-commands.mjs
```

This registers five slash commands to `~/.claude/commands/`, making `/pipline-config`, `/pipline-ingest`, `/pipline-query`, `/pipline-graph`, `/pipline-lint` available in any project.

### Option 2: Manual Install

```bash
git clone https://github.com/YesIamGodt/knowledge-pipline.git
cd knowledge-pipline
node scripts/install-commands.mjs
```

### Prerequisites

| Dependency | Description |
|------------|-------------|
| **Python 3.9+** | Core runtime |
| **A multimodal LLM API** | OpenAI / DeepSeek / Volcengine / local Ollama |
| **Claude Code** (recommended) | Agent host for running the skill |

```bash
# Install Python dependencies
pip install openai pymupdf python-docx openpyxl python-pptx beautifulsoup4 pillow

# Optional: video processing
pip install opencv-python
```

### Configure LLM API

On first use, run **`/pipline-config`** in Claude Code and follow the interactive wizard.

Or manually create a config file:

```json
// ~/.claude/skills/knowledge-pipline/.llm_config.json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-your-key-here"
}
```

<details>
<summary>📋 Supported LLM Providers</summary>

| Provider | base_url | Model Example |
|----------|----------|---------------|
| OpenAI | `https://api.openai.com/v1` | gpt-4o-mini |
| DeepSeek | `https://api.deepseek.com/v1` | deepseek-chat |
| Volcengine | `https://ark.cn-beijing.volces.com/api/coding/v3` | doubao-* |
| Together AI | `https://api.together.xyz/v1` | meta-llama/* |
| Ollama (local) | `http://localhost:11434/v1` | llama3.2 |

</details>

---

## 🔥 Core Capabilities

### 📥 Multimodal Ingestion

```
/pipline-ingest /path/to/research-paper.pdf
/pipline-ingest ./meeting-notes.docx
/pipline-ingest ./product-screenshot.png
```

| Format | Support | Processing |
|--------|---------|------------|
| 📄 PDF | ✅ | Text + tables + image multimodal understanding |
| 🖼️ Images | ✅ | Claude multimodal vision / OCR |
| 🎬 Video | ✅ | Keyframe extraction + scene understanding + audio transcription |
| 📝 Word | ✅ | Text + tables + formatting |
| 📊 Excel | ✅ | Multi-sheet + data cleaning |
| 📽️ PPT | ✅ | Slide content + images |
| 🌐 HTML | ✅ | Main content extraction |
| 📄 Markdown/Text | ✅ | Direct read |

### 🔗 Knowledge Fusion

**Typical tools**: Each ingest overwrites old content.

**Knowledge Pipline**: If an "OpenAI" entity page already exists, new document info is **intelligently merged** — preserving old information, appending new findings, flagging contradictions. Your knowledge only grows.

### ⚡ Proactive Contradiction Detection

Doesn't wait for you to ask. Automatically scans after every ingest:

```
============================================================
📋 Proactive Contradiction Report
============================================================
## ⚠️ Contradictions Found
- [paper-A] "GPT-4 code generation accuracy: 92%"
  vs [paper-B] "GPT-4 code generation accuracy: only 78%"
  — Difference may stem from different evaluation benchmarks

## ✅ Cross-Source Corroboration
- [paper-A] and [report-C] both mention "RAG reduces hallucination by 40%"
  — Strengthens credibility of this claim
============================================================
```

### 🧭 Cross-Source Aggregated Query

```
/pipline-query "What are the main innovations in transformer models?"
```

Answers include not just conclusions but **multi-source perspectives**:

```markdown
## Multi-Source Perspectives
- [[attention-paper]]: Attention mechanism is the core innovation, replacing RNN
- [[bert-paper]]: Pre-training + fine-tuning paradigm is the key contribution
- [[gpt-survey]]: Scaling Laws are more fundamental

## Consensus & Divergence
✅ Multi-source consensus: Self-attention significantly improves parallel computation (3 sources)
⚠️ Divergence: Whether the core contribution is architectural or training paradigm (2 sources)
❓ Single-source unique: MoE may be the next-gen architecture (1 source only)
```

### 📊 Knowledge Graph

```
/pipline-graph
```

Generates a self-contained `graph.html` — open in browser to interactively explore:
- Nodes colored by type (source / entity / concept)
- Edges distinguish explicit links from inferred relationships
- Louvain community detection for auto-clustering
- Search and zoom support

---

## 📂 Knowledge Base Structure

```
wiki/
├── index.md          # Global index — auto-updated on every ingest
├── overview.md       # Living synthesis across all sources
├── claims.json       # Claims database — foundation for contradiction detection
├── sources/          # One summary page per source document
│   ├── attention-is-all-you-need.md
│   └── quarterly-report-q1.md
├── entities/         # Auto-generated entity pages
│   ├── OpenAI.md
│   └── TransformerModel.md
├── concepts/         # Auto-generated concept pages
│   ├── RAG.md
│   └── KnowledgeFusion.md
└── syntheses/        # Archived query answers
    └── main-innovations.md
```

Open `wiki/` in [Obsidian](https://obsidian.md) — native `[[wikilink]]` support, graph mode works instantly.

---

## 🎯 Use Cases

### 🔬 Academic Research

```
/pipline-ingest paper1.pdf     →  "Transformer replaces RNN with attention"
/pipline-ingest paper2.pdf     →  "BERT's pre-training paradigm is more important"
/pipline-ingest paper3.pdf     →  "Scaling Laws are fundamental"
/pipline-query "What are the core innovations?"  →  Multi-paper comparison + consensus
/pipline-graph                  →  Concept relationship visualization
```

> After reading 50 papers, you don't have 50 files — you have a cross-referenced knowledge system.

### 📊 Competitive Analysis

```
/pipline-ingest openai-blog.md
/pipline-ingest anthropic-report.pdf
/pipline-ingest google-deepmind-paper.pdf
/pipline-query "Compare the three companies' safety strategies"
→ Auto-displays each company's position, consensus, and divergence
```

### 📚 Reading Notes

```
/pipline-ingest chapter-01.md   →  Theme/character pages auto-created
/pipline-ingest chapter-02.md   →  New info merged into existing pages
/pipline-ingest chapter-10.md   →  Auto-discovers contradictions
/pipline-query "How does the protagonist's motivation evolve?"
```

### 🏢 Enterprise Knowledge Base

```
/pipline-ingest meeting-minutes.docx
/pipline-ingest customer-interviews.pdf
/pipline-ingest product-roadmap.xlsx
/pipline-query "What needs do customers mention most?"
/pipline-lint  →  "Project X mentioned in 5 docs but has no dedicated page"
```

---

## 📝 Examples: Real Usage Flow

### Example 1: Batch Ingest — Throw It In, Keep It Forever

```
You: /pipline-ingest D:\docs\raw
AI:  ✅ Batch ingest complete (18 files)
     📄 sources: theses×4, security audits×3, incident reports×2, RAG tech×1, photos×3, video×1 ...
     🧑 entities: 23 (Huawei Cloud, Anthropic, researchers, universities ...)
     💡 concepts: 36 (RAG, group fusion, security audit, graph neural networks ...)
     ⚠️ contradictions: 3 cross-source claim conflicts
```

### Example 2: Cross-Domain Query — Answers From Your Own Documents

```
You: /pipline-query "Will AI cause programmer unemployment in 2026?"
AI:  ## AI's Impact on Programmer Employment

     ### Direct Evidence from Wiki
     1. [[claude-code-leak]]: Claude Code ARR hit $2.5B, AI coding tools at mass scale
     2. [[group-fusion-method]]: Academic paper coding work is exactly what AI replaces best
     3. [[security-incident-brief]]: Security audits still need human business context understanding

     ### Overall Verdict
     ✅ Consensus: Junior coding work will significantly decrease
     ⚠️ Divergence: Whether high-level system design will be affected
     ❓ Unknown: When AI-native development paradigms will become mainstream
```

### Example 3: Build Knowledge Graph

```
You: /pipline-graph
AI:  📊 Graph statistics:
        Extracted edges: 289 (from [[wikilinks]])
        Inferred edges: 81 (LLM semantic inference)
        Total: 370 edges, 80 nodes, 6 communities
     ✅ Graph built → Open graph/graph.html to explore
```

### Example 4: Wiki Health Check

```
You: /pipline-lint
AI:  🏥 Wiki Health Report
     ❌ Broken links: 2
     ⚠️ Orphan pages: 1
     💡 Suggestion: "Huawei" referenced in 5 pages but has no dedicated entity page
```

---

## ⚙️ Command Reference

After installation, you get **five core slash commands**, available in any Claude Code project:

### ⚙️ `/pipline-config` — Configure LLM API

Configure the LLM API used by the knowledge pipeline. **Must run before first use.**

```
/pipline-config
```

Interactive wizard guides you through:
- Provider selection (OpenAI / custom compatible endpoint / Ollama)
- base_url, model name, API key input
- Config saved to `.llm_config.json` in the skill directory

### 📥 `/pipline-ingest` — Ingest Documents

Ingest documents into the knowledge wiki. Supports PDF, images, video, Word, Excel, PPT, HTML, Markdown.

```
/pipline-ingest "D:\docs\research-paper.pdf"
/pipline-ingest "/home/user/meeting-notes.docx"
/pipline-ingest "C:\Users\me\Desktop\screenshot.png"
```

**Absolute paths required.** Each ingest automatically:
- Parses multimodal content (text + images + tables)
- Knowledge fusion: merges new info into existing entity/concept pages
- Proactive contradiction detection: compares against existing claims
- Updates index, overview, and log

### 🔍 `/pipline-query` — Query Wiki

Multi-source aggregated query based on ingested documents.

```
/pipline-query "What are the core innovations in transformer models?"
/pipline-query "What divergences exist across sources on AI safety?"
```

Results include:
- **Multi-source perspectives**: Each source's different viewpoint on the same question
- **Consensus & divergence**: Multi-source agreement ✅ / Divergence ⚠️ / Single-source unique ❓
- **[[wikilink]]** references to specific pages

### 📊 `/pipline-graph` — Build Knowledge Graph

Generate interactive vis.js knowledge graph visualization.

```
/pipline-graph
```

Output:
- `graph/graph.json` — Nodes + edges + community data
- `graph/graph.html` — Open in browser to explore interactively

### 🏥 `/pipline-lint` — Wiki Health Check

Check knowledge wiki completeness and consistency.

```
/pipline-lint
```

Checks for:
- **Orphan pages** — Pages with no inbound links
- **Broken links** — [[wikilinks]] pointing to non-existent pages
- **Contradictions** — Cross-page claim conflicts
- **Missing entities** — Frequently mentioned but lacking dedicated pages
- **Data gaps** — Suggests new sources to add

### Natural Language Triggers (Also Supported)

| Say | Equivalent to |
|-----|---------------|
| `configure` / `config LLM` | `/pipline-config` |
| `ingest <file>` | `/pipline-ingest` |
| `query: <question>` | `/pipline-query` |
| `build graph` | `/pipline-graph` |
| `lint` / `check wiki` | `/pipline-lint` |

### Python CLI

Can also be used independently without Claude Code:

```bash
python tools/pipeline_ingest.py <file>            # Ingest
python tools/pipeline_query.py "<question>"        # Query
python tools/pipeline_query.py "<q>" --auto-save   # Query and auto-save
python tools/pipeline_lint.py                      # Lint
python tools/build_graph.py                        # Build graph
python tools/pipeline_config.py                    # Configure
```

### Environment Variables

```bash
PIPELINE_PDF_STRATEGY=fast|balanced|accurate  # PDF processing strategy
LLM_CONFIG_JSON=/path/to/.llm_config.json     # Custom config path
```

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User (Natural Language)                │
├─────────────────────────────────────────────────────────┤
│                    Claude Code Agent                     │
│              Reads SKILL.md / CLAUDE.md instructions     │
├──────────┬──────────┬──────────┬──────────┬──────────────┤
│  Ingest  │  Query   │   Lint   │  Graph   │   Config     │
├──────────┴──────────┴──────────┴──────────┴──────────────┤
│  BM25 Retrieval │ Wikilink Parser │ Claims DB │ Fusion   │
├─────────────────────────────────────────────────────────┤
│  Multimodal Processors (PDF / Image / Video / Office)    │
├─────────────────────────────────────────────────────────┤
│               LLM API (OpenAI-compatible)                │
└─────────────────────────────────────────────────────────┘
         ↕                    ↕                    ↕
    wiki/ (Markdown)    claims.json         graph/graph.html
```

---

## 🤝 Contributing

PRs and Issues welcome.

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.
