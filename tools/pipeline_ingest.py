#!/usr/bin/env python3
"""
Ingest a source document into the LLM Wiki using multi-modal pipeline.

Usage:
    python tools/pipeline_ingest.py <path-to-source>
    python tools/pipeline_ingest.py raw/articles/my-article.md

This multi-modal pipeline supports:
  - Text files (.md, .txt)
  - PDF documents (.pdf)
  - Word documents (.docx)
  - Excel spreadsheets (.xlsx)
  - Images (.jpg, .png, .webp) with OCR
  - PowerPoint files (.pptx)
  - HTML files (.html, .htm)
  - Video files (.mp4, .avi, .mov, .mkv, etc.) with keyframe extraction

The pipeline reads the source, extracts knowledge, and updates the wiki:
  - Creates wiki/sources/<slug>.md
  - Updates wiki/index.md
  - Updates wiki/overview.md (if warranted)
  - Creates/updates entity and concept pages
  - Appends to wiki/log.md
  - Flags contradictions
"""

import os
import sys
import json
import hashlib
import re
import time
from pathlib import Path
from datetime import date

# --- 流式进度输出 ---
def progress(msg: str):
    """实时输出进度信息到 stderr（不会被管道吞掉）"""
    ts = time.strftime("%H:%M:%S")
    print(f"  [{ts}] {msg}", flush=True)

# Add parent directory to path for backend imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from backend.processors import FileProcessor
    HAS_BACKEND = True
except ImportError:
    HAS_BACKEND = False
    print("Warning: backend.processors not available. Falling back to text-only mode.")

try:
    from core.retrieval import BM25Index, build_wiki_index, tokenize
    HAS_BM25 = True
except ImportError:
    HAS_BM25 = False

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
LOG_FILE = WIKI_DIR / "log.md"
INDEX_FILE = WIKI_DIR / "index.md"
OVERVIEW_FILE = WIKI_DIR / "overview.md"
SCHEMA_FILE = REPO_ROOT / "CLAUDE.md"


def sha256(text: str) -> str:
    # 清理代理字符，避免编码错误
    text = text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore')
    return hashlib.sha256(text.encode()).hexdigest()[:16]


def clean_text(text: str) -> str:
    """清理文本中的无效字符"""
    # 移除代理字符（Python 内部使用的 Unicode 代理对）
    import re
    # 移除孤立的高/低代理值
    text = re.sub(r'[\ud800-\udfff]', '', text)
    return text


def read_file(path: Path) -> str:
    content = path.read_text(encoding="utf-8") if path.exists() else ""
    # 清理文本中的无效字符
    return clean_text(content)


def write_file(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"  wrote: {path.relative_to(REPO_ROOT)}")


def extract_keywords(content: str) -> list:
    """简单的关键词提取（可改进点：使用更复杂的 NLP 方法）"""
    # 常见的停用词（英文 + 中文）
    stopwords = set([
        # 英文停用词
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'for', 'with',
        'is', 'are', 'was', 'were', 'be', 'been', 'being', 'to', 'of', 'by',
        'from', 'up', 'down', 'over', 'under', 'again', 'further', 'then',
        'once', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
        'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
        # 中文停用词
        '的', '了', '和', '是', '在', '有', '这', '那', '我', '你', '他',
        '她', '它', '们', '与', '或', '但', '而', '也', '都', '就', '也',
        '很', '太', '最', '更', '还', '再', '又', '也', '就', '才', '已',
        '已经', '正在', '将要', '会', '能', '可以', '应该', '必须', '需要',
        '这个', '那个', '这些', '那些', '什么', '怎么', '为什么', '哪里',
        '因为', '所以', '如果', '虽然', '但是', '而且', '或者', '还是',
        '之一', '之一', '方面', '部分', '整体', '全部', '一些', '一点',
        '进行', '实施', '开展', '推进', '落实', '执行', '完成', '实现',
        '新', '最新', '最近', '现在', '今天', '明天', '昨天', '时候', '时间',
        '推出', '发布', '宣布', '表示', '说', '认为', '指出', '说明', '解释'
    ])

    import re

    # 提取英文单词和中文字符序列
    # 英文单词：\w+
    # 中文字符序列：[\u4e00-\u9fff]+
    words = []

    # 提取英文单词
    english_words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9]*\b', content.lower())
    words.extend(english_words)

    # 提取中文序列（简化版）
    # 对于中文，我们可以用更简单的方法：找常见的专有名词
    # 这里简化处理：提取长度为 2-5 的中文序列
    chinese_chars = re.findall(r'[\u4e00-\u9fff]+', content)
    for seq in chinese_chars:
        if 2 <= len(seq) <= 10:  # 只保留 2-10 字的序列
            words.append(seq)

    # 也添加一些明显的产品名（包含数字和字母组合的）
    product_names = re.findall(r'[a-zA-Z0-9\-]+', content)
    for name in product_names:
        if 2 <= len(name) <= 20 and '-' in name or any(c.isdigit() for c in name):
            words.append(name.lower())

    # 过滤停用词和短词，统计频率
    word_counts = {}
    for word in words:
        if (len(word) >= 2 and  # 至少 2 个字符
            word not in stopwords and  # 不是停用词
            not word.isdigit()):  # 不是纯数字
            word_counts[word] = word_counts.get(word, 0) + 1

    # 取频率最高的前 20 个词作为关键词
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, count in sorted_words[:20]]

    return keywords


def calculate_relevance_score(keywords: list, content: str) -> int:
    """计算内容与关键词的相关性分数"""
    score = 0
    content_lower = content.lower()

    for keyword in keywords:
        # 简单的词频统计
        score += content_lower.count(keyword)

    return score


def find_relevant_sources(new_content: str, all_sources: list, max_results: int = 10) -> list:
    """
    找到与新内容相关的源（BM25 + 关键词混合检索）

    优先使用 BM25 评分，回退到简单关键词匹配。
    """
    if HAS_BM25 and len(all_sources) >= 2:
        try:
            index = BM25Index()
            for source_path in all_sources:
                try:
                    content = source_path.read_text(encoding="utf-8")
                    index.add(str(source_path), content)
                except Exception:
                    pass

            # 用新内容的前 3000 字作为查询
            query_text = new_content[:3000]
            results = index.search(query_text, top_k=max_results)
            ranked = [Path(doc_id) for doc_id, score in results if score > 0]
            if ranked:
                return ranked[:max_results]
        except Exception as e:
            print(f"  ⚠️ BM25 检索失败: {e}，回退到关键词匹配")

    # 回退：简单关键词匹配
    keywords = extract_keywords(new_content)
    scored_sources = []
    for source_path in all_sources:
        try:
            content = source_path.read_text()
            score = calculate_relevance_score(keywords, content)
            if score > 0:
                scored_sources.append((score, source_path))
        except Exception as e:
            print(f"  ⚠️ 读取源文件失败: {source_path}: {e}")
    scored_sources.sort(reverse=True, key=lambda x: x[0])
    return [path for (score, path) in scored_sources[:max_results]]


def build_wiki_context(new_source_content: str) -> str:
    """
    构建维基上下文，用于给 LLM 提供背景信息

    改进：现在会智能检索相关源（不只是最近的），用于更好的矛盾检测
    """
    parts = []

    # 1. 总是包含索引和概览
    if INDEX_FILE.exists():
        parts.append(f"## wiki/index.md\n{read_file(INDEX_FILE)}")
    if OVERVIEW_FILE.exists():
        parts.append(f"## wiki/overview.md\n{read_file(OVERVIEW_FILE)}")

    sources_dir = WIKI_DIR / "sources"
    if sources_dir.exists():
        all_sources = list(sources_dir.glob("*.md"))

        # 智能检索相关源
        relevant_sources = find_relevant_sources(new_source_content, all_sources, max_results=10)

        if relevant_sources:
            print(f"  找到 {len(relevant_sources)} 个相关源用于矛盾检测")
            for p in relevant_sources:
                parts.append(f"## {p.relative_to(REPO_ROOT)}\n{p.read_text()}")

        # 补充最近的 3 个源（以防万一）
        recent = sorted(
            all_sources,
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )[:3]

        for p in recent:
            # 避免重复
            already_included = any(str(p) in part for part in parts)
            if not already_included:
                parts.append(f"## {p.relative_to(REPO_ROOT)}\n{p.read_text()}")
                print(f"  补充最近的源: {p.name}")

    return "\n\n---\n\n".join(parts)


def parse_json_from_response(text: str) -> dict:
    # Strip markdown code fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text.strip())
    text = re.sub(r"\s*```$", "", text.strip())
    # Find the outermost JSON object
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        raise ValueError("No JSON object found in response")
    return json.loads(match.group())


def update_index(new_entry: str, section: str = "Sources"):
    content = read_file(INDEX_FILE)
    if not content:
        content = "# Wiki Index\n\n## Overview\n- [Overview](overview.md) — living synthesis\n\n## Sources\n\n## Entities\n\n## Concepts\n\n## Syntheses\n"
    section_header = f"## {section}"
    if section_header in content:
        # 避免重复条目
        # 提取 entry 中的路径部分（如 sources/slug.md）
        entry_path_match = re.search(r'\(([^)]+)\)', new_entry)
        if entry_path_match:
            entry_path = entry_path_match.group(1)
            if entry_path in content:
                return  # 已存在，跳过
        content = content.replace(section_header + "\n", section_header + "\n" + new_entry + "\n")
    else:
        content += f"\n{section_header}\n{new_entry}\n"
    write_file(INDEX_FILE, content)


def append_log(entry: str):
    existing = read_file(LOG_FILE)
    write_file(LOG_FILE, entry.strip() + "\n\n" + existing)


def process_source_with_backend(source_path: str) -> tuple[str, dict]:
    """Process source file using backend multi-modal processors."""
    if not HAS_BACKEND:
        # Fallback to text-only mode
        source = Path(source_path)
        return source.read_text(encoding="utf-8"), {"source": str(source), "type": "text"}

    source_ext = Path(source_path).suffix.lower()
    pdf_strategy = os.getenv("PIPELINE_PDF_STRATEGY", "balanced").lower()
    enable_multimodal = True

    if source_ext == ".pdf":
        # fast: 纯文本优先；balanced/accurate: 启用多模态图片理解
        if pdf_strategy == "fast":
            enable_multimodal = False
            print("  PDF strategy=fast: using text-first parser only")
        elif pdf_strategy in ("balanced", "accurate"):
            enable_multimodal = True
            print(f"  PDF strategy={pdf_strategy}: multimodal image understanding enabled")
        else:
            print(f"  Unknown PIPELINE_PDF_STRATEGY={pdf_strategy}, fallback to balanced")
            enable_multimodal = True

    processor = FileProcessor(use_multimodal=enable_multimodal)
    result = processor.process(source_path)

    if result.errors:
        print(f"  ⚠️  Processing warnings:")
        for error in result.errors:
            print(f"     - {error}")

    # Build enhanced content with tables if available
    content_parts = [result.content]
    if result.tables:
        content_parts.append("\n\n## 提取的表格\n")
        for table in result.tables:
            content_parts.append(table)

    full_content = "\n".join(content_parts)
    # 清理文本中的无效字符
    full_content = clean_text(full_content)
    return full_content, result.metadata


def ingest(source_path: str):
    source = Path(source_path)
    if not source.exists():
        print(f"Error: file not found: {source_path}")
        sys.exit(1)

    # ========== 第一步：检查 LLM 配置 ==========
    from core.llm_config import require_llm_config, LLMConfig
    require_llm_config()

    # 加载配置并初始化客户端
    llm_config = LLMConfig()
    cfg = llm_config.get_config()
    import openai
    client = openai.OpenAI(
        base_url=cfg.get("LLM_BASE_URL"),
        api_key=cfg.get("OPENAI_API_KEY")
    )
    model = cfg.get("LLM_MODEL", "gpt-4o-mini")
    use_openai = True

    # Process source file with multi-modal pipeline
    print(f"\n📂 处理文件: {source.name}")
    t0 = time.time()
    source_content, metadata = process_source_with_backend(str(source))

    if not source_content.strip():
        print(f"Error: could not extract content from {source.name}")
        sys.exit(1)

    t_extract = time.time() - t0
    progress(f"✓ 提取完成: {len(source_content)} 字符 ({t_extract:.1f}s)")

    source_hash = sha256(source_content)
    today = date.today().isoformat()

    print(f"\n🔄 摄入: {source.name}  (hash: {source_hash})")

    progress("构建维基上下文...")
    t1 = time.time()
    wiki_context = build_wiki_context(source_content)
    progress(f"上下文就绪: {len(wiki_context)} 字符 ({time.time()-t1:.1f}s)")

    schema = read_file(SCHEMA_FILE)

    # 限制 prompt 体积，避免大文档导致 LLM 响应过慢。
    source_prompt_content = source_content
    source_trimmed = False
    source_prompt_limit = int(os.getenv("PIPELINE_SOURCE_PROMPT_MAX_CHARS", "60000"))
    if len(source_prompt_content) > source_prompt_limit:
        keep_head = int(source_prompt_limit * 0.7)
        keep_tail = source_prompt_limit - keep_head
        source_prompt_content = (
            source_prompt_content[:keep_head]
            + "\n\n...[内容过长，已截断中间部分以提升处理速度]...\n\n"
            + source_prompt_content[-keep_tail:]
        )
        source_trimmed = True

    wiki_prompt_context = wiki_context
    context_trimmed = False
    context_prompt_limit = int(os.getenv("PIPELINE_CONTEXT_PROMPT_MAX_CHARS", "30000"))
    if len(wiki_prompt_context) > context_prompt_limit:
        wiki_prompt_context = wiki_prompt_context[:context_prompt_limit] + "\n\n...[上下文过长，已截断]..."
        context_trimmed = True

    if source_trimmed:
        print(f"  source content trimmed for prompt: {len(source_content)} -> {len(source_prompt_content)} chars")
    if context_trimmed:
        print(f"  wiki context trimmed for prompt: {len(wiki_context)} -> {len(wiki_prompt_context)} chars")

    # Build metadata description for prompt
    metadata_desc = ""
    if metadata:
        metadata_desc = "\nFile metadata:\n" + "\n".join(f"- {k}: {v}" for k, v in metadata.items())

    prompt = f"""你正在维护一个 LLM 维基。请处理这个源文档并将其知识整合到维基中。

维基架构和规范：
{schema}

当前维基状态（索引 + 最近页面）：
{wiki_prompt_context if wiki_prompt_context else "(维基是空的 — 这是第一个源)"}

要摄入的新源（文件：{source.relative_to(REPO_ROOT) if source.is_relative_to(REPO_ROOT) else source.name}）：
{metadata_desc}

=== 源内容开始 ===
{source_prompt_content}
=== 源内容结束 ===

今天日期：{today}

**重要规则：**
1. 生成的 entity_pages 和 concept_pages 中，每个页面的 frontmatter 必须包含 `sources: ["{source.name}"]` 字段
2. 请在 source_page 的 Key Claims 部分提取 3-8 项关键可验证主张（含数值指标、关键结论等），这些主张用于跨源矛盾检测
3. 仔细对比现有维基内容，检测任何事实矛盾、数值冲突或结论分歧，不只是表面文字矛盾
4. 如果源文档包含图片/视频/音频描述内容，注意跨模态信息的关联（如：图片中出现的人物、场景与文字描述的对应）

只返回一个有效的 JSON 对象（不要 markdown 代码块，JSON 外不要有其他文字）：
{{
  "title": "这个源的人类可读标题",
  "slug": "文件名用的 kebab-case 标识",
  "source_page": "wiki/sources/<slug>.md 的完整 markdown 内容 — 使用架构中定义的源页面格式。Key Claims 部分必须包含 3-8 项可验证主张",
  "index_entry": "- [标题](sources/slug.md) — 单行摘要",
  "overview_update": "wiki/overview.md 的完整更新内容，如果不需要更新则为 null",
  "entity_pages": [
    {{"path": "entities/EntityName.md", "content": "完整的 markdown 内容（frontmatter 包含 sources 字段）"}}
  ],
  "concept_pages": [
    {{"path": "concepts/ConceptName.md", "content": "完整的 markdown 内容（frontmatter 包含 sources 字段）"}}
  ],
  "key_claims": [
    {{"claim": "可验证的关键主张", "type": "factual|numerical|opinion", "confidence": 0.9}}
  ],
  "contradictions": ["描述与现有维基内容的任何矛盾（包含来源页面名称），或者空数组"],
  "cross_references": ["发现的跨源关联描述，如 '本源的 X 概念与 [[Y页面]] 的 Z 概念密切相关'"],
  "log_entry": "## [{today}] ingest | <标题>\\n\\n添加了源。主要观点：..."
}}
"""

    progress(f"📡 调用 LLM API ({model})...")
    t2 = time.time()
    if use_openai:
        response = client.chat.completions.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content
    else:
        response = client.messages.create(
            model=model,
            max_tokens=8192,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.content[0].text

    progress(f"LLM 响应完成 ({time.time()-t2:.1f}s, {len(raw)} 字符)")

    try:
        data = parse_json_from_response(raw)
    except (ValueError, json.JSONDecodeError) as e:
        print(f"Error parsing API response: {e}")
        print("Raw response saved to /tmp/ingest_debug.txt")
        Path("/tmp/ingest_debug.txt").write_text(raw)
        sys.exit(1)

    # Write source page
    progress("写入维基页面...")
    slug = data["slug"]
    write_file(WIKI_DIR / "sources" / f"{slug}.md", data["source_page"])

    # --- 知识融合：更新已有实体/概念页面，而非覆盖 ---
    merge_stats = {"created": 0, "merged": 0}

    for page in data.get("entity_pages", []):
        _merge_or_create_page(page, source.name, today, merge_stats, client, model, use_openai)

    for page in data.get("concept_pages", []):
        _merge_or_create_page(page, source.name, today, merge_stats, client, model, use_openai)

    if merge_stats["merged"] > 0:
        progress(f"🔗 知识融合: {merge_stats['merged']} 个已有页面被更新，{merge_stats['created']} 个新页面创建")
    elif merge_stats["created"] > 0:
        progress(f"📝 新建 {merge_stats['created']} 个实体/概念页面")

    # Update overview
    if data.get("overview_update"):
        write_file(OVERVIEW_FILE, data["overview_update"])

    # Update index
    update_index(data["index_entry"], section="Sources")

    # Update index for entity/concept pages
    for page in data.get("entity_pages", []):
        path = page["path"]
        name = Path(path).stem
        if "entities/" in path:
            update_index(f"- [{name}]({path}) — entity", section="Entities")
        elif "concepts/" in path:
            update_index(f"- [{name}]({path}) — concept", section="Concepts")

    for page in data.get("concept_pages", []):
        path = page["path"]
        name = Path(path).stem
        if "concepts/" in path:
            update_index(f"- [{name}]({path}) — concept", section="Concepts")

    # Append log
    append_log(data["log_entry"])

    # Report contradictions from LLM
    contradictions = data.get("contradictions", [])
    if contradictions:
        print("\n  ⚠️  LLM 检测到的矛盾:")
        for c in contradictions:
            print(f"     - {c}")

    # Report cross-references
    cross_refs = data.get("cross_references", [])
    if cross_refs:
        print("\n  🔗 发现的跨源关联:")
        for cr in cross_refs:
            print(f"     - {cr}")

    # Save key_claims to structured file for cross-source contradiction detection
    key_claims = data.get("key_claims", [])
    if key_claims:
        claims_file = WIKI_DIR / "claims.json"
        existing_claims = {}
        if claims_file.exists():
            try:
                existing_claims = json.loads(claims_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, IOError):
                existing_claims = {}
        existing_claims[slug] = {
            "title": data["title"],
            "claims": key_claims,
            "date": today,
        }
        claims_file.write_text(json.dumps(existing_claims, indent=2, ensure_ascii=False), encoding="utf-8")
        progress(f"✓ 保存 {len(key_claims)} 条关键主张到 claims.json")

    # --- 主动矛盾检测：用本次新 claims 对比所有已有 claims ---
    _run_post_ingest_contradiction_check(slug, key_claims, client, model, use_openai)

    print(f"\n✅ 完成。摄入: {data['title']}  (总耗时 {time.time()-t0:.1f}s)")


def _merge_or_create_page(page: dict, source_name: str, today: str,
                          stats: dict, client, model: str, use_openai: bool):
    """
    知识融合核心逻辑：如果目标页面已存在，用 LLM 合并新旧内容；否则直接创建。

    合并策略：
    1. 保留旧页面的所有信息
    2. 追加新源的信息
    3. 更新 frontmatter 的 sources 列表
    4. 去重并统一格式
    """
    target_path = WIKI_DIR / page["path"]
    new_content = page["content"]

    if not target_path.exists():
        # 新页面，直接创建
        write_file(target_path, new_content)
        stats["created"] += 1
        return

    # 已有页面 → 需要合并
    existing_content = read_file(target_path)
    page_name = Path(page["path"]).stem

    progress(f"🔄 融合已有页面: {page_name}")

    # 构建合并 prompt
    merge_prompt = f"""你正在维护一个知识维基。页面 "{page_name}" 已经存在。现在有来自新源的补充信息需要合并进去。

**当前页面内容：**
{existing_content}

**新源提供的内容：**
{new_content}

**合并规则：**
1. 保留当前页面的所有已有信息，不要删除任何内容
2. 将新源的新增信息合并到对应章节中
3. 如果新源与已有信息有矛盾，两者都保留，并在旁边用 `⚠️ 矛盾` 标注
4. 更新 frontmatter 的 `sources` 列表，追加新源名称 "{source_name}"
5. 更新 `last_updated` 为 "{today}"
6. 去除重复信息
7. 保持页面格式一致

直接返回合并后的完整 markdown 内容（包括 frontmatter），不要加代码块包裹。"""

    try:
        if use_openai:
            response = client.chat.completions.create(
                model=model, max_tokens=4096,
                messages=[{"role": "user", "content": merge_prompt}],
            )
            merged = response.choices[0].message.content
        else:
            response = client.messages.create(
                model=model, max_tokens=4096,
                messages=[{"role": "user", "content": merge_prompt}],
            )
            merged = response.content[0].text

        # 清理可能的代码块包裹
        merged = re.sub(r'^```(?:markdown|md)?\s*\n?', '', merged.strip())
        merged = re.sub(r'\n?```\s*$', '', merged.strip())

        write_file(target_path, merged)
        stats["merged"] += 1
    except Exception as e:
        print(f"    ⚠️ 合并失败 ({page_name}): {e}，使用覆盖模式")
        write_file(target_path, new_content)
        stats["created"] += 1


def _run_post_ingest_contradiction_check(new_slug: str, new_claims: list,
                                          client, model: str, use_openai: bool):
    """
    主动矛盾报告：摄入后自动检查新 claims 与所有已有 claims 的冲突。

    不再被动等待下次 lint，而是立即告诉用户"你刚摄入的文档与第 X 源有冲突"。
    """
    claims_file = WIKI_DIR / "claims.json"
    if not claims_file.exists() or not new_claims:
        return

    try:
        all_claims = json.loads(claims_file.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, IOError):
        return

    # 至少需要 2 个源才能对比
    if len(all_claims) < 2:
        return

    # 构建新源的 claims 文本
    new_claims_text = "\n".join(
        f"[{new_slug}] {c['claim']}" if isinstance(c, dict) else f"[{new_slug}] {c}"
        for c in new_claims
    )

    # 构建其他源的 claims 文本（最多取最相关的 5 个源）
    other_claims = []
    for slug, claim_data in all_claims.items():
        if slug == new_slug:
            continue
        claims_list = claim_data.get("claims", claim_data) if isinstance(claim_data, dict) else claim_data
        if isinstance(claims_list, list):
            for c in claims_list:
                claim_text = c["claim"] if isinstance(c, dict) else str(c)
                other_claims.append(f"[{slug}] {claim_text}")

    if not other_claims:
        return

    # 限制数量
    other_claims_text = "\n".join(other_claims[:40])

    progress("🔍 主动矛盾检测: 对比新旧 claims...")

    prompt = f"""以下是维基中的两组声明。请识别它们之间的矛盾或冲突。

**新摄入的声明（来自 {new_slug}）：**
{new_claims_text}

**已有声明（来自其他源）：**
{other_claims_text}

如果发现矛盾，按以下格式输出：
## ⚠️ 矛盾发现
- **冲突 1**: [源A] 的声明 X 与 [源B] 的声明 Y 矛盾 — 简要说明差异
- **冲突 2**: ...

如果发现有趣的跨源佐证（多个源互相支持的观点），也列出：
## ✅ 跨源佐证
- [源A] 和 [源B] 都提到了 Z — 增强该观点可信度

如果没有发现矛盾，回复「未发现跨源矛盾」。"""

    try:
        if use_openai:
            response = client.chat.completions.create(
                model=model, max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.choices[0].message.content
        else:
            response = client.messages.create(
                model=model, max_tokens=2000,
                messages=[{"role": "user", "content": prompt}],
            )
            result = response.content[0].text

        if "未发现" not in result:
            print(f"\n{'='*60}")
            print("📋 主动矛盾检测报告")
            print(f"{'='*60}")
            print(result)
            print(f"{'='*60}")

            # 追加到 log
            append_log(f"## [{date.today().isoformat()}] contradiction-check | {new_slug}\n\n{result}")
        else:
            progress("✅ 未发现跨源矛盾")

    except Exception as e:
        print(f"    ⚠️ 矛盾检测失败: {e}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python tools/pipeline_ingest.py <path-to-source>")
        sys.exit(1)
    ingest(sys.argv[1])
