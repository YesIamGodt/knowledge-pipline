---
title: "Overview"
type: synthesis
tags: []
sources: ["llm-wiki", "rag-tech", "claude-code-leak", "ront-ronp-vpd-vt", "security-incident-brief", "system-architecture-note", "audit-report-template", "hong-kong-top-mall-street-scene", "group-fusion-method-individual-service-customization-full-thesis", "juchang-starlight-market-concert-recording", "beibei-5-scenic-spot-portrait-photo", "修改2 基于图神经网络的多行为推荐系统模型研究-杨晨.docx"]
last_updated: 2026-04-11
---

# Overview

*This page is maintained by the LLM. It is updated on every ingest to reflect the current synthesis across all sources.*

## Current State

The wiki currently contains **17 sources** documenting diverse domains:
- **安全审计** — 华为云生产环境越权访问事件与审计流程
- **系统架构** — 华为云生产环境核心组件与数据流
- **LLM Wiki pattern** — Persistent, compounding knowledge compilation
- **RAG technology** — Real-time retrieval and generation
- **Claude Code源码泄露事件** — AI安全事件与供应链安全案例研究
- **RonT与RonP型室性早搏** — 心脏病学临床案例研究
- **香港都市景观** — 香港TOP商场街景照片记录
- **服务计算** — 面向个人服务定制需求的群组融合方法研究，包含MaxQ、MaxS创新算法及仿真系统实现
- **线下活动记录** — 菊厂（华为）限定星光集市音乐会夜间户外休闲活动实景记录
- **旅游摄影** — 中式宫殿景区人像打卡实拍记录
- **推荐系统** — 基于图神经网络的多行为推荐算法研究，包含MBWGCN、C-MBR两种创新模型及公开数据集实验验证

## Core Thesis: Two Complementary Paradigms

### 1. LLM Wiki: Persistent Compilation

Unlike traditional [[RAG]] systems that retrieve and re-derive answers on every query, the LLM Wiki pattern has the LLM **incrementally build and maintain a persistent wiki** — a structured, interlinked collection of markdown files.

**Key characteristics:**
- Knowledge compiled once and kept current
- Cross-references maintained automatically
- Contradictions flagged over time
- Synthesis evolves with each new source

### 2. RAG: Real-time Retrieval

[[RAG]] (Retrieval-Augmented Generation) retrieves relevant information from external knowledge bases at query time and injects it as context for the LLM.

**Key characteristics:**
- Real-time access to latest information
- No persistent structure across queries
- Flexible and fast to update knowledge
- Good for frequently changing data

### When to Use Which

| Scenario | Recommended Approach |
|----------|---------------------|
| **Long-term research projects** | LLM Wiki — accumulate insights over time |
| **Enterprise knowledge bases** | LLM Wiki — build persistent structure |
| **Real-time news analysis** | RAG — latest information matters most |
| **Customer support** | RAG — product docs change frequently |
| **Personal knowledge management** | LLM Wiki — compound learning over years |

## Three-Layer Architecture (LLM Wiki)

1. **Raw Sources** — Immutable collection (articles, papers, images)
2. **The Wiki** — LLM-generated markdown (summaries, entities, concepts, synthesis)
3. **The Schema** — Configuration document (e.g., [[CLAUDE.md]]) that tells the LLM workflows and conventions

## RAG Architecture Flow

### 1. Indexing Phase (Offline)
- **Document chunking**: Split long documents into appropriate text chunks
- **Vectorization**: Convert text to vectors using Embedding models
- **Vector storage**: Store in vector databases (Milvus, Chroma, Qdrant, etc.)

### 2. Retrieval Phase (Online)
- **Query understanding**: Rewrite, expand, or identify user intent
- **Similarity search**: Recall Top-K relevant documents via vector similarity
- **Reranking**: Use stronger models to refine initial results

### 3. Generation Phase
- **Context assembly**: Combine retrieval results with system prompt and user question
- **LLM generation**: Generate final answer based on provided context
- **Citation**: Mark information sources for traceability

## Operations

### For LLM Wiki
- **Ingest** — Add new sources; LLM updates wiki with summaries, entities, concepts
- **Query** — Ask questions; LLM searches wiki, synthesizes answers with citations
- **Lint** — Health-check wiki for contradictions, orphan pages, stale claims

### For RAG
- **Index** — Process documents into vectors
- **Retrieve** — Search for relevant chunks
- **Generate** — Produce answers with context

## Realizing Vannevar Bush's Memex

The LLM Wiki pattern closely resembles [[VannevarBush]]'s 1945 [[Memex]] vision — a personal, curated knowledge store with associative trails. The missing piece in Bush's vision was **maintenance**, which LLMs now solve through their ability to:
- Touch 15 files in one pass
- Never forget cross-references
- Maintain consistency at scale
- Work for near-zero marginal cost

## Recommended Tools

### For LLM Wiki
- [[Obsidian]] — Wiki viewer/IDE with graph view
- qmd — Local search engine (BM25 + vector search)
- Obsidian Web Clipper — Article → markdown conversion
- Marp — Markdown-based slide decks
- Dataview — Frontmatter queries

### For RAG
- **Vector databases**: Milvus, Chroma, Qdrant, Weaviate, Pinecone
- **Embedding models**: BGE-M3, GTE, M3E (Chinese), E5-Mistral, OpenAI text-embedding-3
- **Rerankers**: BGE-Reranker, Cohere Rerank
- **Frameworks**: [[LangChain]], [[LlamaIndex]], Haystack, Semantic Kernel

## Human vs. LLM Roles

| Aspect | Human | LLM |
|--------|-------|-----|
| Source curation | ✅ | |
| Direction & questions | ✅ | |
| Bookkeeping | | ✅ |
| Cross-referencing | | ✅ |
| Filing & maintenance | | ✅ |

The human's job: **curate sources, direct analysis, ask questions, think about meaning.**

The LLM's job: **everything else.**

## RAG Challenges and Solutions

| Problem | Solution |
|---------|----------|
| Semantic gap | Query rewriting, HyDE (Hypothetical Document Embeddings) |
| Long document retrieval | Sliding window, hierarchical indexing |
| Multi-hop reasoning | Iterative RAG, GraphRAG |
| Context redundancy | LLMLingua compression, selective context |
| Generation quality | Self-RAG, Corrective RAG, RAG-Fusion |

## Use Cases

**For LLM Wiki:**
- Personal tracking (goals, health, psychology)
- Research projects (papers, articles over months)
- Book reading companions (character maps, plot threads)
- Business/team wikis (from Slack, meetings, docs)
- Competitive analysis, due diligence

**For RAG:**
- Enterprise knowledge base Q&A
- Customer support chatbots
- Legal/medical consultation (with professional literature)
- Code assistants (search open-source repos)
- Financial report analysis (real-time news integration)

## Hybrid Approach: Combining Both

The most powerful systems combine both approaches:

1. **Use LLM Wiki** to build a curated, well-structured knowledge base over time
2. **Use RAG** as the query interface, with the wiki as one of the knowledge sources
3. **Benefits**:
   - Persistent structure for long-term knowledge
   - Flexibility for real-time updates
   - Rich cross-references maintained automatically
   - Fast, accurate retrieval when needed

## Frameworks for Implementation

- [[LangChain]] — General-purpose LLM application framework with strong RAG support
- [[LlamaIndex]] — Data framework focused on connecting custom data to LLMs
- Both support the full RAG pipeline: indexing, retrieval, and generation