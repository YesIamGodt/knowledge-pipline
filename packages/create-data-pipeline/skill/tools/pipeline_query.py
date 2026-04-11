#!/usr/bin/env python3
"""
Query the LLM Wiki.

Usage:
    python tools/pipeline_query.py "What are the main themes across all sources?"
    python tools/pipeline_query.py "How does ConceptA relate to ConceptB?" --save
    python tools/pipeline_query.py "question" --reasoning-chain

Flags:
    --save              Save the answer back into the wiki (prompts for filename)
    --save <path>       Save to a specific wiki path
    --reasoning-chain   Show deep reasoning chain with subgraph visualization
    --rc                Alias for --reasoning-chain
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

# LLM configuration — initialized lazily in query() to allow --help without config
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
GRAPH_DIR = REPO_ROOT / "graph"
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


# ============================================================
#  深度推理链（Deep Reasoning Chain）
# ============================================================

def _load_graph():
    """加载 graph.json，返回 (nodes_dict, adjacency)。"""
    graph_file = GRAPH_DIR / "graph.json"
    if not graph_file.exists():
        return {}, {}
    data = json.loads(graph_file.read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in data.get("nodes", [])}
    adj = {}  # id -> [(neighbor_id, edge_info), ...]
    for e in data.get("edges", []):
        adj.setdefault(e["from"], []).append((e["to"], e))
        adj.setdefault(e["to"], []).append((e["from"], e))
    return nodes, adj


def _page_id_from_path(p: Path) -> str:
    """wiki/concepts/RAG.md -> concepts/RAG"""
    rel = p.relative_to(WIKI_DIR)
    return str(rel).replace("\\", "/").replace(".md", "")


def _find_reasoning_paths(relevant_pages: list[Path], nodes: dict, adj: dict) -> list[dict]:
    """
    从相关页面中提取节点，在图上做 BFS 找页面间的连接路径。
    返回 reasoning steps 列表（去重、限制数量）。
    """
    page_ids = set()
    for p in relevant_pages:
        pid = _page_id_from_path(p)
        if pid in nodes:
            page_ids.add(pid)

    if len(page_ids) < 2:
        return []

    # 优先选取概念和实体节点（而非源文档），推理链更有意义
    concept_entity_ids = [pid for pid in page_ids
                          if nodes.get(pid, {}).get("type") in ("concept", "entity")]
    source_ids = [pid for pid in page_ids
                  if nodes.get(pid, {}).get("type") == "source"]

    # 先在概念/实体间找路径，再从源到概念找路径
    priority_pairs = []
    for i, a in enumerate(concept_entity_ids):
        for b in concept_entity_ids[i + 1:]:
            priority_pairs.append((a, b))
    for src in source_ids[:4]:  # 限制源数量
        for ce in concept_entity_ids[:6]:
            priority_pairs.append((src, ce))

    # BFS 找路径（最多 3 跳，精简图谱）
    paths_found = []
    for src, dst in priority_pairs:
        if len(paths_found) >= 8:  # 最多 8 条路径
            break
        path = _bfs(src, dst, adj, max_depth=3)
        if path and len(path) > 1:
            paths_found.append(path)

    # 构建推理步骤（全局边去重）
    steps = []
    seen_edges = set()
    for path in paths_found:
        for k in range(len(path) - 1):
            edge_key = tuple(sorted([path[k], path[k + 1]]))
            if edge_key in seen_edges:
                continue
            seen_edges.add(edge_key)
            # 找到对应边信息
            edge_info = None
            for nb, e in adj.get(path[k], []):
                if nb == path[k + 1]:
                    edge_info = e
                    break
            src_node = nodes.get(path[k], {})
            dst_node = nodes.get(path[k + 1], {})

            # 推导边的语义描述：读取源页面内容查找上下文
            edge_label = _infer_edge_label(path[k], path[k + 1], edge_info, nodes)

            steps.append({
                "from_id": path[k],
                "from_label": src_node.get("label", path[k]),
                "from_type": src_node.get("type", "unknown"),
                "to_id": path[k + 1],
                "to_label": dst_node.get("label", path[k + 1]),
                "to_type": dst_node.get("type", "unknown"),
                "edge_type": edge_info.get("type", "UNKNOWN") if edge_info else "UNKNOWN",
                "edge_label": edge_label,
                "confidence": edge_info.get("confidence", 1.0) if edge_info else 1.0,
            })
        if len(steps) >= 15:  # 总步骤上限
            break
    return steps


def _infer_edge_label(from_id: str, to_id: str, edge_info: dict | None, nodes: dict) -> str:
    """推导边的语义描述，而非简单的'提取链接'。"""
    if edge_info and edge_info.get("label") and edge_info["label"] not in ("提取链接", "EXTRACTED"):
        return edge_info["label"]

    # 根据节点类型推导关系语义
    ft = nodes.get(from_id, {}).get("type", "")
    tt = nodes.get(to_id, {}).get("type", "")
    fl = nodes.get(from_id, {}).get("label", from_id)
    tl = nodes.get(to_id, {}).get("label", to_id)

    if ft == "source" and tt == "concept":
        return f"论述了"
    elif ft == "source" and tt == "entity":
        return f"提及了"
    elif ft == "concept" and tt == "source":
        return f"出现于"
    elif ft == "entity" and tt == "source":
        return f"被记录于"
    elif ft == "concept" and tt == "concept":
        return f"关联概念"
    elif ft == "entity" and tt == "entity":
        return f"关联实体"
    elif ft == "entity" and tt == "concept":
        return f"涉及概念"
    elif ft == "concept" and tt == "entity":
        return f"相关实体"
    elif ft == "source" and tt == "source":
        return f"互相引用"
    elif tt == "synthesis" or ft == "synthesis":
        return f"综合于"
    else:
        return edge_info.get("label", "关联") if edge_info else "关联"


def _bfs(src: str, dst: str, adj: dict, max_depth: int = 4) -> list[str] | None:
    """BFS 找最短路径。"""
    if src == dst:
        return [src]
    queue = [(src, [src])]
    visited = {src}
    while queue:
        node, path = queue.pop(0)
        if len(path) > max_depth:
            continue
        for nb, _ in adj.get(node, []):
            if nb == dst:
                return path + [nb]
            if nb not in visited:
                visited.add(nb)
                queue.append((nb, path + [nb]))
    return None


TYPE_LABELS = {
    "source": "📄源",
    "entity": "🏢实体",
    "concept": "💡概念",
    "synthesis": "📝综合",
}


def _print_reasoning_chain(steps: list[dict], question: str):
    """在终端中用中文展示推理链。"""
    if not steps:
        return

    all_nodes = set()
    for s in steps:
        all_nodes.add(s["from_id"])
        all_nodes.add(s["to_id"])

    w = 60  # 框宽
    print()
    print(f"┌{'─' * w}┐")
    print(f"│{'🧠 深度推理链（Reasoning Chain）':^{w - 6}}│")
    print(f"├{'─' * w}┤")
    q_display = question[:48]
    print(f"│  ❓ {q_display:<{w - 5}}│")
    print(f"├{'─' * w}┤")

    for i, step in enumerate(steps):
        ft = TYPE_LABELS.get(step["from_type"], "❓")
        tt = TYPE_LABELS.get(step["to_type"], "❓")
        conf = step["confidence"]
        edge_desc = step["edge_label"]

        if i == 0:
            node_str = f"  {ft} {step['from_label']}"
            print(f"│{node_str:<{w}}│")

        # 边
        arrow = "──▶" if step["edge_type"] == "EXTRACTED" else "╌╌▶"
        conf_str = ""
        if conf < 1.0:
            conf_pct = int(conf * 100)
            conf_str = f" ({conf_pct}%)"
        edge_str = f"    ├{arrow} {edge_desc}{conf_str}"
        print(f"│{edge_str:<{w}}│")

        # 目标节点
        node_str = f"  {tt} {step['to_label']}"
        print(f"│{node_str:<{w}}│")

    print(f"├{'─' * w}┤")
    summary = f"  📊 {len(steps)} 条推理边 · {len(all_nodes)} 个知识节点"
    print(f"│{summary:<{w}}│")
    print(f"└{'─' * w}┘")
    print()


def _collect_subgraph(steps: list[dict], nodes: dict) -> tuple[list, list]:
    """从推理步骤中收集子图节点和边。"""
    sub_node_ids = set()
    sub_edges = []
    for s in steps:
        sub_node_ids.add(s["from_id"])
        sub_node_ids.add(s["to_id"])
        sub_edges.append({
            "from": s["from_id"],
            "to": s["to_id"],
            "type": s["edge_type"],
            "label": s["edge_label"] or s["edge_type"],
            "color": "#FF5722" if s["edge_type"] == "INFERRED" else "#4FC3F7",
            "confidence": s["confidence"],
            "width": 3,
            "arrows": "to",
        })
    sub_nodes = []
    for nid in sub_node_ids:
        n = nodes.get(nid, {"id": nid, "label": nid})
        sub_nodes.append({
            "id": n.get("id", nid),
            "label": n.get("label", nid),
            "type": n.get("type", "unknown"),
            "type_cn": n.get("type_cn", ""),
            "color": n.get("color", {"background": "#888"}),
            "path": n.get("path", ""),
        })
    return sub_nodes, sub_edges


def _generate_reasoning_html(sub_nodes: list, sub_edges: list, question: str,
                              steps: list[dict], answer: str) -> Path:
    """生成推理子图 HTML 可视化。"""
    out_path = GRAPH_DIR / "reasoning.html"
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    nodes_json = json.dumps(sub_nodes, ensure_ascii=False, indent=2)
    edges_json = json.dumps(sub_edges, ensure_ascii=False, indent=2)

    # 构建推理链 HTML
    chain_html_parts = []
    for i, s in enumerate(steps):
        ft = TYPE_LABELS.get(s["from_type"], "❓")
        tt = TYPE_LABELS.get(s["to_type"], "❓")
        conf = s["confidence"]
        conf_pct = int(conf * 100)
        edge_cls = "extracted" if s["edge_type"] == "EXTRACTED" else "inferred"
        if i == 0:
            chain_html_parts.append(
                f'<div class="chain-node type-{s["from_type"]}">{ft} {s["from_label"]}</div>')
        chain_html_parts.append(
            f'<div class="chain-edge {edge_cls}">'
            f'  <span class="edge-arrow">{"──▶" if edge_cls == "extracted" else "╌╌▶"}</span> '
            f'  <span class="edge-label">{s["edge_label"] or s["edge_type"]}</span>'
            f'  <span class="edge-conf">({conf_pct}%)</span>'
            f'</div>')
        chain_html_parts.append(
            f'<div class="chain-node type-{s["to_type"]}">{tt} {s["to_label"]}</div>')
    chain_html = "\n".join(chain_html_parts)

    # 答案 HTML — 转义基本 HTML 字符并转换 markdown 粗体/标题
    answer_html = (answer or "")
    answer_html = answer_html.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    answer_html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', answer_html)
    answer_html = re.sub(r'^### (.+)$', r'<h4>\1</h4>', answer_html, flags=re.MULTILINE)
    answer_html = re.sub(r'^## (.+)$', r'<h3>\1</h3>', answer_html, flags=re.MULTILINE)
    answer_html = re.sub(r'^# (.+)$', r'<h2>\1</h2>', answer_html, flags=re.MULTILINE)
    answer_html = re.sub(r'\[\[([^\]]+)\]\]', r'<code class="wikilink">[[\1]]</code>', answer_html)
    answer_html = answer_html.replace("\n", "<br>\n")

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>🧠 推理链 — {question[:60]}</title>
<style>
  * {{ margin: 0; padding: 0; box-sizing: border-box; }}
  body {{ background: #0d1117; color: #c9d1d9; font-family: "Microsoft YaHei", "PingFang SC", sans-serif; }}

  .layout {{ display: grid; grid-template-columns: 340px 1fr; grid-template-rows: auto 1fr auto; height: 100vh; }}
  .header {{ grid-column: 1 / -1; background: linear-gradient(135deg, #161b22 0%, #1a1f2e 100%);
             padding: 16px 24px; border-bottom: 1px solid #30363d; display: flex; align-items: center; gap: 16px; }}
  .header h1 {{ font-size: 18px; color: #58a6ff; }}
  .header .question {{ font-size: 14px; color: #8b949e; flex: 1; }}

  .sidebar {{ grid-row: 2 / 4; background: #161b22; border-right: 1px solid #30363d; overflow-y: auto; padding: 16px; }}
  .sidebar h2 {{ font-size: 15px; color: #58a6ff; margin-bottom: 12px; }}

  .chain-node {{ padding: 8px 12px; margin: 4px 0; border-radius: 6px; font-size: 13px; font-weight: 600; }}
  .type-source {{ background: #1a3a1a; border-left: 3px solid #4CAF50; color: #a3d9a5; }}
  .type-entity {{ background: #1a2a3a; border-left: 3px solid #2196F3; color: #90caf9; }}
  .type-concept {{ background: #3a2a0a; border-left: 3px solid #FF9800; color: #ffcc80; }}
  .type-synthesis {{ background: #2a1a3a; border-left: 3px solid #9C27B0; color: #ce93d8; }}
  .type-unknown {{ background: #2a2a2a; border-left: 3px solid #888; }}

  .chain-edge {{ padding: 2px 12px 2px 24px; font-size: 12px; color: #8b949e; }}
  .chain-edge.extracted {{ color: #4FC3F7; }}
  .chain-edge.inferred {{ color: #FF8A65; }}
  .edge-arrow {{ font-family: monospace; }}
  .edge-conf {{ font-size: 11px; color: #6e7681; }}

  #graph {{ min-height: 300px; border-bottom: 1px solid #30363d; position: relative; }}
  #graph-fallback {{ display: none; position: absolute; inset: 0; padding: 24px;
                     color: #8b949e; font-size: 13px; overflow-y: auto; }}
  #graph-fallback.show {{ display: block; }}
  #graph-fallback h3 {{ color: #58a6ff; margin-bottom: 12px; }}
  #graph-fallback .fb-node {{ display: inline-block; padding: 4px 10px; margin: 3px; border-radius: 4px; font-size: 12px; }}
  #graph-fallback .fb-edge {{ margin: 6px 0; padding-left: 16px; font-size: 12px; }}
  .fb-concept {{ background: #3a2a0a; color: #ffcc80; border: 1px solid #FF9800; }}
  .fb-source {{ background: #1a3a1a; color: #a3d9a5; border: 1px solid #4CAF50; }}
  .fb-entity {{ background: #1a2a3a; color: #90caf9; border: 1px solid #2196F3; }}

  .answer-panel {{ overflow-y: auto; padding: 16px 24px; max-height: 45vh;
                   background: #161b22; font-size: 13px; line-height: 1.7; }}
  .answer-panel h2, .answer-panel h3, .answer-panel h4 {{ color: #58a6ff; margin: 12px 0 6px; }}
  .answer-panel .wikilink {{ background: #1f2a3a; color: #79c0ff; padding: 1px 5px; border-radius: 3px; font-size: 12px; }}
  .answer-panel strong {{ color: #f0f6fc; }}

  .stats {{ padding: 8px 16px; font-size: 11px; color: #6e7681; border-top: 1px solid #21262d; }}
</style>
</head>
<body>
<div class="layout">
  <div class="header">
    <h1>🧠 深度推理链</h1>
    <div class="question">❓ {question}</div>
  </div>
  <div class="sidebar">
    <h2>推理路径</h2>
    {chain_html}
    <div class="stats">共 {len(steps)} 条路径 · {len(sub_nodes)} 个节点</div>
  </div>
  <div id="graph">
    <div id="graph-fallback">
      <h3>🔗 推理子图（文本模式）</h3>
      <p style="margin-bottom:12px;color:#6e7681;">vis.js 图形库加载失败，以文本形式展示关系：</p>
      {"".join(
        f'<div class="fb-edge">🔗 <span class="fb-node fb-{s["from_type"]}">{s["from_label"]}</span>'
        f' → <em>{s["edge_label"] or s["edge_type"]}</em> → '
        f'<span class="fb-node fb-{s["to_type"]}">{s["to_label"]}</span></div>'
        for s in steps
      )}
    </div>
  </div>
  <div class="answer-panel">
    <h2>💡 综合答案</h2>
    {answer_html}
  </div>
</div>
<script>
(function() {{
  var script = document.createElement('script');
  script.src = "https://cdn.jsdelivr.net/npm/vis-network@9/standalone/umd/vis-network.min.js";
  script.onload = function() {{
    var nodes = new vis.DataSet({nodes_json});
    var edges = new vis.DataSet({edges_json});
    var container = document.getElementById("graph");
    document.getElementById("graph-fallback").style.display = "none";
    var network = new vis.Network(container, {{ nodes: nodes, edges: edges }}, {{
      nodes: {{
        shape: "dot", size: 20,
        font: {{ color: "#c9d1d9", size: 14, face: "Microsoft YaHei" }},
        borderWidth: 3, borderWidthSelected: 5
      }},
      edges: {{
        width: 2.5,
        smooth: {{ type: "curvedCW", roundness: 0.15 }},
        arrows: {{ to: {{ enabled: true, scaleFactor: 0.8 }} }},
        font: {{ size: 11, color: "#8b949e", align: "middle" }}
      }},
      physics: {{
        stabilization: {{ iterations: 100 }},
        barnesHut: {{ gravitationalConstant: -5000, springLength: 160 }}
      }},
      interaction: {{ hover: true }}
    }});
  }};
  script.onerror = function() {{
    document.getElementById("graph-fallback").classList.add("show");
  }};
  document.head.appendChild(script);
}})();
</script>
</body>
</html>"""

    write_file(out_path, html)
    return out_path


def query(question: str, save_path: str | None = None, auto_save: bool = False,
          reasoning_chain: bool = False):
    # ========== 第一步：检查 LLM 配置 ==========
    _init_llm()

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

    # ========== 推理链（可选）==========
    reasoning_steps = []
    reasoning_context = ""
    if reasoning_chain:
        print("\n  🧠 构建深度推理链...")
        graph_nodes, graph_adj = _load_graph()
        if graph_nodes:
            reasoning_steps = _find_reasoning_paths(relevant_pages, graph_nodes, graph_adj)
            if reasoning_steps:
                _print_reasoning_chain(reasoning_steps, question)
                # 将推理链作为额外上下文注入 LLM
                rc_lines = []
                for s in reasoning_steps:
                    rc_lines.append(
                        f"  {s['from_label']}({s['from_type']}) "
                        f"─[{s['edge_label'] or s['edge_type']}]→ "
                        f"{s['to_label']}({s['to_type']})"
                    )
                reasoning_context = (
                    "\n\n知识图谱推理路径（请基于这些关联进行深度推理）：\n"
                    + "\n".join(rc_lines)
                )
            else:
                print("  ⚠️ 未找到跨页面推理路径（图谱可能需要重建：/pipeline-graph）")
        else:
            print("  ⚠️ 知识图谱不存在，请先运行 /pipeline-graph 构建")

    # Step 4: Synthesize answer
    print(f"  synthesizing answer from {len(relevant_pages)} pages...")

    synthesis_prompt = f"""你正在查询一个 LLM 维基来回答问题。使用下面的维基页面综合一个详尽的答案。

维基页面：
{pages_context}
{claims_context}
{source_perspectives}
{reasoning_context}

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

    # 推理链子图可视化
    if reasoning_chain and reasoning_steps:
        graph_nodes, _ = _load_graph()
        sub_nodes, sub_edges = _collect_subgraph(reasoning_steps, graph_nodes)
        html_path = _generate_reasoning_html(sub_nodes, sub_edges, question, reasoning_steps, answer)
        print(f"\n  📊 推理子图已生成：{html_path.relative_to(REPO_ROOT)}")
        # 尝试打开浏览器
        try:
            import webbrowser
            webbrowser.open(str(html_path))
            print("  🌐 已在浏览器中打开")
        except Exception:
            pass

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
    parser.add_argument("--reasoning-chain", "--rc", action="store_true",
                        help="展示深度推理链并生成推理子图可视化")
    args = parser.parse_args()
    query(args.question, args.save, auto_save=args.auto_save,
          reasoning_chain=args.reasoning_chain)
