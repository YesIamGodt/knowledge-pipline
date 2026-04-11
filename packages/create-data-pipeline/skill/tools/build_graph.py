#!/usr/bin/env python3
"""
Build the knowledge graph from the wiki.

Usage:
    python tools/build_graph.py               # full rebuild (uses default LLM)
    python tools/build_graph.py --no-infer    # skip semantic inference (faster)
    python tools/build_graph.py --open        # open graph.html in browser after build

Environment Variables (optional):
    LLM_PROVIDER    - claude (default), openai, ollama
    LLM_MODEL       - model name (auto-detected if not set)
    LLM_BASE_URL    - for Ollama (default: http://localhost:11434) or OpenAI-compatible endpoints
    ANTHROPIC_API_KEY  - for Claude (reads from ~/.config/anthropic/config.json if not set)
    OPENAI_API_KEY  - for OpenAI

Examples:
    # Use Claude (default)
    python tools/build_graph.py

    # Use OpenAI
    LLM_PROVIDER=openai LLM_MODEL=gpt-4o-mini python tools/build_graph.py

    # Use local Ollama
    LLM_PROVIDER=ollama LLM_MODEL=llama3.2 python tools/build_graph.py

    # Use OpenAI-compatible endpoint (e.g., vLLM, LocalAI)
    LLM_PROVIDER=openai LLM_BASE_URL=http://localhost:8000/v1 LLM_MODEL=qwen2.5 python tools/build_graph.py

Outputs:
    graph/graph.json    — node/edge data (cached by SHA256)
    graph/graph.html    — interactive vis.js visualization

Edge types:
    EXTRACTED   — explicit [[wikilink]] in a page
    INFERRED    — LLM-detected implicit relationship
    AMBIGUOUS   — low-confidence inferred relationship
"""

import re
import json
import hashlib
import argparse
import webbrowser
import os
import sys
import time
from pathlib import Path
from datetime import date
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for config imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load LLM configuration from .llm_config.json if available
try:
    from core.llm_config import LLMConfig
    llm_config = LLMConfig()
    if llm_config.is_configured():
        cfg = llm_config.get_config()
        LLM_PROVIDER = cfg.get("LLM_PROVIDER", "openai")
        LLM_MODEL = cfg.get("LLM_MODEL")
        LLM_BASE_URL = cfg.get("LLM_BASE_URL")
        OPENAI_API_KEY = cfg.get("OPENAI_API_KEY")
    else:
        # Fallback to environment variables
        LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")
        LLM_MODEL = os.getenv("LLM_MODEL", None)
        LLM_BASE_URL = os.getenv("LLM_BASE_URL", None)
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        llm_config = None
except ImportError:
    # Fallback to environment variables only
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "claude")
    LLM_MODEL = os.getenv("LLM_MODEL", None)
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", None)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    llm_config = None

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

try:
    import openai
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

try:
    import networkx as nx
    from networkx.algorithms import community as nx_community
    HAS_NETWORKX = True
except ImportError:
    HAS_NETWORKX = False
    print("Warning: networkx not installed. Community detection disabled. Run: pip install networkx")

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
GRAPH_DIR = REPO_ROOT / "graph"
GRAPH_JSON = GRAPH_DIR / "graph.json"
GRAPH_HTML = GRAPH_DIR / "graph.html"
CACHE_FILE = GRAPH_DIR / ".cache.json"
LOG_FILE = WIKI_DIR / "log.md"
SCHEMA_FILE = REPO_ROOT / "CLAUDE.md"

# 加载 WikilinkResolver
try:
    from core.wikilink import WikilinkResolver
    HAS_RESOLVER = True
except ImportError:
    HAS_RESOLVER = False

# Node type → color mapping
TYPE_COLORS = {
    "source": "#4CAF50",
    "entity": "#2196F3",
    "concept": "#FF9800",
    "synthesis": "#9C27B0",
    "unknown": "#9E9E9E",
}

# Node type → Chinese name mapping
TYPE_NAMES_CN = {
    "source": "来源文档",
    "entity": "实体",
    "concept": "概念",
    "synthesis": "综合",
    "unknown": "未知",
}

EDGE_COLORS = {
    "EXTRACTED": "#555555",
    "INFERRED": "#FF5722",
    "AMBIGUOUS": "#BDBDBD",
}

# Edge type → Chinese name mapping
EDGE_NAMES_CN = {
    "EXTRACTED": "提取链接",
    "INFERRED": "推断关系",
    "AMBIGUOUS": "模糊关系",
}


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def sha256(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def all_wiki_pages() -> list[Path]:
    return [p for p in WIKI_DIR.rglob("*.md")
            if p.name not in ("index.md", "log.md", "lint-report.md")]


def extract_wikilinks(content: str) -> list[str]:
    return list(set(re.findall(r'\[\[([^\]]+)\]\]', content)))


def extract_frontmatter_type(content: str) -> str:
    match = re.search(r'^type:\s*(\S+)', content, re.MULTILINE)
    return match.group(1).strip('"\'') if match else "unknown"


def page_id(path: Path) -> str:
    return path.relative_to(WIKI_DIR).as_posix().replace(".md", "")


def load_cache() -> dict:
    if CACHE_FILE.exists():
        try:
            return json.loads(CACHE_FILE.read_text())
        except (json.JSONDecodeError, IOError):
            return {}
    return {}


def save_cache(cache: dict):
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps(cache, indent=2))


def build_nodes(pages: list[Path]) -> list[dict]:
    nodes = []
    for p in pages:
        content = read_file(p)
        node_type = extract_frontmatter_type(content)
        title_match = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
        label = title_match.group(1).strip() if title_match else p.stem

        # Add Chinese type name
        type_cn = TYPE_NAMES_CN.get(node_type, TYPE_NAMES_CN["unknown"])

        nodes.append({
            "id": page_id(p),
            "label": label,
            "type": node_type,
            "type_cn": type_cn,  # Chinese type name
            "color": TYPE_COLORS.get(node_type, TYPE_COLORS["unknown"]),
            "path": str(p.relative_to(REPO_ROOT)),
        })
    return nodes


def build_extracted_edges(pages: list[Path]) -> list[dict]:
    """第一遍：确定性 wikilink 边。使用 WikilinkResolver 解析链接。"""
    # 使用 WikilinkResolver 进行规范化解析
    if HAS_RESOLVER:
        resolver = WikilinkResolver(WIKI_DIR)
    else:
        resolver = None

    # 同时保留 stem_map 作为降级
    stem_map = {p.stem.lower(): page_id(p) for p in pages}

    edges = []
    seen = set()
    for p in pages:
        content = read_file(p)
        src = page_id(p)
        for link in extract_wikilinks(content):
            target = None
            if resolver:
                resolved_path = resolver.resolve(link)
                if resolved_path:
                    target = page_id(resolved_path)
            else:
                target = stem_map.get(link.lower())

            if target and target != src:
                key = (src, target)
                if key not in seen:
                    seen.add(key)
                    edges.append({
                        "from": src,
                        "to": target,
                        "type": "EXTRACTED",
                        "type_cn": EDGE_NAMES_CN["EXTRACTED"],
                        "label": EDGE_NAMES_CN["EXTRACTED"],
                        "color": EDGE_COLORS["EXTRACTED"],
                        "confidence": 1.0,
                    })
    return edges


def call_llm(prompt: str, provider: str = None) -> str:
    """Unified LLM interface supporting multiple providers."""
    provider = provider or LLM_PROVIDER

    if provider == "claude":
        if not HAS_ANTHROPIC:
            raise ImportError("anthropic package required for LLM_PROVIDER=claude. Run: pip install anthropic")
        model = LLM_MODEL or "claude-haiku-4-5-20251001"
        client = anthropic.Anthropic()
        response = client.messages.create(
            model=model,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    elif provider == "openai":
        if not HAS_OPENAI:
            raise ImportError("openai package required for LLM_PROVIDER=openai. Run: pip install openai")
        model = LLM_MODEL or "gpt-4o-mini"
        # Use OPENAI_API_KEY from config or environment
        api_key = OPENAI_API_KEY or os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured. Run a wiki command to set up LLM configuration.")
        client = openai.OpenAI(
            base_url=LLM_BASE_URL,
            api_key=api_key
        )
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )
        return response.choices[0].message.content

    elif provider == "ollama":
        if not HAS_REQUESTS:
            raise ImportError("requests package required for LLM_PROVIDER=ollama. Run: pip install requests")
        base_url = LLM_BASE_URL or "http://localhost:11434"
        model = LLM_MODEL or "llama3.2"
        response = requests.post(
            f"{base_url}/api/generate",
            json={"model": model, "prompt": prompt, "stream": False},
            timeout=120
        )
        response.raise_for_status()
        return response.json().get("response", "")

    else:
        raise ValueError(f"Unknown LLM_PROVIDER: {provider}. Choose: claude, openai, ollama")


def build_inferred_edges(pages: list[Path], existing_edges: list[dict], cache: dict) -> list[dict]:
    """Pass 2: LLM-inferred semantic relationships — 并发执行。"""
    # Only process pages that changed since last run
    changed_pages = []
    for p in pages:
        content = read_file(p)
        h = sha256(content)
        if cache.get(str(p)) != h:
            changed_pages.append(p)
            cache[str(p)] = h

    if not changed_pages:
        print("  无变更页面 — 跳过语义推断")
        return []

    provider = LLM_PROVIDER
    model = LLM_MODEL or ("claude-haiku-4-5-20251001" if provider == "claude" else
                          "gpt-4o-mini" if provider == "openai" else "llama3.2")
    print(f"  对 {len(changed_pages)} 个变更页面进行语义推断 ({provider}/{model})...")

    # Build context once (shared across all calls)
    node_list = "\n".join(f"- {page_id(p)} ({extract_frontmatter_type(read_file(p))})" for p in pages)
    existing_edge_summary = "\n".join(
        f"- {e['from']} → {e['to']} (EXTRACTED)" for e in existing_edges[:30]
    )

    def _infer_single_page(p: Path) -> list[dict]:
        """单个页面的推断（在线程中执行）"""
        content = read_file(p)[:2000]
        src = page_id(p)

        prompt = f"""分析这个维基页面，识别与维基中其他页面的隐含语义关系。

源页面：{src}
内容：
{content}

所有可用页面：
{node_list}

已从这个页面提取的边：
{existing_edge_summary}

只返回一个包含新的关系的 JSON 数组（不包括显式 wikilinks 已捕获的关系）：
[
  {{"to": "page-id", "relationship": "一行描述", "confidence": 0.0-1.0, "type": "INFERRED 或 AMBIGUOUS", "relation_type": "关系类别"}}
]

关系类别（relation_type）必须是以下之一：
- "derives_from" — 一个概念/实体派生自另一个
- "contradicts" — 声明互相矛盾
- "supports" — 证据/声明互相支持
- "implements" — 实现某个概念/方法
- "related_to" — 其他相关关系

规则：
- 只包含上面列表中的页面
- 置信度 >= 0.7 → INFERRED，< 0.7 → AMBIGUOUS
- 不要重复已提取列表中的边
- 如果没有找到新关系，返回空数组 []
"""

        try:
            raw = call_llm(prompt, provider).strip()
            raw = re.sub(r"^```(?:json)?\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)

            inferred = json.loads(raw)
            edges = []
            for rel in inferred:
                if isinstance(rel, dict) and "to" in rel:
                    edge_type = rel.get("type", "INFERRED")
                    edge_type_cn = EDGE_NAMES_CN.get(edge_type, EDGE_NAMES_CN["INFERRED"])
                    relationship_cn = rel.get("relationship", edge_type_cn)

                    edges.append({
                        "from": src,
                        "to": rel["to"],
                        "type": edge_type,
                        "type_cn": edge_type_cn,
                        "label": relationship_cn,
                        "relation_type": rel.get("relation_type", "related_to"),
                        "color": EDGE_COLORS.get(edge_type, EDGE_COLORS["INFERRED"]),
                        "confidence": rel.get("confidence", 0.7),
                    })
            return edges
        except (json.JSONDecodeError, TypeError, Exception) as e:
            print(f"    ⚠️ {src}: {e}")
            return []

    # 并发推断（最多 3 个线程，避免 API 限流）
    max_workers = min(3, len(changed_pages))
    new_edges = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(_infer_single_page, p): p for p in changed_pages}
        for future in as_completed(futures):
            p = futures[future]
            completed += 1
            try:
                page_edges = future.result()
                new_edges.extend(page_edges)
                # 只打印找到新边的页面，避免刷屏 +0
                if page_edges:
                    print(f"    ✨ {page_id(p)}: +{len(page_edges)} 条新推断边", flush=True)
                # 每 10 个页面或最后一个显示进度
                if completed % 10 == 0 or completed == len(changed_pages):
                    print(f"    [{completed}/{len(changed_pages)}] 已处理... 累计推断: {len(new_edges)} 条边", flush=True)
            except Exception as e:
                print(f"    ⚠️ {page_id(p)}: {e}", flush=True)

    return new_edges


def detect_communities(nodes: list[dict], edges: list[dict]) -> dict[str, int]:
    """Assign community IDs to nodes using Louvain algorithm."""
    if not HAS_NETWORKX:
        return {}

    G = nx.Graph()
    for n in nodes:
        G.add_node(n["id"])
    for e in edges:
        G.add_edge(e["from"], e["to"])

    if G.number_of_edges() == 0:
        return {}

    try:
        communities = nx_community.louvain_communities(G, seed=42)
        node_to_community = {}
        for i, comm in enumerate(communities):
            for node in comm:
                node_to_community[node] = i
        return node_to_community
    except Exception:
        return {}


COMMUNITY_COLORS = [
    "#E91E63", "#00BCD4", "#8BC34A", "#FF5722", "#673AB7",
    "#FFC107", "#009688", "#F44336", "#3F51B5", "#CDDC39",
]


def render_html(nodes: list[dict], edges: list[dict]) -> str:
    """Generate self-contained vis.js HTML with Chinese labels."""
    nodes_json = json.dumps(nodes, indent=2, ensure_ascii=False)
    edges_json = json.dumps(edges, indent=2, ensure_ascii=False)

    legend_items = "".join(
        f'<span style="background:{color};padding:3px 8px;margin:2px;border-radius:3px;font-size:12px">{TYPE_NAMES_CN.get(t, t)}</span>'
        for t, color in TYPE_COLORS.items() if t != "unknown"
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<title>LLM Wiki — 知识图谱</title>
<script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
<style>
  body {{ margin: 0; background: #1a1a2e; font-family: "Microsoft YaHei", sans-serif; color: #eee; }}
  #graph {{ width: 100vw; height: 100vh; }}
  #controls {{
    position: fixed; top: 10px; left: 10px; background: rgba(0,0,0,0.7);
    padding: 12px; border-radius: 8px; z-index: 10; max-width: 280px;
  }}
  #controls h3 {{ margin: 0 0 8px; font-size: 16px; }}
  #search {{ width: 100%; padding: 4px; margin-bottom: 8px; background: #333; color: #eee; border: 1px solid #555; border-radius: 4px; }}
  #info {{
    position: fixed; bottom: 10px; left: 10px; background: rgba(0,0,0,0.8);
    padding: 12px; border-radius: 8px; z-index: 10; max-width: 350px;
    display: none;
  }}
  #stats {{ position: fixed; top: 10px; right: 10px; background: rgba(0,0,0,0.7); padding: 10px; border-radius: 8px; font-size: 13px; }}
</style>
</head>
<body>
<div id="controls">
  <h3>📊 LLM 维基知识图谱</h3>
  <input id="search" type="text" placeholder="搜索节点..." oninput="searchNodes(this.value)">
  <div style="margin-bottom:8px">{legend_items}</div>
  <div style="margin-top:8px;font-size:11px;color:#aaa">
    <span style="background:#555;padding:2px 6px;border-radius:3px;margin-right:4px">──</span> 提取链接<br>
    <span style="background:#FF5722;padding:2px 6px;border-radius:3px;margin-right:4px">──</span> 推断关系
  </div>
</div>
<div id="graph"></div>
<div id="info">
  <b id="info-title" style="font-size:15px"></b><br>
  <span id="info-type" style="font-size:12px;color:#aaa"></span><br>
  <span id="info-confidence" style="font-size:11px;color:#888"></span><br>
  <span id="info-path" style="font-size:10px;color:#666"></span>
</div>
<div id="stats"></div>
<script>
const nodes = new vis.DataSet({nodes_json});
const edges = new vis.DataSet({edges_json});

// Add labels to edges from data
edges.forEach(edge => {{
  if (edge.label) {{
    edges.update({{ id: edge.id, label: edge.label, font: {{ size: 10, color: "#ccc" }} }});
  }}
}});

const container = document.getElementById("graph");
const network = new vis.Network(container, {{ nodes, edges }}, {{
  nodes: {{
    shape: "dot",
    size: 14,
    font: {{ color: "#eee", size: 14, face: "Microsoft YaHei" }},
    borderWidth: 3,
    borderWidthSelected: 5,
  }},
  edges: {{
    width: 1.5,
    smooth: {{ type: "continuous" }},
    arrows: {{ to: {{ enabled: true, scaleFactor: 0.6 }} }},
    font: {{ size: 10, color: "#ccc", align: "middle" }},
  }},
  physics: {{
    stabilization: {{ iterations: 200 }},
    barnesHut: {{ gravitationalConstant: -8000, springLength: 130 }},
  }},
  interaction: {{ hover: true, tooltipDelay: 200 }},
}});

network.on("click", params => {{
  if (params.nodes.length > 0) {{
    const node = nodes.get(params.nodes[0]);
    document.getElementById("info").style.display = "block";
    document.getElementById("info-title").textContent = node.label || node.id;
    document.getElementById("info-type").textContent = "类型: " + (node.type_cn || node.type || "未知");
    document.getElementById("info-confidence").textContent = "";
    document.getElementById("info-path").textContent = node.path || "";
  }} else if (params.edges.length > 0) {{
    const edge = edges.get(params.edges[0]);
    const fromNode = nodes.get(edge.from);
    const toNode = nodes.get(edge.to);
    document.getElementById("info").style.display = "block";
    document.getElementById("info-title").textContent = (fromNode.label || edge.from) + " → " + (toNode.label || edge.to);
    document.getElementById("info-type").textContent = "关系: " + (edge.type_cn || edge.type || "未知");
    document.getElementById("info-confidence").textContent = edge.label ? ("描述: " + edge.label) : "";
    document.getElementById("info-path").textContent = "置信度: " + (edge.confidence || "N/A");
  }} else {{
    document.getElementById("info").style.display = "none";
  }}
}});

document.getElementById("stats").textContent =
  `节点: ${{nodes.length}} · 边: ${{edges.length}}`;

function searchNodes(q) {{
  const lower = q.toLowerCase();
  nodes.forEach(n => {{
    const label = (n.label || "").toLowerCase();
    const id = n.id.toLowerCase();
    nodes.update({{ id: n.id, opacity: (!q || label.includes(lower) || id.includes(lower)) ? 1 : 0.15 }});
  }});
}}
</script>
</body>
</html>"""


def append_log(entry: str):
    log_path = WIKI_DIR / "log.md"
    existing = read_file(log_path)
    log_path.write_text(entry.strip() + "\n\n" + existing, encoding="utf-8")


def build_graph(infer: bool = True, open_browser: bool = False):
    pages = all_wiki_pages()
    today = date.today().isoformat()
    t0 = time.time()

    if not pages:
        print("⚠️  维基为空。请先摄入一些源文档。")
        return

    # Check LLM configuration if inference is enabled
    if infer:
        from core.llm_config import require_llm_config
        require_llm_config()

    print(f"🔨 正在从 {len(pages)} 个维基页面构建知识图谱...")
    GRAPH_DIR.mkdir(parents=True, exist_ok=True)

    cache = load_cache()

    # Pass 1: extracted edges
    t1 = time.time()
    print("  📎 第一遍：提取 [[wikilinks]]...")
    nodes = build_nodes(pages)
    edges = build_extracted_edges(pages)
    print(f"  ✅ 提取完成: {len(edges)} 条边 ({time.time()-t1:.1f}s)")

    # Pass 2: inferred edges
    if infer:
        t2 = time.time()
        print("  🧠 第二遍：推断语义关系（并发）...")
        inferred = build_inferred_edges(pages, edges, cache)
        edges.extend(inferred)
        print(f"  ✅ 推断完成: {len(inferred)} 条新边 ({time.time()-t2:.1f}s)")
        save_cache(cache)

    # Community detection
    t3 = time.time()
    print("  运行 Louvain 社区检测...")
    communities = detect_communities(nodes, edges)
    for node in nodes:
        comm_id = communities.get(node["id"], -1)
        # Keep type-based color as primary; use community color as border
        if comm_id >= 0:
            comm_color = COMMUNITY_COLORS[comm_id % len(COMMUNITY_COLORS)]
            node["color"] = {
                "background": TYPE_COLORS.get(node["type"], TYPE_COLORS["unknown"]),
                "border": comm_color,
                "highlight": {"background": TYPE_COLORS.get(node["type"], TYPE_COLORS["unknown"]), "border": comm_color},
                "hover": {"background": TYPE_COLORS.get(node["type"], TYPE_COLORS["unknown"]), "border": comm_color},
            }
        node["community"] = comm_id
        node["group"] = node["type"]  # vis.js group by type, not community

    # Save graph.json（包含社区信息）
    # 构建社区摘要
    community_summary = {}
    for node in nodes:
        cid = node.get("community", -1)
        if cid >= 0:
            if cid not in community_summary:
                community_summary[cid] = []
            community_summary[cid].append(node["label"])

    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "communities": community_summary,
        "built": today,
    }
    GRAPH_JSON.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False))
    print(f"  ✅ 已保存: graph/graph.json  ({len(nodes)} 个节点, {len(edges)} 条边, {len(community_summary)} 个社区)")

    # Save graph.html
    html = render_html(nodes, edges)
    GRAPH_HTML.write_text(html, encoding="utf-8")
    print(f"  ✅ 已保存: graph/graph.html")

    # Count edges by type
    extracted_count = len([e for e in edges if e['type']=='EXTRACTED'])
    inferred_count = len([e for e in edges if e['type']=='INFERRED'])
    ambiguous_count = len([e for e in edges if e['type']=='AMBIGUOUS'])

    append_log(f"## [{today}] graph | 知识图谱已重建\n\n{len(nodes)} 个节点, {len(edges)} 条边 ({extracted_count} 条提取, {inferred_count} 条推断, {ambiguous_count} 条模糊).")

    total_time = time.time() - t0
    print(f"\n📊 图谱统计:")
    print(f"   提取边: {extracted_count} 条 (来自 [[wikilinks]])")
    if infer:
        print(f"   推断边: {inferred_count} 条 (LLM 语义推断)")
        if ambiguous_count:
            print(f"   模糊边: {ambiguous_count} 条")
    print(f"   总  计: {len(edges)} 条边, {len(nodes)} 个节点, {len(community_summary)} 个社区")
    print(f"\n✅ 图谱构建完成 (总耗时 {total_time:.1f}s)")

    if open_browser:
        webbrowser.open(f"file://{GRAPH_HTML.resolve()}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build LLM Wiki knowledge graph")
    parser.add_argument("--no-infer", action="store_true", help="Skip semantic inference (faster)")
    parser.add_argument("--open", action="store_true", help="Open graph.html in browser")
    args = parser.parse_args()
    build_graph(infer=not args.no_infer, open_browser=args.open)
