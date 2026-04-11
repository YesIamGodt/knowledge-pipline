#!/usr/bin/env python3
"""
Script to parse knowledge graph from wiki pages manually when Python tools are limited.
"""

import os
import re
import json
from datetime import date
from pathlib import Path

# Configuration
WIKI_DIR = r"D:\coding\project\llm-wiki-agent\wiki"
OUTPUT_DIR = r"D:\coding\project\llm-wiki-agent\graph"
LOG_FILE = r"D:\coding\project\llm-wiki-agent\wiki\log.md"

# Node type colors and Chinese names
TYPE_COLORS = {
    "source": "#4CAF50",
    "entity": "#2196F3",
    "concept": "#FF9800",
    "synthesis": "#9C27B0",
    "unknown": "#9E9E9E",
}

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

EDGE_NAMES_CN = {
    "EXTRACTED": "提取链接",
    "INFERRED": "推断关系",
    "AMBIGUOUS": "模糊关系",
}

def read_file(path):
    try:
        return Path(path).read_text("utf-8")
    except:
        return ""

def extract_title(content):
    match = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
    return match.group(1).strip() if match else "Untitled"

def extract_type(content):
    match = re.search(r'^type:\s*(\S+)', content, re.MULTILINE)
    return match.group(1).strip('"\'') if match else "unknown"

def extract_wikilinks(content):
    return list(set(re.findall(r'\[\[([^\]]+)\]\]', content)))

def page_id(path):
    return str(path.relative_to(WIKI_DIR)).replace(".md", "")

def find_page_by_title(pages, title):
    """Find page by title or stem match."""
    title = title.strip()
    for page in pages:
        page_title = extract_title(read_file(page)).strip()
        page_stem = page.stem.strip()

        if page_title.lower() == title.lower() or page_stem.lower() == title.lower():
            return page_id(page)
    return None

def main():
    print("Parsing wiki pages...")

    # Find all wiki pages
    all_pages = list(Path(WIKI_DIR).rglob("*.md"))
    all_pages = [p for p in all_pages if p.name not in ("index.md", "log.md", "lint-report.md")]

    print(f"Found {len(all_pages)} pages")

    # Build nodes
    nodes = []
    for page in all_pages:
        content = read_file(page)
        node_type = extract_type(content)
        title = extract_title(content)

        type_cn = TYPE_NAMES_CN.get(node_type, TYPE_NAMES_CN["unknown"])

        nodes.append({
            "id": page_id(page),
            "label": title,
            "type": node_type,
            "type_cn": type_cn,
            "color": TYPE_COLORS.get(node_type, TYPE_COLORS["unknown"]),
            "path": str(page.relative_to(Path(WIKI_DIR).parent)),
        })

    print(f"Created {len(nodes)} nodes")

    # Build edges
    edges = []
    seen = set()

    for page in all_pages:
        content = read_file(page)
        src_id = page_id(page)

        for link in extract_wikilinks(content):
            target_id = find_page_by_title(all_pages, link)

            if target_id and target_id != src_id:
                edge_key = (src_id, target_id)
                if edge_key not in seen:
                    seen.add(edge_key)
                    edges.append({
                        "from": src_id,
                        "to": target_id,
                        "type": "EXTRACTED",
                        "type_cn": EDGE_NAMES_CN["EXTRACTED"],
                        "label": EDGE_NAMES_CN["EXTRACTED"],
                        "color": EDGE_COLORS["EXTRACTED"],
                        "confidence": 1.0,
                    })

    print(f"Created {len(edges)} edges")

    # Create output directory if needed
    Path(OUTPUT_DIR).mkdir(exist_ok=True)

    # Save graph.json
    graph_data = {
        "nodes": nodes,
        "edges": edges,
        "built": date.today().isoformat()
    }

    graph_json_path = Path(OUTPUT_DIR) / "graph.json"
    graph_json_path.write_text(json.dumps(graph_data, indent=2, ensure_ascii=False), "utf-8")
    print(f"Saved: graph/graph.json")

    # Generate HTML
    html_content = generate_html(graph_data)
    graph_html_path = Path(OUTPUT_DIR) / "graph.html"
    graph_html_path.write_text(html_content, "utf-8")
    print(f"Saved: graph/graph.html")

    # Generate and append log
    append_log(nodes, edges)

    # Print summary
    print_graph_summary(nodes, edges)

def generate_html(graph_data):
    """Generate HTML with vis.js visualization."""
    nodes_json = json.dumps(graph_data["nodes"], indent=2, ensure_ascii=False)
    edges_json = json.dumps(graph_data["edges"], indent=2, ensure_ascii=False)

    TYPE_COLORS_STR = json.dumps(TYPE_COLORS, indent=2, ensure_ascii=False)
    TYPE_NAMES_CN_STR = json.dumps(TYPE_NAMES_CN, indent=2, ensure_ascii=False)
    EDGE_COLORS_STR = json.dumps(EDGE_COLORS, indent=2, ensure_ascii=False)
    EDGE_NAMES_CN_STR = json.dumps(EDGE_NAMES_CN, indent=2, ensure_ascii=False)

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LLM Wiki - 知识图谱</title>
    <style>
        body {{
            margin: 0;
            padding: 0;
            background: #0a0e1a;
            color: #e0e6f0;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            overflow: hidden;
        }}

        #container {{
            width: 100vw;
            height: 100vh;
        }}

        #controls {{
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.9);
            border-radius: 12px;
            padding: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.3);
        }}

        #search {{
            width: 250px;
            padding: 8px 12px;
            border: 1px solid rgba(148, 163, 184, 0.5);
            border-radius: 6px;
            background: rgba(15, 23, 42, 0.8);
            color: #e0e6f0;
            font-size: 14px;
            margin-bottom: 12px;
        }}

        #stats {{
            font-size: 12px;
            color: rgba(148, 163, 184, 0.8);
            margin-top: 12px;
        }}

        .legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            font-size: 12px;
            color: rgba(148, 163, 184, 0.8);
        }}

        .legend-item {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 2px 6px;
            background: rgba(30, 64, 175, 0.2);
            border-radius: 4px;
        }}

        .legend-color {{
            width: 16px;
            height: 16px;
            border-radius: 3px;
        }}

        #info {{
            position: absolute;
            bottom: 20px;
            left: 20px;
            z-index: 1000;
            background: rgba(15, 23, 42, 0.9);
            border-radius: 12px;
            padding: 16px;
            backdrop-filter: blur(10px);
            border: 1px solid rgba(148, 163, 184, 0.3);
            max-width: 300px;
            display: none;
        }}

        #info h3 {{
            margin: 0 0 8px 0;
            font-size: 14px;
            color: #e0e6f0;
        }}

        #info .type {{
            font-size: 12px;
            color: rgba(148, 163, 184, 0.8);
            margin-bottom: 4px;
        }}

        #info .path {{
            font-size: 11px;
            color: rgba(148, 163, 184, 0.6);
            word-break: break-all;
        }}
    </style>
</head>
<body>
    <div id="controls">
        <input type="text" id="search" placeholder="搜索节点...">
        <div class="legend">
            <div class="legend-item">
                <div class="legend-color" style="background: #4CAF50;"></div>来源文档
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #2196F3;"></div>实体
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF9800;"></div>概念
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #9C27B0;"></div>综合
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #555555;"></div>提取链接
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #FF5722;"></div>推断关系
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background: #BDBDBD;"></div>模糊关系
            </div>
        </div>
        <div id="stats"></div>
    </div>

    <div id="info">
        <h3 id="info-title"></h3>
        <div class="type" id="info-type"></div>
        <div class="path" id="info-path"></div>
    </div>

    <div id="container"></div>

    <script type="text/javascript" src="https://unpkg.com/vis-network@9.1.9/dist/vis-network.min.js"></script>

    <script type="text/javascript">
        // Graph data
        const nodes = new vis.DataSet({nodes_json});
        const edges = new vis.DataSet({edges_json});

        // Network container
        const container = document.getElementById('container');

        // Network options
        const options = {{
            nodes: {{
                shape: 'dot',
                size: 14,
                font: {{
                    color: '#e0e6f0',
                    size: 12,
                    face: 'Segoe UI'
                }},
                borderWidth: 2,
                shadow: {{
                    enabled: true,
                    color: 'rgba(0, 0, 0, 0.3)',
                    size: 5
                }}
            }},
            edges: {{
                width: 1.5,
                smooth: {{
                    type: 'continuous',
                    roundness: 0.1
                }},
                font: {{
                    color: '#94a3b8',
                    size: 10,
                    face: 'Segoe UI'
                }},
                arrows: {{
                    to: {{
                        enabled: true,
                        scaleFactor: 0.6
                    }}
                }}
            }},
            physics: {{
                stabilization: {{
                    iterations: 200,
                    fit: true
                }},
                barnesHut: {{
                    gravitationalConstant: -8000,
                    springLength: 130,
                    springConstant: 0.04,
                    damping: 0.09
                }},
                minVelocity: 0.75
            }},
            interaction: {{
                hover: true,
                tooltipDelay: 200,
                zoomView: true,
                dragView: true,
                dragNodes: true
            }}
        }};

        // Create network
        const network = new vis.Network(container, {{ nodes, edges }}, options);

        // Search functionality
        document.getElementById('search').addEventListener('input', function(e) {{
            const searchTerm = e.target.value.toLowerCase();

            nodes.forEach(node => {{
                const label = node.label.toLowerCase();
                const id = node.id.toLowerCase();
                const shouldShow = !searchTerm || label.includes(searchTerm) || id.includes(searchTerm);

                nodes.update({{
                    id: node.id,
                    opacity: shouldShow ? 1 : 0.15
                }});
            }});
        }});

        // Node click event
        network.on('click', function(params) {{
            if (params.nodes.length > 0) {{
                const node = nodes.get(params.nodes[0]);
                document.getElementById('info-title').textContent = node.label;
                document.getElementById('info-type').textContent = node.type_cn;
                document.getElementById('info-path').textContent = node.path;
                document.getElementById('info').style.display = 'block';
            }} else {{
                document.getElementById('info').style.display = 'none';
            }}
        }});

        // Update stats
        document.getElementById('stats').textContent =
            `节点: ${{nodes.length}} · 边: ${{edges.length}} · 来源: ${{nodes.get({nodes_json}).filter(n => n.type === 'source').length}} · 实体: ${{nodes.get({nodes_json}).filter(n => n.type === 'entity').length}} · 概念: ${{nodes.get({nodes_json}).filter(n => n.type === 'concept').length}} · 综合: ${{nodes.get({nodes_json}).filter(n => n.type === 'synthesis').length}}`;
    </script>
</body>
</html>
"""

def print_graph_summary(nodes, edges):
    """Print summary of the graph."""
    type_counts = {}
    for node in nodes:
        node_type = node["type"]
        type_counts[node_type] = type_counts.get(node_type, 0) + 1

    print("\nGraph Summary:")
    print(f"Total nodes: {len(nodes)}")
    print(f"Total edges: {len(edges)}")
    print("\nNodes by type:")
    for node_type, count in type_counts.items():
        type_cn = TYPE_NAMES_CN.get(node_type, node_type)
        print(f"  {type_cn}: {count}")

    # Find most connected nodes (indegree + outdegree)
    connection_counts = {}
    for node in nodes:
        connection_counts[node["id"]] = 0

    for edge in edges:
        connection_counts[edge["from"]] = connection_counts.get(edge["from"], 0) + 1
        connection_counts[edge["to"]] = connection_counts.get(edge["to"], 0) + 1

    sorted_nodes = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
    top_nodes = sorted_nodes[:5]

    print("\nMost connected nodes:")
    for node_id, count in top_nodes:
        node = next(n for n in nodes if n["id"] == node_id)
        print(f"  {node['label']} ({count} connections)")

def append_log(nodes, edges):
    """Append graph build log to log.md."""
    today = date.today().isoformat()
    type_counts = {}
    for node in nodes:
        node_type = node["type"]
        type_counts[node_type] = type_counts.get(node_type, 0) + 1

    # Node type summary
    type_summary = []
    for node_type, count in type_counts.items():
        type_cn = TYPE_NAMES_CN.get(node_type, node_type)
        type_summary.append(f"{type_cn}: {count}")

    log_entry = f"""## [{today}] graph | 知识图谱已重建

{len(nodes)} 个节点, {len(edges)} 条边 ({len([e for e in edges if e['type'] == 'EXTRACTED'])} 条提取, {len([e for e in edges if e['type'] == 'INFERRED'])} 条推断, {len([e for e in edges if e['type'] == 'AMBIGUOUS'])} 条模糊).

### 节点分类

| 类型 | 数量 |
|------|------|
{"\n".join([f"| {TYPE_NAMES_CN.get(t, t)} | {c} |" for t, c in type_counts.items()])}

### 最连接的节点（中心度排名）

| 节点 | 连接数 |
|------|--------|
"""

    # Find most connected nodes (indegree + outdegree)
    connection_counts = {}
    for node in nodes:
        connection_counts[node["id"]] = 0

    for edge in edges:
        connection_counts[edge["from"]] = connection_counts.get(edge["from"], 0) + 1
        connection_counts[edge["to"]] = connection_counts.get(edge["to"], 0) + 1

    sorted_nodes = sorted(connection_counts.items(), key=lambda x: x[1], reverse=True)
    top_nodes = sorted_nodes[:5]

    for node_id, count in top_nodes:
        node = next(n for n in nodes if n["id"] == node_id)
        log_entry += f"| {node['label']} | {count} |\n"

    log_entry += "\n---\n"

    # Append to log file
    log_content = read_file(LOG_FILE)
    with open(LOG_FILE, "w", encoding="utf-8") as f:
        f.write(log_entry + log_content)

if __name__ == "__main__":
    main()
