<div align="center">

# 🧠 Knowledge Pipeline

**Your documents shouldn't just be "summarized". They should be compiled into a reasoning-ready knowledge system.**

English | [中文](README.md)

[![GitHub](https://img.shields.io/github/stars/YesIamGodt/knowledge-pipline?style=social)](https://github.com/YesIamGodt/knowledge-pipline)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Skills](https://img.shields.io/badge/npx%20skills%20add-knowledge--pipline-00b894)](https://skills.sh)

A Claude Code skill — throw PDF, images, Word, Excel, video at it, and it compiles them into a structured Markdown wiki + interactive knowledge graph.  
Cross-document contradiction detection, knowledge fusion, deep reasoning chains — not just retrieval, but **reasoning**.

[Quick Start](#-quick-start) · [Live PPT Flagship](#-live-ppt--knowledge-driven-presentations-flagship-feature) · [Who Needs This](#-who-needs-this) · [Comparison](#-comparison) · [Core Capabilities](#-core-capabilities)

</div>

---

## 📑 Live PPT — Knowledge-Driven Presentations (🚀 Flagship Feature)

> **Problem**: Gemini, GPT, Gamma can generate pretty slides. But throw a 200-page audit report at them? They'll give you generic fluff. They don't *understand* your documents — they're just stitching together the model's general knowledge.
>
> **Solution**: `/pipeline-ppt` doesn't take a prompt as input — it takes your **entire knowledge base**. 18 documents compiled into entity networks, concept relationships, contradiction detection results — all become the content source for your slides.

```
/pipeline-ppt "AI Security Analysis"
/pipeline-ppt "Competitive Analysis" --template 3 --pages 10
```

**Core capabilities**:
- 🧠 **Knowledge-base driven** — Extracts key points from wiki entities/concepts/contradictions, not generic model knowledge
- 🎨 **8 built-in templates** — Business, tech, academic scenarios covered, one-click selection
- 📤 **PPTX export** — One-click browser export with editable text (not screenshots)
- ✏️ **Natural language editing** — "Add a competitor comparison table to slide 3", live update without breaking other slides
- 📖 **Source tracing** — Every slide attributes its knowledge source, audit-ready
- 📐 **Smart layout** — Auto-scales when content overflows, never clips or truncates
- ⌨️ **Keyboard navigation** — ←→ navigate · F fullscreen · Home/End

> **Others use AI to make "pretty slides". You use Knowledge Pipeline to make "insightful analysis reports".**

---

## 🎯 Who Needs This?

> If you face any of these scenarios, Knowledge Pipeline was designed for you.

### Scenario 1: The more documents you read, the more lost you get

You've read 30 papers, taken notes, highlighted key points — but three months later when you need to find "did Paper A and Paper B actually contradict each other on this?" you have to re-read them one by one. **ChatGPT and NotebookLM can't solve this — they're stateless, starting from scratch every session.**

→ Knowledge Pipeline auto-merges every ingest into an existing knowledge network. Knowledge accumulates, never lost. Contradiction detection fires in real time.

### Scenario 2: Your questions span multiple documents and domains

You want to know "what are the security strategy differences across these 5 audit reports?" or "what do clinical judgment patterns in medical literature have in common with engineering architecture decisions?" — answers are scattered across different documents, and no single document directly discusses your question.

→ RAG can only retrieve and stitch text fragments. Knowledge Pipeline **reasons out answers** in the compiled concept network, even when no document directly covers the topic.

### Scenario 3: You need a transparent, auditable knowledge middle layer

You don't trust black-box vector databases — you need to see how knowledge is organized, browse every entity and concept page, and manually correct AI's judgments.

→ All knowledge is stored as structured Markdown (Obsidian-compatible). Browsable, editable, version-controllable. No black boxes.

### Scenario 4: You need local deployment + full control

You don't want your data sent to Google's or OpenAI's servers. You need to choose your own LLM provider, or even use local Ollama.

→ Runs entirely locally. Supports any OpenAI-compatible API (DeepSeek, Volcengine, Together AI, Ollama, etc.).

---

## ⚔️ Comparison

### vs ChatGPT / Claude File Upload

| | ChatGPT / Claude File Upload | Knowledge Pipeline |
|---|---|---|
| 📄 Knowledge accumulation | Re-upload every session, no accumulation | **Ingest once, accumulate forever** |
| 🔗 Cross-doc linking | Only retrieves relevant fragments to stitch | **Auto-builds entity & concept networks** |
| ⚠️ Contradiction detection | Won't proactively find contradictions | **Reports conflicts on ingest** |
| 🔄 Knowledge fusion | Doesn't exist, independent each time | **New docs auto-merge into existing pages** |
| 🧭 Multi-source perspectives | Only gives one synthesized answer | **Shows each source's stance + consensus & divergence** |
| 💾 Intermediate repr. | Black box, not user-visible | **Markdown wiki, browsable & editable** |

### vs Google NotebookLM

| | NotebookLM | Knowledge Pipeline |
|---|---|---|
| 🌐 Where it runs | Google Cloud, data uploaded to Google | **Runs locally, data never leaves your machine** |
| 🔧 LLM choice | Google Gemini only | **Any OpenAI-compatible API / local Ollama** |
| ⚠️ Contradiction detection | None | **Proactive cross-source contradiction detection** |
| 🔗 Knowledge fusion | None, sources stay independent | **Auto entity/concept merging** |
| 📊 Knowledge graph | None | **Interactive vis.js graph + community detection** |
| 🧠 Reasoning chains | None | **BFS deep reasoning chains + visualization** |
| 📁 Exportability | Locked in Google ecosystem | **Pure Markdown files, Obsidian/Git compatible** |
| 📦 Format support | PDF, text, web pages | **PDF/images/video/Word/Excel/PPT/HTML** |

### vs Traditional RAG (LangChain / LlamaIndex)

| | Traditional RAG | Knowledge Pipeline |
|---|---|---|
| How it works | Chunk → vectorize → retrieve similar fragments | **Compile → structured knowledge network → reason** |
| Answer basis | Text fragment similarity matching | **Relationship reasoning in concept network** |
| Cross-doc capability | Weak — just throws more fragments into context | **Strong — entity/concept pages auto-merge across sources** |
| Contradiction handling | Unaware, may give contradictory answers | **Proactively detects and reports** |
| Intermediate repr. | Vector database (not readable) | **Markdown wiki (human-readable & editable)** |
| Development cost | Need to write code to build pipeline | **5 slash commands, zero code** |
| New doc adaptation | Need to re-index | **Incremental ingest, auto-fusion** |

**In one sentence:**
- **ChatGPT/Claude** = chat tool, starts from scratch every time
- **NotebookLM** = document reader, single-project single-use, locked to Google
- **Traditional RAG** = search engine, searches through fragments
- **Knowledge Pipeline** = knowledge compiler, compiles documents into a reasoning-ready knowledge system

### vs AI PPT Tools (Gemini / GPT / Gamma / Beautiful.ai)

> Why a separate comparison? Because "AI-powered slides" is one of the hottest AI use cases, but existing tools are **solving the wrong problem** — they compete on who has prettier templates, not who delivers deeper insights.

| | Gemini / GPT / Gamma etc. | Knowledge Pipeline LivePPT |
|---|---|---|
| 📄 Content source | A one-line user prompt | **Knowledge base: multiple docs → entity network → concept graph** |
| 🧠 Analysis depth | Model's generic knowledge, surface-level | **Real data & insights from YOUR documents** |
| ⚠️ Contradiction handling | Unaware, may self-contradict | **Auto-detects cross-source contradictions** |
| 📖 Source tracing | No attribution | **Every slide cites Wiki source pages** |
| ✏️ Editing | Regenerate entire deck | **Natural language per-slide live editing** |
| 📤 Export | PDF / images (not editable) | **PPTX (editable text boxes + HD background)** |
| 🎨 Templates | Platform-fixed templates | **8 built-in themes, one-click selection** |
| 💰 Cost | $20–40/mo subscription | **Free & open source, use your own LLM** |

**AI PPT tools give you "pretty slides". Knowledge Pipeline gives you "insightful analysis reports".**

---

## 🎯 Core Value in 30 Seconds

```
You: Throw in 18 documents (papers + audit reports + news + photos + video)
AI:  ✅ Compiled → 23 entity pages + 36 concept pages + 3 contradictions

You: Ask a question NO document directly discusses —
     "Will AI really cause programmer unemployment in 2026?"

RAG approach: Search for "programmer unemployment" text chunks → nothing found → generic answer from model knowledge
KP approach:  Reason through concept network →
     • Thesis "algorithm coding" + Claude Code "$2.5B ARR" → AI is replacing coding work at scale
     • Thesis "asymmetric similarity discovery" = creative insight → can't be automated
     • Medical "clinical judgment" ≈ Engineering "architecture decisions" → contextual reasoning work won't disappear

Result: Not "unemployment" but "layered elimination" — with citations, reasoning chains, and knowledge graph visualization
```

**The fundamental difference: RAG searches for answers in document fragments. Knowledge Pipeline reasons for answers within your knowledge system.**

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

This registers five slash commands to `~/.claude/commands/`, making `/pipeline-config`, `/pipeline-ingest`, `/pipeline-query`, `/pipeline-graph`, `/pipeline-lint` available in any project.

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

On first use, run **`/pipeline-config`** in Claude Code and follow the interactive wizard.

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
/pipeline-ingest /path/to/research-paper.pdf
/pipeline-ingest ./meeting-notes.docx
/pipeline-ingest ./product-screenshot.png
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

**Knowledge Pipeline**: If an "OpenAI" entity page already exists, new document info is **intelligently merged** — preserving old information, appending new findings, flagging contradictions. Your knowledge only grows.

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
/pipeline-query "What are the main innovations in transformer models?"
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
/pipeline-graph
```

Generates a self-contained `graph.html` — open in browser to interactively explore:
- Node fill color by type (source / entity / concept)
- Node border color by community cluster (Louvain detection)
- Edges distinguish explicit links from inferred relationships
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
/pipeline-ingest paper1.pdf     →  "Transformer replaces RNN with attention"
/pipeline-ingest paper2.pdf     →  "BERT's pre-training paradigm is more important"
/pipeline-ingest paper3.pdf     →  "Scaling Laws are fundamental"
/pipeline-query "What are the core innovations?"  →  Multi-paper comparison + consensus
/pipeline-graph                  →  Concept relationship visualization
```

> After reading 50 papers, you don't have 50 files — you have a cross-referenced knowledge system.

### 📊 Competitive Analysis

```
/pipeline-ingest openai-blog.md
/pipeline-ingest anthropic-report.pdf
/pipeline-ingest google-deepmind-paper.pdf
/pipeline-query "Compare the three companies' safety strategies"
→ Auto-displays each company's position, consensus, and divergence
```

### 📚 Reading Notes

```
/pipeline-ingest chapter-01.md   →  Theme/character pages auto-created
/pipeline-ingest chapter-02.md   →  New info merged into existing pages
/pipeline-ingest chapter-10.md   →  Auto-discovers contradictions
/pipeline-query "How does the protagonist's motivation evolve?"
```

### 🏢 Enterprise Knowledge Base

```
/pipeline-ingest meeting-minutes.docx
/pipeline-ingest customer-interviews.pdf
/pipeline-ingest product-roadmap.xlsx
/pipeline-query "What needs do customers mention most?"
/pipeline-lint  →  "Project X mentioned in 5 docs but has no dedicated page"
```

---

## 📝 Examples: Real Usage Flow

### Example 1: Batch Ingest — Throw It In, Keep It Forever

```
You: /pipeline-ingest D:\docs\raw
AI:  ✅ Batch ingest complete (18 files)
     📄 sources: theses×4, security audits×3, incident reports×2, RAG tech×1, photos×3, video×1 ...
     🧑 entities: 23 (Huawei Cloud, Anthropic, researchers, universities ...)
     💡 concepts: 36 (RAG, group fusion, security audit, graph neural networks ...)
     ⚠️ contradictions: 3 cross-source claim conflicts
```

### Example 2: Cross-Domain Query — Answers From Your Own Documents

```
You: /pipeline-query "Will AI cause programmer unemployment in 2026?"
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
You: /pipeline-graph
AI:  📊 Graph statistics:
        Extracted edges: 289 (from [[wikilinks]])
        Inferred edges: 81 (LLM semantic inference)
        Total: 370 edges, 80 nodes, 6 communities
     ✅ Graph built → Open graph/graph.html to explore
```

### Example 4: Wiki Health Check

```
You: /pipeline-lint
AI:  🏥 Wiki Health Report
     ❌ Broken links: 2
     ⚠️ Orphan pages: 1
     💡 Suggestion: "Huawei" referenced in 5 pages but has no dedicated entity page
```

### Example 5: One-Command Live PPT

```
You: /pipeline-ppt "AI Security Trends" --theme apple
AI:  📑 Live PPT Generator
     📚 Reading 18 sources, 23 entities, 36 concepts
     🧠 Generated 10 slides
     ✅ Saved to graph/liveppt.html
     🌐 Opened in browser

→ Interactive presentation in browser: ←→ navigate · F fullscreen · 5 themes
→ Every slide cites Wiki sources — fully traceable
→ Self-contained HTML — share directly with colleagues
```

---

## ⚙️ Command Reference

After installation, you get **six core slash commands**, available in any Claude Code project:

### ⚙️ `/pipeline-config` — Configure LLM API

Configure the LLM API used by the knowledge pipeline. **Must run before first use.**

```
/pipeline-config
```

Interactive wizard guides you through:
- Provider selection (OpenAI / custom compatible endpoint / Ollama)
- base_url, model name, API key input
- Config saved to `.llm_config.json` in the skill directory

### 📥 `/pipeline-ingest` — Ingest Documents

Ingest documents into the knowledge wiki. Supports PDF, images, video, Word, Excel, PPT, HTML, Markdown.

```
/pipeline-ingest "D:\docs\research-paper.pdf"
/pipeline-ingest "/home/user/meeting-notes.docx"
/pipeline-ingest "C:\Users\me\Desktop\screenshot.png"
```

**Absolute paths required.** Each ingest automatically:
- Parses multimodal content (text + images + tables)
- Knowledge fusion: merges new info into existing entity/concept pages
- Proactive contradiction detection: compares against existing claims
- Updates index, overview, and log

### 🔍 `/pipeline-query` — Query Wiki

Multi-source aggregated query based on ingested documents.

```
/pipeline-query "What are the core innovations in transformer models?"
/pipeline-query "What divergences exist across sources on AI safety?"
```

Results include:
- **Multi-source perspectives**: Each source's different viewpoint on the same question
- **Consensus & divergence**: Multi-source agreement ✅ / Divergence ⚠️ / Single-source unique ❓
- **[[wikilink]]** references to specific pages

### 📊 `/pipeline-graph` — Build Knowledge Graph

Generate interactive vis.js knowledge graph visualization.

```
/pipeline-graph
```

Output:
- `graph/graph.json` — Nodes + edges + community data
- `graph/graph.html` — Open in browser to explore interactively

### 📑 `/pipeline-ppt` — Generate Live PPT

Generate interactive HTML presentations from wiki knowledge.

```bash
/pipeline-ppt "AI Security Trends"
/pipeline-ppt "Competitive Analysis" --theme apple --pages 10
/pipeline-ppt "Project Summary" --sources claude-code-leak,rag-tech --open
```

Parameters:
- `--pages N` — Target slide count (default: auto)
- `--theme` — dark / light / apple / warm / minimal
- `--sources` — Comma-separated source slugs to use
- `--open` — Auto-open in browser after generation

Output: `graph/liveppt.html` — self-contained HTML, share with anyone.

### 🏥 `/pipeline-lint` — Wiki Health Check

Check knowledge wiki completeness and consistency.

```
/pipeline-lint
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
| `configure` / `config LLM` | `/pipeline-config` |
| `ingest <file>` | `/pipeline-ingest` |
| `query: <question>` | `/pipeline-query` |
| `build graph` | `/pipeline-graph` |
| `make ppt` / `generate slides` | `/pipeline-ppt` |
| `lint` / `check wiki` | `/pipeline-lint` |

### Python CLI

Can also be used independently without Claude Code:

```bash
python tools/pipeline_ingest.py <file>            # Ingest
python tools/pipeline_query.py "<question>"        # Query
python tools/pipeline_query.py "<q>" --auto-save   # Query and auto-save
python tools/pipeline_query.py "<q>" --rc          # Deep reasoning chain query
python tools/pipeline_lint.py                      # Lint
python tools/build_graph.py                        # Build graph
python tools/pipeline_ppt.py "topic" --open          # Generate Live PPT
python tools/pipeline_config.py                    # Configure
```

#### 🧠 Deep Reasoning Chain (`--reasoning-chain` / `--rc`)

Add the `--rc` flag to perform **BFS path search** over the knowledge graph, revealing reasoning paths between knowledge nodes:

```bash
python tools/pipeline_query.py "How are asymmetric similarity and group fusion related?" --rc
```

Effects:
- **Terminal**: Displays a reasoning chain with emoji type labels (💡Concept → 📄Source → 🏢Entity)
- **Browser**: Auto-generates and opens `graph/reasoning.html` with an interactive reasoning subgraph + synthesized answer panel

> When using the `/pipeline-query` slash command, mentioning keywords like "reasoning chain", "reasoning path", or "deep analysis" will automatically add this flag.

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
