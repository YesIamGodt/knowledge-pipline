---
title: "Overview"
type: synthesis
tags: []
sources: []
last_updated: 2026-04-16
---

# Overview

*This page is maintained by the LLM. It is updated on every ingest to reflect the current synthesis across all sources.*

## Current State

The wiki is empty. Use `/pipeline-ingest` to add your first document.
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