#!/usr/bin/env python3
"""
Query the LLM Wiki.

Usage:
    python tools/pipeline_query.py "What are the main themes across all sources?"
    python tools/pipeline_query.py "How does ConceptA relate to ConceptB?" --save
    python tools/pipeline_query.py "Summarize everything about EntityName" --save synthesis/my-analysis.md

Flags:
    --save              Save the answer back into the wiki (prompts for filename)
    --save <path>       Save to a specific wiki path
"""

import sys
import re
import json
import argparse
from pathlib import Path
from datetime import date
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load LLM configuration
try:
    from core.llm_config import LLMConfig
    llm_config = LLMConfig()
    if llm_config.is_configured():
        cfg = llm_config.get_config()
        os.environ["OPENAI_API_KEY"] = cfg.get("OPENAI_API_KEY", "")
        # Use OpenAI-compatible client
        import openai
        client = openai.OpenAI(
            base_url=cfg.get("LLM_BASE_URL"),
            api_key=cfg.get("OPENAI_API_KEY")
        )
        model = cfg.get("LLM_MODEL", "gpt-4o-mini")
        use_openai = True
    else:
        # Fallback to Anthropic
        import anthropic
        client = anthropic.Anthropic()
        model = "claude-sonnet-4-6"
        use_openai = False
except ImportError:
    # Fallback to Anthropic
    import anthropic
    client = anthropic.Anthropic()
    model = "claude-sonnet-4-6"
    use_openai = False

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
INDEX_FILE = WIKI_DIR / "index.md"
LOG_FILE = WIKI_DIR / "log.md"
SCHEMA_FILE = REPO_ROOT / "CLAUDE.md"

# 加载 BM25 检索引擎
try:
    from core.retrieval import build_wiki_index
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  saved: {path.relative_to(REPO_ROOT)}")


def find_relevant_pages(question: str, index_content: str) -> list[Path]:
    """BM25 检索 + 关键词降级查找相关页面。"""

    # 优先用 BM25 全文检索
    if HAS_BM25:
        try:
            bm25 = build_wiki_index(WIKI_DIR)
            hits = bm25.search(question, top_k=12)
            if hits:
                pages = []
                for rel_path, _score in hits:
                    p = WIKI_DIR / rel_path
                    if p.exists():
                        pages.append(p)
                # 确保 overview 在最前面
                overview = WIKI_DIR / "overview.md"
                if overview.exists() and overview not in pages:
                    pages.insert(0, overview)
                if pages:
                    return pages[:12]
        except Exception:
            pass

    # 降级：关键词匹配
    md_links = re.findall(r'\[([^\]]+)\]\(([^)]+)\)', index_content)
    question_lower = question.lower()
    relevant = []
    for title, href in md_links:
        if any(word in question_lower for word in title.lower().split() if len(word) > 3):
            p = WIKI_DIR / href
            if p.exists():
                relevant.append(p)
    # Always include overview
    overview = WIKI_DIR / "overview.md"
    if overview.exists() and overview not in relevant:
        relevant.insert(0, overview)
    return relevant[:12]


def append_log(entry: str):
    existing = read_file(LOG_FILE)
    LOG_FILE.write_text(entry.strip() + "\n\n" + existing, encoding="utf-8")


def query(question: str, save_path: str | None = None, auto_save: bool = False):
    today = date.today().isoformat()

    # Step 1: Read index
    index_content = read_file(INDEX_FILE)
    if not index_content:
        print("Wiki is empty. Ingest some sources first with: python tools/pipeline_ingest.py <source>")
        sys.exit(1)

    # 加载 claims.json 以支持跨源聚合与矛盾检查
    claims_file = WIKI_DIR / "claims.json"
    claims_context = ""
    source_perspectives = ""   # 跨源视角
    if claims_file.exists():
        try:
            claims_data = json.loads(claims_file.read_text(encoding="utf-8"))
            if claims_data:
                # 构建每个源的 claims 文本
                source_claims_map = {}
                all_claim_texts = []
                for slug, entry in claims_data.items():
                    claims_list = entry.get("claims", entry) if isinstance(entry, dict) else entry
                    title = entry.get("title", slug) if isinstance(entry, dict) else slug
                    texts = []
                    if isinstance(claims_list, list):
                        for c in claims_list:
                            ct = c["claim"] if isinstance(c, dict) else str(c)
                            texts.append(ct)
                            all_claim_texts.append(f"[{slug}] {ct}")
                    source_claims_map[slug] = {"title": title, "claims": texts}

                # 用 BM25 筛选相关 claims
                relevant_slugs = set()
                if HAS_BM25 and all_claim_texts:
                    from core.retrieval import BM25Index
                    ci = BM25Index()
                    for slug, info in source_claims_map.items():
                        ci.add(slug, " ".join(info["claims"]))
                    claim_hits = ci.search(question, top_k=8)
                    relevant_claims = []
                    for slug, _ in claim_hits:
                        relevant_slugs.add(slug)
                        for c in source_claims_map.get(slug, {}).get("claims", []):
                            relevant_claims.append(f"[{slug}] {c}")
                    if relevant_claims:
                        claims_context = "\n\n已知声明（可能相关）：\n" + "\n".join(f"- {c}" for c in relevant_claims[:30])

                # 构建跨源视角上下文
                if relevant_slugs and len(relevant_slugs) >= 2:
                    perspectives = []
                    for slug in relevant_slugs:
                        info = source_claims_map[slug]
                        claims_str = "\n".join(f"  - {c}" for c in info["claims"][:8])
                        perspectives.append(f"**{info['title']}** ({slug}):\n{claims_str}")
                    source_perspectives = "\n\n各源观点汇总：\n" + "\n\n".join(perspectives)
        except Exception:
            pass

    # Step 2: Find relevant pages
    relevant_pages = find_relevant_pages(question, index_content)

    # If no keyword match, ask Claude to identify relevant pages from the index
    if not relevant_pages or len(relevant_pages) <= 1:
        print("  selecting relevant pages via LLM...")
        if use_openai:
            selection_response = client.chat.completions.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": f"给定这个维基索引：\n\n{index_content}\n\n哪些页面与回答这个问题最相关：\"{question}\"\n\n只返回一个 JSON 数组，包含相对文件路径（如索引中列出的），例如 [\"sources/foo.md\", \"concepts/Bar.md\"]。最多 10 个页面。"}]
            )
            raw = selection_response.choices[0].message.content
        else:
            selection_response = client.messages.create(
                model=model,
                max_tokens=512,
                messages=[{"role": "user", "content": f"给定这个维基索引：\n\n{index_content}\n\n哪些页面与回答这个问题最相关：\"{question}\"\n\n只返回一个 JSON 数组，包含相对文件路径（如索引中列出的），例如 [\"sources/foo.md\", \"concepts/Bar.md\"]。最多 10 个页面。"}]
            )
            raw = selection_response.content[0].text
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        try:
            paths = json.loads(raw)
            relevant_pages = [WIKI_DIR / p for p in paths if (WIKI_DIR / p).exists()]
        except (json.JSONDecodeError, TypeError):
            pass

    # Step 3: Read relevant pages
    pages_context = ""
    for p in relevant_pages:
        rel = p.relative_to(REPO_ROOT)
        pages_context += f"\n\n### {rel}\n{p.read_text(encoding='utf-8')}"

    if not pages_context:
        pages_context = f"\n\n### wiki/index.md\n{index_content}"

    schema = read_file(SCHEMA_FILE)

    # Step 4: Synthesize answer
    print(f"  synthesizing answer from {len(relevant_pages)} pages...")

    synthesis_prompt = f"""你正在查询一个 LLM 维基来回答问题。使用下面的维基页面综合一个详尽的答案。

维基页面：
{pages_context}
{claims_context}
{source_perspectives}

问题：{question}

要求：
1. 使用 [[页面名称]] wikilink 语法引用来源（必须是真实存在的页面名）
2. 对每个关键论点，标注有多少个源支持（例如"2 源佐证"或"仅单源"）
3. 如果多个源对同一问题有不同观点，必须在 ## 多源视角 部分明确列出每个源的立场
4. 在 ## 共识与分歧 部分总结：
   - ✅ 多源共识：多个源一致同意的观点
   - ⚠️ 观点分歧：各源存在不同看法的地方
   - ❓ 单源独有：仅在一个源中出现的重要论点
5. 最后添加 ## 来源 部分，列出参考页面及其贡献
6. 如果现有知识不足以完整回答，在 ## 知识缺口 部分指出缺失信息

写一个结构良好的 markdown 答案，包含标题、项目符号和 [[wikilink]] 引用。
"""

    if use_openai:
        response = client.chat.completions.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        answer = response.choices[0].message.content
    else:
        response = client.messages.create(
            model=model,
            max_tokens=4096,
            messages=[{"role": "user", "content": synthesis_prompt}]
        )
        answer = response.content[0].text

    print("\n" + "=" * 60)
    print(answer)
    print("=" * 60)

    # Step 5: 保存答案
    should_save = save_path is not None or auto_save

    if should_save:
        if save_path is None or save_path == "":
            # auto-save 模式：自动生成 slug
            if auto_save:
                slug = re.sub(r'[^\w\u4e00-\u9fff]+', '-', question[:40]).strip('-').lower()
                if not slug:
                    slug = f"query-{today}"
                save_path = f"syntheses/{slug}.md"
            else:
                slug = input("\n保存为 (slug, 例如 'my-analysis'): ").strip()
                if not slug:
                    print("跳过保存。")
                    return
                save_path = f"syntheses/{slug}.md"

        full_save_path = WIKI_DIR / save_path

        # 从答案中提取引用的页面作为 sources
        answer_links = re.findall(r'\[\[([^\]]+)\]\]', answer)
        sources_list = list(set(answer_links))[:10]

        frontmatter = f"""---
title: "{question[:80]}"
type: synthesis
tags: []
sources: {json.dumps(sources_list, ensure_ascii=False)}
last_updated: {today}
---

"""
        write_file(full_save_path, frontmatter + answer)

        # Update index
        index_content = read_file(INDEX_FILE)
        entry = f"- [{question[:60]}]({save_path}) — synthesis"
        if "## Syntheses" in index_content:
            if save_path not in index_content:
                index_content = index_content.replace("## Syntheses\n", f"## Syntheses\n{entry}\n")
                INDEX_FILE.write_text(index_content, encoding="utf-8")
        print(f"  已索引: {save_path}")

    # Append to log
    append_log(f"## [{today}] query | {question[:80]}\n\n从 {len(relevant_pages)} 个页面综合答案。" +
               (f" 已保存到 {save_path}。" if should_save and save_path else ""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="查询 LLM 维基")
    parser.add_argument("question", help="要问维基的问题")
    parser.add_argument("--save", nargs="?", const="", default=None,
                        help="保存答案到维基（可选指定路径）")
    parser.add_argument("--auto-save", action="store_true",
                        help="自动保存答案到 wiki/syntheses/（无需交互）")
    args = parser.parse_args()
    query(args.question, args.save, auto_save=args.auto_save)
