"""
pptx_live.py — CLI bridge between Claude Code and the LivePPT preview browser.

This is the tool that Claude calls in the terminal after editing slides.
It pushes slide JSON to the preview server via HTTP POST.

Usage (from Claude Code terminal):
    # Push all slides
    python ppt_live/pptx_live.py push slides.json

    # Push inline JSON
    python ppt_live/pptx_live.py push --inline '[{"type":"title","title":"Hello"}]'

    # Navigate to slide
    python ppt_live/pptx_live.py goto 3

    # Export to PPTX
    python ppt_live/pptx_live.py export output/my.pptx

    # Create + push (one-shot: generate from template)
    python ppt_live/pptx_live.py create --title "AI安全" --pages 6

    # Edit a specific slide
    python ppt_live/pptx_live.py edit 3 --title "新标题" --items "要点1" "要点2"

    # Batch: set all slides' badge
    python ppt_live/pptx_live.py batch --badge "Company Logo"
"""

import argparse
import json
import os
import sys
import re
import urllib.parse
import urllib.request
import urllib.error
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
_cfg = {"server": "http://localhost:5679"}


def _post(path, data):
    url = f"{_cfg['server']}{urllib.parse.quote(path, safe='/:?=&')}"
    body = json.dumps(data, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"❌ 无法连接到预览服务器 ({url}): {e}", file=sys.stderr)
        print("请先启动: python ppt_live/server.py --open", file=sys.stderr)
        sys.exit(1)


def _get(path):
    url = f"{_cfg['server']}{urllib.parse.quote(path, safe='/:?=&')}"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return json.loads(resp.read())
    except urllib.error.URLError as e:
        print(f"❌ 无法连接到预览服务器: {e}", file=sys.stderr)
        sys.exit(1)


def _verify_state(expected_count=None, expected_current=None):
    """Best-effort verification that server state matches the last operation."""
    state = _get("/api/state")
    slides = state.get("slides", [])
    current = state.get("current", 0)

    if expected_count is not None and len(slides) != expected_count:
        print(f"⚠️ 状态校验失败: 期望页数 {expected_count}，实际 {len(slides)}", file=sys.stderr)
        sys.exit(2)

    if expected_current is not None and current != expected_current:
        print(f"⚠️ 状态校验失败: 期望当前页 {expected_current + 1}，实际 {current + 1}", file=sys.stderr)
        sys.exit(2)


def _replace_first_text_node(html, new_text):
    """Replace the first non-empty text node in an HTML string.

    This is a safe fallback for HTML slides when only --title/--text is provided.
    """
    if not html:
        return html

    # Prefer replacing a large title-like node first.
    title_like = re.search(
        r'(<([a-zA-Z0-9]+)[^>]*style="[^"]*font-size\s*:\s*([2-9][0-9]|[1-9][0-9]{2})px[^"]*"[^>]*>)([^<]+)(</\2>)',
        html,
        flags=re.IGNORECASE,
    )
    if title_like:
        return html[:title_like.start(4)] + new_text + html[title_like.end(4):]

    # Generic fallback: first visible text chunk between tags.
    generic = re.search(r'>([^<\s][^<]*)<', html)
    if generic:
        return html[:generic.start(1)] + new_text + html[generic.end(1):]

    return html


def cmd_push(args):
    """Push slides JSON or HTML directory to preview server."""
    try:
        if args.inline:
            slides = json.loads(args.inline)
        elif args.file and os.path.isdir(args.file):
            # Directory mode: read slide-01.html, slide-02.html, ...
            slides = _load_slides_from_dir(args.file)
        else:
            with open(args.file, "r", encoding="utf-8-sig") as f:
                raw = f.read()
            # Auto-fix common HTML-in-JSON issues
            import re
            # Fix broken tags like \p -> <p (missing < before tag names)
            raw = re.sub(r'(?<!</)\\([a-z]+)\s+style=', r'<\1 style=', raw)
            slides = json.loads(raw)
    except json.JSONDecodeError as e:
        print(f"❌ JSON 解析失败: {e}")
        print(f"   提示: HTML 中可能有未转义的引号或特殊字符")
        print(f"   建议: 改用目录模式 — 每页一个 .html 文件，避免 JSON 转义问题")
        print(f"   用法: python pptx_live.py push output/_tmp_slides/")
        sys.exit(1)

    if isinstance(slides, dict) and "slides" in slides:
        slides = slides["slides"]

    result = _post("/api/push", {"slides": slides})
    print(f"✅ 已推送 {result.get('count', '?')} 页到浏览器")
    _verify_state(expected_count=len(slides))


def _load_slides_from_dir(dir_path):
    """Load slides from a directory of .html files.
    
    Files are sorted by name, so use naming like:
      slide-01.html, slide-02.html, ... slide-15.html
    
    Each file contains raw HTML (the <div> for one slide).
    No JSON escaping needed — this avoids all quote/special-char issues.
    """
    html_dir = Path(dir_path)
    files = sorted(html_dir.glob("*.html"))
    if not files:
        print(f"❌ 目录 {dir_path} 中没有 .html 文件")
        sys.exit(1)
    
    slides = []
    for f in files:
        html = f.read_text(encoding="utf-8").strip()
        slides.append({"html": html})
    
    print(f"📂 从目录加载了 {len(slides)} 个 HTML 幻灯片")
    return slides


def cmd_goto(args):
    """Navigate to a specific slide."""
    result = _post("/api/goto", {"index": args.index - 1})  # 1-indexed for user
    print(f"✅ 已跳转到第 {result.get('current', 0) + 1} 页")
    _verify_state(expected_current=result.get("current", 0))


def cmd_export(args):
    """Export current slides to PPTX."""
    result = _post("/api/export", {"path": args.path})
    if result.get("ok"):
        print(f"✅ 已导出: {result['path']}")
    else:
        print(f"❌ 导出失败: {result.get('error', '未知错误')}")


def cmd_edit(args):
    """Edit a specific slide's properties."""
    state = _get("/api/state")
    slides = state.get("slides", [])
    idx = args.index - 1  # 1-indexed

    if idx < 0 or idx >= len(slides):
        print(f"❌ 第 {args.index} 页不存在（共 {len(slides)} 页）")
        sys.exit(1)

    slide = slides[idx]
    if args.html is not None:
        slide["html"] = args.html
    else:
        if args.title:
            slide["title"] = args.title
        if args.subtitle:
            slide["subtitle"] = args.subtitle
        if args.badge:
            slide["badge"] = args.badge
        if args.slide_type:
            slide["type"] = args.slide_type
        if args.items:
            slide["items"] = args.items
        if args.text:
            slide["text"] = args.text

        # If this is an HTML slide, also patch the HTML text so preview/export stay in sync.
        if isinstance(slide.get("html"), str):
            if args.title:
                slide["html"] = _replace_first_text_node(slide["html"], args.title)
            elif args.text:
                slide["html"] = _replace_first_text_node(slide["html"], args.text)

    result = _post("/api/push", {"slides": slides, "current": idx})
    print(f"✅ 已更新第 {args.index} 页")
    _verify_state(expected_count=len(slides), expected_current=idx)


def cmd_batch(args):
    """Apply changes to all slides."""
    state = _get("/api/state")
    slides = state.get("slides", [])

    for slide in slides:
        if args.badge is not None:
            slide["badge"] = args.badge
        if args.theme_bg:
            slide.setdefault("theme", {})["bg"] = args.theme_bg
        if args.theme_accent:
            slide.setdefault("theme", {})["accent"] = args.theme_accent

    result = _post("/api/push", {"slides": slides})
    print(f"✅ 已批量更新 {result.get('count', '?')} 页")
    _verify_state(expected_count=len(slides))


def cmd_reset(args):
    """Clear all slides — reset to empty state."""
    resp = _post("/api/reset", {})
    print(json.dumps(resp, indent=2, ensure_ascii=False))


def cmd_stop(args):
    """Shut down the preview server."""
    try:
        resp = _post("/api/shutdown", {})
        print(json.dumps(resp, indent=2, ensure_ascii=False))
    except Exception:
        print("Server stopped (or was not running).")


def cmd_state(args):
    """Print current state as JSON."""
    state = _get("/api/state")
    print(json.dumps(state, indent=2, ensure_ascii=False))


def cmd_delete(args):
    """Delete a specific slide."""
    state = _get("/api/state")
    slides = state.get("slides", [])
    idx = args.index - 1

    if idx < 0 or idx >= len(slides):
        print(f"❌ 第 {args.index} 页不存在")
        sys.exit(1)

    slides.pop(idx)
    current = min(state.get("current", 0), len(slides) - 1)
    expected_current = max(current, 0)
    result = _post("/api/push", {"slides": slides, "current": expected_current})
    print(f"✅ 已删除第 {args.index} 页，剩余 {result.get('count', '?')} 页")
    _verify_state(expected_count=len(slides), expected_current=expected_current)


def cmd_insert(args):
    """Insert a new slide at position."""
    state = _get("/api/state")
    slides = state.get("slides", [])
    idx = args.index - 1  # insert before this position

    if args.html is not None:
        new_slide = {"html": args.html}
    else:
        new_slide = {
            "type": args.slide_type or "bullets",
            "title": args.title or "",
        }
        if args.items:
            new_slide["items"] = args.items
        if args.text:
            new_slide["text"] = args.text
        if args.badge:
            new_slide["badge"] = args.badge

    slides.insert(max(0, idx), new_slide)
    expected_current = max(0, idx)
    result = _post("/api/push", {"slides": slides, "current": expected_current})
    print(f"✅ 已在第 {max(1, args.index)} 页插入，共 {result.get('count', '?')} 页")
    _verify_state(expected_count=len(slides), expected_current=expected_current)


def cmd_swap(args):
    """Swap two slides."""
    state = _get("/api/state")
    slides = state.get("slides", [])
    a, b = args.a - 1, args.b - 1

    if a < 0 or a >= len(slides) or b < 0 or b >= len(slides):
        print(f"❌ 页码超出范围（共 {len(slides)} 页）")
        sys.exit(1)

    slides[a], slides[b] = slides[b], slides[a]
    result = _post("/api/push", {"slides": slides})
    print(f"✅ 已交换第 {args.a} 页和第 {args.b} 页")
    _verify_state(expected_count=len(slides))


def cmd_templates(args):
    """List available templates (built-in + user-parsed)."""
    templates_file = SCRIPT_DIR / "templates.json"
    user_templates_file = SCRIPT_DIR / "user_templates.json"

    templates = []
    if templates_file.exists():
        templates.extend(json.loads(templates_file.read_text("utf-8")))
    if user_templates_file.exists():
        templates.extend(json.loads(user_templates_file.read_text("utf-8")))

    if not templates:
        print("❌ 没有可用的模板")
        return

    print(f"📋 共 {len(templates)} 个模板:\n")
    for i, t in enumerate(templates, 1):
        preview = t.get("preview", "📄")
        source = "用户" if t.get("user_uploaded") else "内置"
        print(f"  {i}. {preview} {t['name']} [{source}]")
        print(f"     {t.get('description', '')}")
        print(f"     ID: {t['id']}")
        print()


def cmd_parse_template(args):
    """Parse a user-uploaded PPTX file into a reusable template."""
    pptx_path = Path(args.file)
    if not pptx_path.exists():
        print(f"❌ 文件不存在: {pptx_path}")
        sys.exit(1)

    try:
        project_root = SCRIPT_DIR.parents[1]
        sys.path.insert(0, str(project_root))
        from backend.ppt.template_analyzer import TemplateAnalyzer

        analyzer = TemplateAnalyzer()
        style = analyzer.analyze(str(pptx_path))

        # Build theme from extracted colors
        colors = style.colors if hasattr(style, 'colors') else {}
        fonts = style.fonts if hasattr(style, 'fonts') else {}

        # Map OOXML theme colors to our theme format
        accent1 = colors.get("accent1", "#58a6ff")
        dk1 = colors.get("dk1", "#000000")
        lt1 = colors.get("lt1", "#ffffff")
        dk2 = colors.get("dk2", "#1f1f1f")
        lt2 = colors.get("lt2", "#e7e6e6")

        # Determine if dark or light template
        is_dark = _is_dark_color(dk1) if dk1 != "#000000" else True

        template_id = pptx_path.stem.lower().replace(" ", "-").replace("_", "-")
        new_template = {
            "id": template_id,
            "name": args.name or pptx_path.stem,
            "description": f"从 {pptx_path.name} 解析的用户模板",
            "preview": "📎",
            "user_uploaded": True,
            "source_file": str(pptx_path),
            "theme": {
                "bg": dk1 if is_dark else lt1,
                "title": lt1 if is_dark else dk1,
                "body": lt2 if is_dark else dk2,
                "accent": accent1,
                "muted": lt2 if is_dark else dk2,
                "badge": accent1,
                "badgeBg": accent1 + "22",
                "accentDim": accent1,
            },
            "fonts": {
                "title": fonts.get("latin", fonts.get("ea", "Arial")),
                "body": fonts.get("latin", "Calibri"),
            },
            "ooxml_colors": colors,
            "layouts": style.slide_layouts if hasattr(style, 'slide_layouts') else [],
        }

        # Save to user_templates.json
        user_templates_file = SCRIPT_DIR / "user_templates.json"
        existing = []
        if user_templates_file.exists():
            existing = json.loads(user_templates_file.read_text("utf-8"))

        # Replace if same ID
        existing = [t for t in existing if t["id"] != template_id]
        existing.append(new_template)
        user_templates_file.write_text(json.dumps(existing, indent=2, ensure_ascii=False), encoding="utf-8")

        print(f"✅ 模板已解析并保存: {new_template['name']}")
        print(f"   ID: {template_id}")
        print(f"   配色: bg={new_template['theme']['bg']} accent={accent1}")
        print(f"   字体: {new_template['fonts']}")
        print(f"   布局: {len(new_template.get('layouts', []))} 种")

    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 解析失败: {e}")
        sys.exit(1)


def _is_dark_color(hex_color):
    """Check if a hex color is dark (luminance < 128)."""
    h = hex_color.lstrip("#")
    if len(h) != 6:
        return True
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return (0.299 * r + 0.587 * g + 0.114 * b) < 128


def cmd_get_template(args):
    """Get a specific template's theme JSON by ID."""
    templates_file = SCRIPT_DIR / "templates.json"
    user_templates_file = SCRIPT_DIR / "user_templates.json"

    all_templates = []
    if templates_file.exists():
        all_templates.extend(json.loads(templates_file.read_text("utf-8")))
    if user_templates_file.exists():
        all_templates.extend(json.loads(user_templates_file.read_text("utf-8")))

    for t in all_templates:
        if t["id"] == args.template_id:
            print(json.dumps(t, indent=2, ensure_ascii=False))
            return

    print(f"❌ 未找到模板: {args.template_id}")
    sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="LivePPT CLI — push slides to preview browser")
    parser.add_argument("--server", default=_cfg["server"], help="Preview server URL")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # push
    p_push = sub.add_parser("push", help="Push slides to browser")
    p_push.add_argument("file", nargs="?", help="JSON file path")
    p_push.add_argument("--inline", help="Inline JSON string")

    # goto
    p_goto = sub.add_parser("goto", help="Navigate to slide (1-indexed)")
    p_goto.add_argument("index", type=int)

    # export
    p_export = sub.add_parser("export", help="Export slides to PPTX")
    p_export.add_argument("path", help="Output file path")

    # edit
    p_edit = sub.add_parser("edit", help="Edit a slide's properties")
    p_edit.add_argument("index", type=int, help="Slide number (1-indexed)")
    p_edit.add_argument("--html", help="Replace entire slide HTML")
    p_edit.add_argument("--title", help="New title")
    p_edit.add_argument("--subtitle", help="New subtitle")
    p_edit.add_argument("--badge", help="New badge text")
    p_edit.add_argument("--type", dest="slide_type", help="Slide type")
    p_edit.add_argument("--items", nargs="+", help="Bullet items")
    p_edit.add_argument("--text", help="Body text")

    # batch
    p_batch = sub.add_parser("batch", help="Apply changes to all slides")
    p_batch.add_argument("--badge", help="Set badge on all slides")
    p_batch.add_argument("--theme-bg", help="Background color")
    p_batch.add_argument("--theme-accent", help="Accent color")

    # state
    sub.add_parser("state", help="Print current state")

    # delete
    p_del = sub.add_parser("delete", help="Delete a slide")
    p_del.add_argument("index", type=int, help="Slide number (1-indexed)")

    # insert
    p_ins = sub.add_parser("insert", help="Insert a new slide")
    p_ins.add_argument("index", type=int, help="Insert before this position (1-indexed)")
    p_ins.add_argument("--html", help="Raw HTML for inserted slide")
    p_ins.add_argument("--title", help="Slide title")
    p_ins.add_argument("--type", dest="slide_type", help="Slide type")
    p_ins.add_argument("--items", nargs="+", help="Bullet items")
    p_ins.add_argument("--text", help="Body text")
    p_ins.add_argument("--badge", help="Badge text")

    # swap
    p_swap = sub.add_parser("swap", help="Swap two slides")
    p_swap.add_argument("a", type=int, help="First slide number")
    p_swap.add_argument("b", type=int, help="Second slide number")

    # reset
    sub.add_parser("reset", help="Clear all slides")

    # stop
    sub.add_parser("stop", help="Shut down the preview server")

    # templates (old — lists server-side themes)
    sub.add_parser("templates", help="List all available templates")

    # parse-template (old — server-side template analysis)
    p_parse = sub.add_parser("parse-template", help="Parse a PPTX file into a reusable template")
    p_parse.add_argument("file", help="Path to .pptx file")
    p_parse.add_argument("--name", help="Template display name")

    # get-template (old — get server-side template theme)
    p_get_tpl = sub.add_parser("get-template", help="Get a template's theme by ID")
    p_get_tpl.add_argument("template_id", help="Template ID")

    args = parser.parse_args()
    _cfg["server"] = args.server

    {
        "push": cmd_push,
        "goto": cmd_goto,
        "export": cmd_export,
        "edit": cmd_edit,
        "batch": cmd_batch,
        "state": cmd_state,
        "delete": cmd_delete,
        "insert": cmd_insert,
        "swap": cmd_swap,
        "reset": cmd_reset,
        "stop": cmd_stop,
        "templates": cmd_templates,
        "parse-template": cmd_parse_template,
        "get-template": cmd_get_template,
    }[args.cmd](args)


if __name__ == "__main__":
    main()
