<div align="center">

# 🧠 Knowledge Pipeline

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

But when you have **50 documents** spanning **3 months**, involving **12 people** and **8 core concepts** — ChatGPT gives you a chat log. Knowledge Pipeline gives you a **living knowledge base**:

| | ChatGPT / Claude File Upload (RAG) | Knowledge Pipeline |
|---|---|---|
| 📄 Read docs | Re-upload every session, no accumulation | **Ingest once, accumulate forever** |
| 🔗 Cross-doc links | Only retrieves relevant fragments to stitch | **Auto-builds entity & concept networks** |
| ⚠️ Contradiction detection | Won't proactively find contradictions | **Reports conflicts on ingest** |
| 🔄 Knowledge fusion | Doesn't exist, independent retrieval each time | **New docs auto-merge into existing pages** |
| 🧭 Multi-source perspectives | Only gives one synthesized answer | **Shows each source's stance + consensus & divergence** |
| 📊 Visualization | None | **Interactive knowledge graph (vis.js)** |
| 💾 Intermediate repr. | Black-box vectors, not browsable | **Structured Markdown wiki (Obsidian-compatible)** |

**In one sentence: ChatGPT is your chat tool. Knowledge Pipeline is your second brain.**

### 🎯 Real-World Case: Deep Pattern Mining

We ingested 18 real documents — medical case reports, CS master's theses, a source code leak incident, street photos, a concert video — spanning wildly different domains.

Then asked a question that **no single document directly discusses**:

> **"Will AI really cause programmer unemployment in 2026?"**

**What RAG (ChatGPT/Claude file upload) does:**
Retrieves text chunks most similar to "programmer unemployment" — but none of the 18 documents discuss this topic. RAG can't find relevant passages, so it falls back to the model's own knowledge for a generic answer.

**What Knowledge Pipeline does:**

```
You: /pipeline-ingest D:\docs\raw
AI:  ✅ Batch ingest complete
     📝 18 sources → 23 entity pages + 36 concept pages
     ⚠️ Found 3 cross-source contradictions

You: /pipeline-query "Will AI really cause programmer unemployment in 2026?"
```

It doesn't search text fragments — it discovers deep patterns in the **pre-compiled concept network and entity relationships**:

```markdown
## AI's Impact on Programmer Employment (Based on Wiki Knowledge Base)

### Deep Pattern Discovery

1. **The line between "automatable" and "not automatable"**
   Two master's theses ([[group-fusion-method]] [[gnn-based-multi-behavior]])
   core work is implementing algorithms: MBWGCN model, MaxQ/MaxS group fusion
   algorithms, GNN training pipelines. The essence of this work is "translating
   math formulas into code" — exactly what AI coding tools excel at.
   
   But in the same papers, **problem discovery and modeling** — like realizing
   that "similarity between requirements is asymmetric" ([[AsymmetricSimilarity]]),
   or modeling recommendation systems as multi-behavior graph structures —
   this kind of creative insight cannot currently be automated.

2. **AI coding tools are already big business**
   The [[Claude Code]] source code leak revealed: this is a $2.5B ARR product
   with unreleased features like KAIROS (daemon) and ULTRAPLAN (cloud planning).
   AI coding tools aren't lab toys — they're already replacing development work
   at scale.
   
   But the leak itself ([[SupplyChainSecurity]]) also proves: production
   engineering judgment — "should we exclude source maps in .npmignore" —
   this kind of context-aware decision-making is something AI itself still
   gets wrong.

3. **Cross-domain validation: Medicine vs Programming**
   Medical case reports ([[RonT Syndrome]] [[PVC]]) show that a clinician's
   judgment process — whether coupling intervals are fixed, whether lidocaine
   is needed — depends entirely on experience and context.
   This is isomorphic to "senior programmers judging system architecture":
   **work requiring contextual reasoning won't disappear; work that only
   requires execution will be replaced.**

### Overall Verdict

Not "unemployment" but "layered elimination":
- ✅ Consensus: Algorithm implementation and data processing ("translational coding") will sharply decrease
- ⚠️ Divergence: Problem modeling and creative insight are currently safe (asymmetric similarity discovery can't be automated)
- ❓ Signal: AI tools still have engineering blind spots (source map leak = AI can't replace engineering judgment)
```

**Why can't RAG do this?**

Because RAG works by "retrieving text fragments" — it searches the vector store for passages most similar to "programmer unemployment". But none of the 18 documents discuss programmer unemployment, so RAG can't retrieve useful content.

Knowledge Pipeline can answer because ingestion has already compiled documents into a **structured concept network**:

- Thesis MBWGCN code implementation → concept pages [[GraphNeuralNetwork]], [[ServiceComputing]]
- Claude Code's ARR data → entity page [[Claude Code]], concept page [[SupplyChainSecurity]]
- Cardiac arrhythmia clinical judgment → concept pages [[RonT Syndrome]], [[CouplingInterval]]

At query time, the system doesn't search text fragments — it **reasons** between concept and entity pages: the thesis's "coding work" and Claude Code's "AI programming capability" connect through the concept network; medicine's "clinical judgment" and engineering's "architecture decisions" relate through their shared trait of "contextual reasoning".

**This is the fundamental difference: RAG searches for answers in document fragments. Knowledge Pipeline reasons for answers within your knowledge system.**

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

---

## ⚙️ Command Reference

After installation, you get **five core slash commands**, available in any Claude Code project:

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
