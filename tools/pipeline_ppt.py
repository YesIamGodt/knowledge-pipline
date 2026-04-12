#!/usr/bin/env python3
"""
Generate a Live PPT (interactive HTML presentation) from wiki knowledge.

Usage:
    python tools/pipeline_ppt.py "AI安全分析"
    python tools/pipeline_ppt.py "技术趋势" --pages 8
    python tools/pipeline_ppt.py "竞品分析" --theme apple --open
    python tools/pipeline_ppt.py "项目总结" --sources claude-code-leak,rag-tech

Flags:
    --pages N          Target number of slides (default: auto)
    --theme THEME      Theme preset: dark|light|apple|warm|minimal (default: dark)
    --sources LIST     Comma-separated source slugs to use (default: all)
    --output PATH      Output HTML path (default: graph/liveppt.html)
    --open             Open in browser after generation
"""

import sys
import re
import json
import argparse
import webbrowser
import html as html_mod
from pathlib import Path
from datetime import date

sys.path.insert(0, str(Path(__file__).parent.parent))

# LLM client — initialized lazily
client = None
model = None

REPO_ROOT = Path(__file__).parent.parent
WIKI_DIR = REPO_ROOT / "wiki"
GRAPH_DIR = REPO_ROOT / "graph"
INDEX_FILE = WIKI_DIR / "index.md"


def _init_llm():
    global client, model
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


def read_file(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def collect_wiki_pages(source_filter: list[str] | None = None) -> dict:
    """Collect wiki pages, optionally filtered by source slugs."""
    pages = {"sources": [], "entities": [], "concepts": []}

    for subdir, key in [("sources", "sources"), ("entities", "entities"), ("concepts", "concepts")]:
        d = WIKI_DIR / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if source_filter and key == "sources":
                slug = f.stem
                if slug not in source_filter:
                    continue
            content = read_file(f)
            title = f.stem
            # Extract title from frontmatter
            m = re.search(r'^title:\s*["\']?(.+?)["\']?\s*$', content, re.MULTILINE)
            if m:
                title = m.group(1)
            # Extract summary
            summary = ""
            sm = re.search(r'## Summary\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if sm:
                summary = sm.group(1).strip()[:500]
            # Extract key claims
            claims = []
            cm = re.search(r'## Key Claims\s*\n(.+?)(?=\n##|\Z)', content, re.DOTALL)
            if cm:
                claims = [line.lstrip("- ").strip() for line in cm.group(1).strip().split('\n') if line.strip().startswith('-')][:6]

            pages[key].append({
                "file": str(f.relative_to(REPO_ROOT)),
                "slug": f.stem,
                "title": title,
                "summary": summary,
                "claims": claims,
                "content": content[:2000]
            })

    return pages


def generate_slide_plan(topic: str, pages: dict, num_pages: int | None = None) -> list[dict]:
    """Use LLM to generate a structured slide plan from wiki content."""
    _init_llm()

    # Build context from wiki pages — prioritize sources, limit total size
    context_parts = []
    char_budget = 12000  # Keep context manageable for LLM

    # Sources get full treatment (summary + claims)
    for p in pages["sources"]:
        ctx = f"[source/{p['slug']}] {p['title']}"
        if p.get('summary'):
            ctx += f"\n  Summary: {p['summary'][:300]}"
        if p.get('claims'):
            ctx += "\n  Claims:\n" + "\n".join(f"    - {c}" for c in p['claims'][:4])
        context_parts.append(ctx)

    # Entities/concepts: titles only
    if pages["entities"]:
        context_parts.append("Entities: " + ", ".join(p['title'] for p in pages["entities"]))
    if pages["concepts"]:
        context_parts.append("Concepts: " + ", ".join(p['title'] for p in pages["concepts"]))

    wiki_context = "\n\n".join(context_parts)
    if len(wiki_context) > char_budget:
        wiki_context = wiki_context[:char_budget] + "\n...(truncated)"

    total_sources = len(pages['sources'])
    total_entities = len(pages['entities'])
    total_concepts = len(pages['concepts'])

    page_hint = f"Generate exactly {num_pages} slides." if num_pages else "Generate 6-12 slides as appropriate."

    prompt = f"""You are a presentation designer. Based on the following wiki knowledge base content, create a structured slide deck about: "{topic}"

{page_hint}

Wiki Knowledge Base ({total_sources} sources, {total_entities} entities, {total_concepts} concepts):

{wiki_context}

Return a JSON array of slides. Each slide must have:
- "type": one of "title", "bullets", "comparison", "metric", "quote"
- "badge": short label (e.g. "OVERVIEW", "KEY FINDINGS", topic keywords) — max 20 chars
- "title": slide title (for "quote" type, this is ignored)
- Additional fields based on type:
  - title: "subtitle" (string)
  - bullets: "items" (array of strings, 3-6 items)
  - comparison: "left" (object with "label" and "desc") and "right" (same)
  - metric: "number" (string like "289" or "80%"), "label" (string), "items" (array of strings)
  - quote: "quote" (string), "attribution" (string)
- "source": wiki page path the content comes from (e.g. "wiki/sources/slug.md")

Rules:
- First slide MUST be type "title" with the main topic
- Last slide MUST be type "title" as a closing/thank-you slide
- Mix slide types for visual variety
- Content MUST come from the wiki knowledge — cite specific claims and entities
- Use the SAME LANGUAGE as the topic ("{topic}") for all slide content
- Keep text concise — bullet points, not paragraphs

Return ONLY the JSON array, no markdown fences, no explanation."""

    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=4000,
        timeout=120,
    )

    raw = resp.choices[0].message.content.strip()
    # Strip markdown fences if present
    raw = re.sub(r'^```(?:json)?\s*', '', raw)
    raw = re.sub(r'\s*```$', '', raw)

    try:
        slides = json.loads(raw)
        if not isinstance(slides, list):
            raise ValueError("Expected JSON array")
        return slides
    except (json.JSONDecodeError, ValueError) as e:
        print(f"  ⚠️ LLM output parse error: {e}")
        print(f"  Raw output: {raw[:500]}")
        # Fallback: generate basic slides from wiki content
        return _fallback_slides(topic, pages)


def _fallback_slides(topic: str, pages: dict) -> list[dict]:
    """Generate basic slides without LLM when parsing fails."""
    slides = []
    total = len(pages['sources']) + len(pages['entities']) + len(pages['concepts'])
    slides.append({
        "type": "title", "badge": "KNOWLEDGE PIPELINE",
        "title": topic,
        "subtitle": f"基于 {len(pages['sources'])} 个源文档 · {len(pages['entities'])} 个实体 · {len(pages['concepts'])} 个概念",
        "source": "wiki/index.md"
    })
    for p in pages['sources'][:5]:
        items = p['claims'][:5] if p['claims'] else [p['summary'][:100]] if p['summary'] else [p['title']]
        slides.append({
            "type": "bullets", "badge": p['title'][:18],
            "title": p['title'], "items": items,
            "source": p['file']
        })
    if len(pages['sources']) >= 2:
        slides.append({
            "type": "metric", "badge": "跨源统计",
            "number": str(total), "label": "个知识节点",
            "items": [f"{len(pages['sources'])} 个源文档", f"{len(pages['entities'])} 个实体", f"{len(pages['concepts'])} 个概念"],
            "source": "wiki/index.md"
        })
    slides.append({
        "type": "title", "badge": "THANK YOU",
        "title": "Thanks", "subtitle": f"Generated by Knowledge Pipeline · {date.today()}",
        "source": "wiki/"
    })
    return slides


def escape(s: str) -> str:
    """Escape for safe HTML embedding."""
    return html_mod.escape(str(s)) if s else ""


def generate_html(slides: list[dict], theme: str = "dark", topic: str = "") -> str:
    """Generate self-contained HTML presentation."""

    # Convert slides to JSON for embedding
    slides_json = json.dumps(slides, ensure_ascii=False, indent=2)

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Live PPT — {escape(topic)}</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">
<style>
:root {{
  --bg-deep: #06090f; --bg-card: #0d1117; --bg-slide: #0f1318; --bg-input: #161b22;
  --border: #1b2230; --border-glow: #30363d;
  --text: #e6edf3; --text-dim: #7d8590; --text-muted: #484f58;
  --accent-blue: #58a6ff; --accent-cyan: #56d4dd; --accent-green: #3fb950;
  --accent-orange: #f0883e; --accent-purple: #bc8cff; --accent-red: #f85149; --accent-yellow: #d29922;
  --glow-blue: rgba(88,166,255,0.12); --glow-purple: rgba(188,140,255,0.12);
  --slide-bg: #0f1318; --slide-text: #e6edf3; --slide-dim: #7d8590;
  --slide-accent: #58a6ff; --slide-accent2: #bc8cff;
  --slide-border: #1b2230; --slide-card-bg: rgba(255,255,255,0.03);
  --slide-font: 'Space Grotesk','Noto Sans SC',sans-serif; --slide-radius: 16px;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ background:var(--bg-deep); color:var(--text); font-family:'Space Grotesk','Noto Sans SC',sans-serif; height:100vh; overflow:hidden; }}

.app {{ display:flex; flex-direction:column; height:100vh; }}

/* Toolbar */
.toolbar {{
  display:flex; align-items:center; justify-content:space-between;
  padding:10px 24px; border-bottom:1px solid var(--border); background:var(--bg-card); z-index:10;
}}
.toolbar-title {{ font-size:15px; font-weight:700; display:flex; align-items:center; gap:8px; }}
.toolbar-title .gradient {{ background:linear-gradient(135deg,var(--accent-cyan),var(--accent-blue),var(--accent-purple)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.toolbar-info {{ font-size:12px; color:var(--text-dim); font-family:'JetBrains Mono',monospace; }}
.toolbar-btns {{ display:flex; gap:6px; }}
.tb {{
  background:var(--bg-input); border:1px solid var(--border); color:var(--text-dim);
  padding:5px 14px; border-radius:7px; font-size:12px; font-family:inherit; cursor:pointer; transition:all .2s;
}}
.tb:hover {{ border-color:var(--accent-blue); color:var(--text); }}
.tb.active {{ border-color:var(--accent-blue); color:var(--accent-blue); background:var(--glow-blue); }}

/* Thumbnail strip */
.slide-strip {{
  display:flex; gap:8px; padding:10px 24px; overflow-x:auto;
  border-bottom:1px solid var(--border); background:var(--bg-card); min-height:72px; align-items:center;
}}
.thumb {{
  width:108px; height:60px; border-radius:6px; border:2px solid transparent;
  background:var(--bg-slide); flex-shrink:0; cursor:pointer;
  display:flex; align-items:center; justify-content:center;
  font-size:9px; color:var(--text-muted); text-align:center; padding:4px;
  transition:all .2s; position:relative; overflow:hidden;
}}
.thumb:hover {{ border-color:var(--border-glow); }}
.thumb.active {{ border-color:var(--accent-blue); box-shadow:0 0 0 2px var(--glow-blue); }}
.thumb .thumb-num {{
  position:absolute; top:2px; left:5px; font-size:8px;
  font-family:'JetBrains Mono',monospace; color:var(--text-muted); opacity:.7;
}}

/* Slide canvas */
.slide-canvas {{
  flex:1; display:flex; align-items:center; justify-content:center; padding:24px; position:relative;
}}
.slide-canvas::before {{
  content:''; position:absolute; top:50%; left:50%; transform:translate(-50%,-50%);
  width:500px; height:500px;
  background:radial-gradient(ellipse,var(--glow-purple) 0%,transparent 70%);
  pointer-events:none; opacity:.3;
}}
.slide {{
  width:100%; max-width:1000px; aspect-ratio:16/9;
  background:var(--slide-bg); border:1px solid var(--slide-border);
  border-radius:var(--slide-radius); padding:48px 56px;
  position:relative; overflow:hidden;
  display:flex; flex-direction:column; justify-content:center;
  box-shadow:0 20px 60px rgba(0,0,0,.45);
  font-family:var(--slide-font);
  transition:background .5s,border-color .5s,border-radius .5s;
}}
.slide.entering {{ animation:slide-enter .45s ease forwards; }}
@keyframes slide-enter {{ from{{opacity:0;transform:translateY(24px) scale(.97)}} to{{opacity:1;transform:none}} }}

.slide-badge {{
  position:absolute; top:18px; left:24px;
  font-size:9px; font-weight:600; text-transform:uppercase; letter-spacing:1.5px;
  color:var(--slide-accent); opacity:.55;
}}
.slide-num {{
  position:absolute; bottom:16px; right:24px;
  font-size:12px; font-family:'JetBrains Mono',monospace; color:var(--text-muted);
}}
.slide-source {{
  position:absolute; bottom:16px; left:24px;
  font-size:9px; color:var(--text-muted); max-width:55%;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis;
}}
.slide-source .wiki-tag {{
  background:rgba(63,185,80,.15); color:var(--accent-green);
  padding:1px 5px; border-radius:3px; font-weight:600; margin-right:3px; font-size:8px;
}}
.slide h2 {{ font-size:clamp(24px,3vw,42px); font-weight:700; line-height:1.2; margin-bottom:14px; color:var(--slide-text); }}
.slide h2 .gradient {{ background:linear-gradient(135deg,var(--slide-accent),var(--slide-accent2)); -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text; }}
.slide h3 {{ font-size:18px; font-weight:600; color:var(--slide-accent); margin-bottom:12px; }}
.slide p {{ font-size:15px; line-height:1.7; color:var(--slide-dim); margin-bottom:8px; }}
.slide ul {{ list-style:none; padding:0; }}
.slide ul li {{ position:relative; padding-left:20px; font-size:15px; line-height:1.9; color:var(--slide-dim); }}
.slide ul li::before {{ content:'▸'; position:absolute; left:0; color:var(--slide-accent); font-weight:700; }}
.slide .comparison {{ display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-top:6px; }}
.slide .comp-card {{ background:var(--slide-card-bg); border:1px solid var(--slide-border); border-radius:10px; padding:16px 18px; }}
.slide .comp-card h4 {{ font-size:15px; font-weight:600; margin-bottom:8px; }}
.slide .comp-card.left h4 {{ color:var(--accent-orange); }}
.slide .comp-card.right h4 {{ color:var(--accent-green); }}
.slide .comp-card p {{ font-size:13px; line-height:1.6; }}
.slide .big-number {{
  font-size:64px; font-weight:700; font-family:'JetBrains Mono',monospace;
  background:linear-gradient(135deg,var(--slide-accent),var(--slide-accent2));
  -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
}}
.slide .metric-label {{ font-size:14px; color:var(--slide-dim); margin-bottom:16px; }}
.slide .quote {{
  border-left:3px solid var(--slide-accent2); padding-left:20px;
  font-style:italic; font-size:18px; line-height:1.65; color:var(--slide-text); margin:10px 0;
}}
.slide .quote-attr {{ font-size:12px; color:var(--text-muted); margin-top:8px; font-style:normal; }}

/* Nav dots */
.slide-nav {{ display:flex; justify-content:center; gap:6px; padding:12px; background:var(--bg-card); border-top:1px solid var(--border); }}
.nav-dot {{ width:7px; height:7px; border-radius:50%; background:var(--text-muted); border:none; cursor:pointer; transition:all .2s; padding:0; }}
.nav-dot.active {{ background:var(--accent-blue); transform:scale(1.3); }}
.nav-dot:hover {{ background:var(--accent-blue); }}

/* Fullscreen */
.fullscreen .toolbar {{ display:none; }}
.fullscreen .slide-strip {{ display:none; }}
.fullscreen .slide-nav {{ position:fixed; bottom:0; left:0; right:0; z-index:100; background:rgba(6,9,15,.9); }}
.fullscreen .slide-canvas {{ padding:20px; }}
.fullscreen .slide {{ max-width:1200px; border-radius:0; border:none; }}
.exit-fs {{ position:fixed; top:14px; right:14px; z-index:200; background:rgba(0,0,0,.7); color:var(--text-dim); border:1px solid var(--border); padding:6px 14px; border-radius:7px; font-size:12px; cursor:pointer; font-family:inherit; display:none; }}
.fullscreen .exit-fs {{ display:block; }}

/* Theme selector */
.theme-selector {{ display:flex; gap:4px; }}
.theme-dot {{
  width:16px; height:16px; border-radius:50%; border:2px solid var(--border);
  cursor:pointer; transition:all .2s;
}}
.theme-dot:hover {{ transform:scale(1.2); }}
.theme-dot.active {{ border-color:var(--accent-blue); box-shadow:0 0 0 2px var(--glow-blue); }}

::-webkit-scrollbar {{ width:5px; }}
::-webkit-scrollbar-track {{ background:transparent; }}
::-webkit-scrollbar-thumb {{ background:var(--border); border-radius:3px; }}
</style>
</head>
<body>
<div class="app" id="app">
  <div class="toolbar">
    <div class="toolbar-title">⚡ <span class="gradient">Live PPT</span> <span style="font-weight:400;font-size:12px;color:var(--text-dim);margin-left:8px">{escape(topic)}</span></div>
    <div class="toolbar-info" id="slideCounter">Slide 1 / ?</div>
    <div style="display:flex;align-items:center;gap:12px">
      <div class="theme-selector" id="themeSelector"></div>
      <div class="toolbar-btns">
        <button class="tb" onclick="prevSlide()">← Prev</button>
        <button class="tb" onclick="nextSlide()">Next →</button>
        <button class="tb" onclick="toggleFullscreen()">⛶ 全屏</button>
      </div>
    </div>
  </div>
  <div class="slide-strip" id="slideStrip"></div>
  <div class="slide-canvas" id="slideCanvas">
    <div class="slide entering" id="mainSlide"></div>
  </div>
  <div class="slide-nav" id="slideNav"></div>
  <button class="exit-fs" onclick="toggleFullscreen()">✕ 退出全屏</button>
</div>

<script>
const SLIDES = {slides_json};
let currentSlide = 0;
const initialTheme = "{theme}";

const themes = {{
  dark: {{
    '--slide-bg':'#0f1318','--slide-text':'#e6edf3','--slide-dim':'#7d8590',
    '--slide-accent':'#58a6ff','--slide-accent2':'#bc8cff',
    '--slide-border':'#1b2230','--slide-card-bg':'rgba(255,255,255,0.03)',
    '--slide-font':"'Space Grotesk','Noto Sans SC',sans-serif",'--slide-radius':'16px',
    dot:'#1b2230', label:'深色'
  }},
  light: {{
    '--slide-bg':'#ffffff','--slide-text':'#1d1d1f','--slide-dim':'#6e6e73',
    '--slide-accent':'#0071e3','--slide-accent2':'#bf4800',
    '--slide-border':'#d2d2d7','--slide-card-bg':'rgba(0,0,0,0.03)',
    '--slide-font':"'Space Grotesk','Noto Sans SC',sans-serif",'--slide-radius':'16px',
    dot:'#ffffff', label:'亮色'
  }},
  apple: {{
    '--slide-bg':'#000000','--slide-text':'#f5f5f7','--slide-dim':'#86868b',
    '--slide-accent':'#2997ff','--slide-accent2':'#bf5af2',
    '--slide-border':'#1d1d1f','--slide-card-bg':'rgba(255,255,255,0.05)',
    '--slide-font':"-apple-system,BlinkMacSystemFont,'Noto Sans SC',sans-serif",'--slide-radius':'0px',
    dot:'#000000', label:'Apple'
  }},
  warm: {{
    '--slide-bg':'#1a1410','--slide-text':'#f0e6d3','--slide-dim':'#a89a86',
    '--slide-accent':'#e8a838','--slide-accent2':'#e06040',
    '--slide-border':'#2a2018','--slide-card-bg':'rgba(255,220,160,0.04)',
    '--slide-font':"Georgia,'Noto Sans SC',serif",'--slide-radius':'12px',
    dot:'#1a1410', label:'暖色'
  }},
  minimal: {{
    '--slide-bg':'#fafafa','--slide-text':'#222222','--slide-dim':'#888888',
    '--slide-accent':'#333333','--slide-accent2':'#666666',
    '--slide-border':'#e0e0e0','--slide-card-bg':'rgba(0,0,0,0.02)',
    '--slide-font':"'Space Grotesk','Noto Sans SC',sans-serif",'--slide-radius':'4px',
    dot:'#fafafa', label:'极简'
  }}
}};

// Init theme selector
(function() {{
  const sel = document.getElementById('themeSelector');
  for (const [name, t] of Object.entries(themes)) {{
    const d = document.createElement('div');
    d.className = 'theme-dot' + (name === initialTheme ? ' active' : '');
    d.style.background = t.dot;
    d.title = t.label;
    d.onclick = () => applyTheme(name);
    sel.appendChild(d);
  }}
}})();

function applyTheme(name) {{
  const t = themes[name];
  if (!t) return;
  const root = document.documentElement;
  for (const [k,v] of Object.entries(t)) {{
    if (k.startsWith('--')) root.style.setProperty(k, v);
  }}
  document.querySelectorAll('.theme-dot').forEach((d,i) => {{
    d.classList.toggle('active', Object.keys(themes)[i] === name);
  }});
  showSlide(currentSlide);
}}

// Build thumbnails
(function() {{
  const strip = document.getElementById('slideStrip');
  SLIDES.forEach((s, i) => {{
    const d = document.createElement('div');
    d.className = 'thumb' + (i === 0 ? ' active' : '');
    d.onclick = () => showSlide(i);
    const label = (s.badge || s.type || '').slice(0, 14);
    d.innerHTML = '<span class="thumb-num">' + (i+1) + '</span>' + label;
    strip.appendChild(d);
  }});
}})();

function renderSlide(data, idx) {{
  let h = '<span class="slide-badge">' + esc(data.badge || '') + '</span>';
  switch (data.type) {{
    case 'title':
      h += '<h2><span class="gradient">' + esc(data.title) + '</span></h2>';
      h += '<p>' + esc(data.subtitle || '') + '</p>';
      break;
    case 'bullets':
      h += '<h3>' + esc(data.title) + '</h3><ul>';
      (data.items || []).forEach(item => h += '<li>' + esc(item) + '</li>');
      h += '</ul>';
      break;
    case 'comparison':
      h += '<h3>' + esc(data.title) + '</h3>';
      h += '<div class="comparison">';
      h += '<div class="comp-card left"><h4>' + esc(data.left?.label) + '</h4><p>' + esc(data.left?.desc) + '</p></div>';
      h += '<div class="comp-card right"><h4>' + esc(data.right?.label) + '</h4><p>' + esc(data.right?.desc) + '</p></div>';
      h += '</div>';
      break;
    case 'metric':
      h += '<div class="big-number">' + esc(data.number) + '</div>';
      h += '<div class="metric-label">' + esc(data.label) + '</div>';
      h += '<ul>';
      (data.items || []).forEach(item => h += '<li>' + esc(item) + '</li>');
      h += '</ul>';
      break;
    case 'quote':
      h += '<div class="quote">' + esc(data.quote) + '</div>';
      h += '<div class="quote-attr">' + esc(data.attribution || '') + '</div>';
      break;
  }}
  h += '<span class="slide-source"><span class="wiki-tag">WIKI</span>' + esc(data.source || '') + '</span>';
  h += '<span class="slide-num">' + (idx + 1) + ' / ' + SLIDES.length + '</span>';
  return h;
}}

function esc(s) {{ const d = document.createElement('div'); d.textContent = s || ''; return d.innerHTML; }}

function showSlide(idx) {{
  if (idx < 0 || idx >= SLIDES.length) return;
  currentSlide = idx;
  const el = document.getElementById('mainSlide');
  el.innerHTML = renderSlide(SLIDES[idx], idx);
  el.className = 'slide entering';
  document.getElementById('slideCounter').textContent = 'Slide ' + (idx+1) + ' / ' + SLIDES.length;
  // Update nav
  document.getElementById('slideNav').innerHTML = SLIDES.map((_,i) =>
    '<button class="nav-dot' + (i===idx?' active':'') + '" onclick="showSlide('+i+')"></button>'
  ).join('');
  // Update strip
  document.querySelectorAll('.thumb').forEach((t,i) => t.classList.toggle('active', i===idx));
  // Scroll thumb into view
  const activeThumb = document.querySelector('.thumb.active');
  if (activeThumb) activeThumb.scrollIntoView({{ behavior:'smooth', block:'nearest', inline:'center' }});
}}

function prevSlide() {{ showSlide(currentSlide - 1); }}
function nextSlide() {{ showSlide(currentSlide + 1); }}
function toggleFullscreen() {{ document.getElementById('app').classList.toggle('fullscreen'); }}

// Keyboard nav
document.addEventListener('keydown', e => {{
  if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {{ e.preventDefault(); prevSlide(); }}
  if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {{ e.preventDefault(); nextSlide(); }}
  if (e.key === 'f' || e.key === 'F') toggleFullscreen();
  if (e.key === 'Escape' && document.getElementById('app').classList.contains('fullscreen')) toggleFullscreen();
  if (e.key === 'Home') {{ e.preventDefault(); showSlide(0); }}
  if (e.key === 'End') {{ e.preventDefault(); showSlide(SLIDES.length - 1); }}
}});

// Init
applyTheme(initialTheme);
showSlide(0);
</script>
</body>
</html>'''


def main():
    parser = argparse.ArgumentParser(description="Generate Live PPT from wiki knowledge")
    parser.add_argument("topic", help="Presentation topic / instruction")
    parser.add_argument("--pages", type=int, default=None, help="Target number of slides")
    parser.add_argument("--theme", default="dark", choices=["dark", "light", "apple", "warm", "minimal"],
                        help="Theme preset (default: dark)")
    parser.add_argument("--sources", default=None, help="Comma-separated source slugs to use")
    parser.add_argument("--output", default=None, help="Output HTML path")
    parser.add_argument("--open", action="store_true", help="Open in browser after generation")
    parser.add_argument("--no-llm", action="store_true", help="Skip LLM, use template-based slides")
    args = parser.parse_args()

    output_path = Path(args.output) if args.output else GRAPH_DIR / "liveppt.html"
    source_filter = [s.strip() for s in args.sources.split(",")] if args.sources else None

    print(f"📑 Live PPT Generator")
    print(f"  Topic: {args.topic}")
    print(f"  Theme: {args.theme}")

    # Collect wiki pages
    print(f"\n📚 Reading wiki knowledge base...")
    pages = collect_wiki_pages(source_filter)
    total = sum(len(v) for v in pages.values())
    print(f"  Found: {len(pages['sources'])} sources, {len(pages['entities'])} entities, {len(pages['concepts'])} concepts ({total} total)")

    if total == 0:
        print("  ⚠️ No wiki pages found. Run /pipeline-ingest first.")
        sys.exit(1)

    # Generate slide plan via LLM or fallback
    if args.no_llm:
        print(f"\n📝 Using template-based slide generation (--no-llm)...")
        slides = _fallback_slides(args.topic, pages)
    else:
        print(f"\n🧠 Generating slide plan via LLM...")
        try:
            slides = generate_slide_plan(args.topic, pages, args.pages)
        except Exception as e:
            print(f"  ⚠️ LLM call failed: {e}")
            print(f"  Falling back to template-based generation...")
            slides = _fallback_slides(args.topic, pages)
    print(f"  Generated {len(slides)} slides")

    for i, s in enumerate(slides):
        badge = s.get('badge', s.get('type', ''))
        title = s.get('title', s.get('quote', ''))[:40]
        print(f"  [{i+1}] {s['type']:12s} | {badge:16s} | {title}")

    # Generate HTML
    print(f"\n📄 Generating HTML presentation...")
    html_content = generate_html(slides, theme=args.theme, topic=args.topic)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_content, encoding="utf-8")
    print(f"  ✅ Saved to: {output_path}")

    if args.open:
        webbrowser.open(str(output_path.resolve()))
        print(f"  🌐 Opened in browser")

    print(f"\n✨ Done! Open {output_path} in a browser to view your presentation.")
    print(f"   Keyboard: ←→ navigate · F fullscreen · Home/End first/last")


if __name__ == "__main__":
    main()
