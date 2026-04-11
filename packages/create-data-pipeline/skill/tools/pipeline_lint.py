#!/usr/bin/env python3
"""
Lint the LLM Wiki for health issues.

Usage:
    python tools/pipeline_lint.py
    python tools/pipeline_lint.py --save          # save lint report to wiki/lint-report.md

Checks:
  - Orphan pages (no inbound wikilinks from other pages)
  - Broken wikilinks (pointing to pages that don't exist)
  - Missing entity pages (entities mentioned in 3+ pages but no page)
  - Contradictions between pages
  - Data gaps and suggested new sources
"""

import re
import sys
import json
import argparse
from pathlib import Path
from collections import defaultdict
from datetime import date
import os

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# LLM configuration — initialized lazily in run_lint() to allow --help without config
client = None
model = None
use_openai = False


def _init_llm():
    """Initialize LLM client. Must be called before any LLM operation."""
    global client, model, use_openai
    from core.llm_config import require_llm_config, LLMConfig
    require_llm_config()

    llm_config = LLMConfig()
    cfg = llm_config.get_config()
    import openai
    client = openai.OpenAI(
        base_url=cfg.get("LLM_BASE_URL"),
        api_key=cfg.get("OPENAI_API_KEY")
    )
    model = cfg.get("LLM_MODEL", "gpt-4o-mini")
    use_openai = True


REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
LOG_FILE = WIKI_DIR / "log.md"
SCHEMA_FILE = REPO_ROOT / "CLAUDE.md"

# 加载 WikilinkResolver（规范化链接解析）
try:
    from core.wikilink import WikilinkResolver
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def all_wiki_pages() -> list[Path]:
    return [p for p in WIKI_DIR.rglob("*.md")
            if p.name not in ("index.md", "log.md", "lint-report.md")]


def extract_wikilinks(content: str) -> list[str]:
    return re.findall(r'\[\[([^\]]+)\]\]', content)


# ─── 使用 WikilinkResolver 的新实现 ───

def _get_resolver():
    """获取或创建 WikilinkResolver 实例"""
    if HAS_RESOLVER:
        return WikilinkResolver(WIKI_DIR)
    return None


def find_orphans(pages: list[Path]) -> list[Path]:
    resolver = _get_resolver()
    if resolver:
        return resolver.find_orphans()
    # 降级：旧逻辑
    inbound = defaultdict(int)
    for p in pages:
        content = read_file(p)
        for link in extract_wikilinks(content):
            for q in pages:
                if q.stem.lower() == link.lower():
                    inbound[q] += 1
    return [p for p in pages if inbound[p] == 0 and p != WIKI_DIR / "overview.md"]


def find_broken_links(pages: list[Path]) -> list[tuple[Path, str]]:
    resolver = _get_resolver()
    if resolver:
        return resolver.find_broken_links()
    # 降级：旧逻辑
    broken = []
    for p in pages:
        content = read_file(p)
        for link in extract_wikilinks(content):
            found = any(q.stem.lower() == link.lower() for q in pages)
            if not found:
                broken.append((p, link))
    return broken


def find_missing_entities(pages: list[Path]) -> list[str]:
    """查找在 3+ 个页面中提及但没有独立页面的实体。"""
    resolver = _get_resolver()
    mention_counts: dict[str, int] = defaultdict(int)
    existing_pages = {p.stem.lower() for p in pages}
    for p in pages:
        content = read_file(p)
        links = extract_wikilinks(content)
        for link in links:
            # 使用 resolver 规范化检查
            if resolver:
                if not resolver.exists(link):
                    mention_counts[link] += 1
            else:
                if link.lower() not in existing_pages:
                    mention_counts[link] += 1
    return [name for name, count in mention_counts.items() if count >= 3]


def check_claims_contradictions() -> list[str]:
    """检查 claims.json 中跨源的潜在矛盾。"""
    claims_file = WIKI_DIR / "claims.json"
    if not claims_file.exists():
        return []
    try:
        claims_data = json.loads(claims_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return []
    if len(claims_data) < 2:
        return []

    # 构建所有声明的扁平列表
    all_claims = []
    for slug, claims_list in claims_data.items():
        for c in claims_list:
            all_claims.append((slug, c))

    if len(all_claims) < 2:
        return []

    # 用 LLM 检测矛盾（批量）
    claims_text = "\n".join(f"[{slug}] {claim}" for slug, claim in all_claims[:40])
    prompt = f"""以下是从不同来源提取的声明。识别其中互相矛盾或冲突的声明对。

{claims_text}

如果发现矛盾，每条格式为：
- [源A] 声明X 与 [源B] 声明Y 矛盾：简要说明

如果没有发现矛盾，回复「无矛盾」。"""

    try:
        if use_openai:
            resp = client.chat.completions.create(
                model=model, max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            result = resp.choices[0].message.content
        else:
            resp = client.messages.create(
                model=model, max_tokens=1500,
                messages=[{"role": "user", "content": prompt}]
            )
            result = resp.content[0].text
        if "无矛盾" in result:
            return []
        return [line.strip() for line in result.strip().split("\n") if line.strip().startswith("-")]
    except Exception:
        return []


def run_lint():
    # ========== 第一步：检查 LLM 配置 ==========
    _init_llm()

    pages = all_wiki_pages()
    today = date.today().isoformat()

    if not pages:
        print("Wiki is empty. Nothing to lint.")
        return ""

    print(f"Linting {len(pages)} wiki pages...")

    # Deterministic checks
    orphans = find_orphans(pages)
    broken = find_broken_links(pages)
    missing_entities = find_missing_entities(pages)

    print(f"  orphans: {len(orphans)}")
    print(f"  broken links: {len(broken)}")
    print(f"  missing entity pages: {len(missing_entities)}")

    # 检查 claims.json 中的跨源矛盾
    print("  检查跨源声明矛盾...")
    claim_contradictions = check_claims_contradictions()
    if claim_contradictions:
        print(f"  发现 {len(claim_contradictions)} 条潜在矛盾")

    # Build context for semantic checks — 扩大覆盖范围
    # 按页面大小排序，优先纳入小页面以覆盖更多
    pages_by_size = sorted(pages, key=lambda p: p.stat().st_size if p.exists() else 0)
    sample = []
    total_chars = 0
    char_limit = 50000  # 总字符上限
    for p in pages_by_size:
        content = read_file(p)
        truncated = content[:1500]
        if total_chars + len(truncated) > char_limit:
            break
        sample.append(p)
        total_chars += len(truncated)
    pages_context = ""
    for p in sample:
        rel = p.relative_to(REPO_ROOT)
        pages_context += f"\n\n### {rel}\n{read_file(p)[:1500]}"

    print("  running semantic lint via LLM API...")
    if use_openai:
        response = client.chat.completions.create(
            model=model,
            max_tokens=3000,
            messages=[{"role": "user", "content": f"""You are linting an LLM Wiki. Review the pages below and identify:
1. Contradictions between pages (claims that conflict)
2. Stale content (summaries that newer sources have superseded)
3. Data gaps (important questions the wiki can't answer — suggest specific sources to find)
4. Concepts mentioned but lacking depth

Wiki pages (sample of {len(sample)} pages):
{pages_context}

Return a markdown lint report with these sections:
## Contradictions
## Stale Content
## Data Gaps & Suggested Sources
## Concepts Needing More Depth

Be specific — name the exact pages and claims involved.
"""}]
        )
        semantic_report = response.choices[0].message.content
    else:
        response = client.messages.create(
            model=model,
            max_tokens=3000,
            messages=[{"role": "user", "content": f"""You are linting an LLM Wiki. Review the pages below and identify:
1. Contradictions between pages (claims that conflict)
2. Stale content (summaries that newer sources have superseded)
3. Data gaps (important questions the wiki can't answer — suggest specific sources to find)
4. Concepts mentioned but lacking depth

Wiki pages (sample of {len(sample)} pages):
{pages_context}

Return a markdown lint report with these sections:
## Contradictions
## Stale Content
## Data Gaps & Suggested Sources
## Concepts Needing More Depth

Be specific — name the exact pages and claims involved.
"""}]
        )
        semantic_report = response.content[0].text

    # Compose full report
    report_lines = [
        f"# Wiki Lint Report — {today}",
        "",
        f"Scanned {len(pages)} pages.",
        "",
        "## Structural Issues",
        "",
    ]

    if orphans:
        report_lines.append("### Orphan Pages (no inbound links)")
        for p in orphans:
            report_lines.append(f"- `{p.relative_to(REPO_ROOT)}`")
        report_lines.append("")

    if broken:
        report_lines.append("### Broken Wikilinks")
        for page, link in broken:
            report_lines.append(f"- `{page.relative_to(REPO_ROOT)}` links to `[[{link}]]` — not found")
        report_lines.append("")

    if missing_entities:
        report_lines.append("### Missing Entity Pages (mentioned 3+ times but no page)")
        for name in missing_entities:
            report_lines.append(f"- `[[{name}]]`")
        report_lines.append("")

    if claim_contradictions:
        report_lines.append("### 跨源声明矛盾（来自 claims.json）")
        for c in claim_contradictions:
            report_lines.append(c)
        report_lines.append("")

    if not orphans and not broken and not missing_entities and not claim_contradictions:
        report_lines.append("未发现结构性问题。")
        report_lines.append("")

    report_lines.append("---")
    report_lines.append("")
    report_lines.append(semantic_report)

    report = "\n".join(report_lines)
    print("\n" + report)
    return report


def append_log(entry: str):
    existing = read_file(LOG_FILE)
    LOG_FILE.write_text(entry.strip() + "\n\n" + existing, encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lint the LLM Wiki")
    parser.add_argument("--save", action="store_true", help="Save lint report to wiki/lint-report.md")
    args = parser.parse_args()

    report = run_lint()

    if args.save and report:
        report_path = WIKI_DIR / "lint-report.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\nSaved: {report_path.relative_to(REPO_ROOT)}")

    today = date.today().isoformat()
    append_log(f"## [{today}] lint | Wiki health check\n\nRan lint. See lint-report.md for details.")
