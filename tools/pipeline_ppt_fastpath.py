#!/usr/bin/env python3
"""Fast-path utilities for /pipeline-ppt workflow.

This script reduces shell trial-and-error by providing deterministic commands:
- bootstrap: detect SKILL_DIR, validate llm config, ensure preview server, list wiki docs with indices
- parse-selection: parse user input like "1,3,8-12" into concrete wiki files
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List

SKILL_NAME = "knowledge-pipline"
WIKI_SUBDIRS = ["sources", "entities", "concepts", "syntheses"]


def _http_json(url: str, timeout: float = 1.5):
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _server_alive(port: int) -> bool:
    try:
        _http_json(f"http://localhost:{port}/api/state", timeout=1.0)
        return True
    except Exception:
        return False


def _home_candidates() -> List[Path]:
    vals = []
    for key in ("USERPROFILE", "HOME"):
        v = os.environ.get(key)
        if v:
            vals.append(Path(v))
    vals.append(Path.home())

    out: List[Path] = []
    seen = set()
    for p in vals:
        s = str(p)
        if s not in seen:
            seen.add(s)
            out.append(p)
    return out


def detect_skill_dir() -> Path:
    env_skill = os.environ.get("SKILL_DIR", "").strip()
    if env_skill:
        p = Path(env_skill)
        if p.exists():
            return p

    candidates: List[Path] = []
    for home in _home_candidates():
        candidates.append(home / ".agents" / "skills" / SKILL_NAME)
        candidates.append(home / ".claude" / "skills" / SKILL_NAME)

    for p in candidates:
        if p.exists():
            return p

    joined = "\n".join(str(p) for p in candidates)
    raise SystemExit(
        "ERROR: knowledge-pipline skill not found. Checked:\n" + joined
    )


def check_llm_config(skill_dir: Path) -> Dict[str, str]:
    cfg = skill_dir / ".llm_config.json"
    if not cfg.exists():
        return {"ok": "false", "reason": "missing", "path": str(cfg)}

    try:
        data = json.loads(cfg.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"ok": "false", "reason": f"invalid-json: {exc}", "path": str(cfg)}

    missing = [k for k in ("base_url", "model", "api_key") if not str(data.get(k, "")).strip()]
    if missing:
        return {"ok": "false", "reason": "missing-fields:" + ",".join(missing), "path": str(cfg)}

    return {"ok": "true", "path": str(cfg)}


def ensure_server(skill_dir: Path, port: int, timeout_sec: float = 18.0) -> Dict[str, str]:
    if _server_alive(port):
        return {"ok": "true", "status": "already-running", "url": f"http://localhost:{port}"}

    server_py = skill_dir / "demo" / "ppt_live" / "server.py"
    if not server_py.exists():
        return {
            "ok": "false",
            "status": "server-script-missing",
            "path": str(server_py),
        }

    subprocess.Popen(
        [sys.executable, str(server_py), "--port", str(port), "--no-browser"],
        cwd=str(skill_dir),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        start_new_session=True,
    )

    end = time.time() + timeout_sec
    while time.time() < end:
        if _server_alive(port):
            return {"ok": "true", "status": "started", "url": f"http://localhost:{port}"}
        time.sleep(0.4)

    return {"ok": "false", "status": "start-timeout", "url": f"http://localhost:{port}"}


def list_wiki(skill_dir: Path) -> List[Dict[str, str]]:
    wiki_root = skill_dir / "wiki"
    items: List[Dict[str, str]] = []
    idx = 1

    for sub in WIKI_SUBDIRS:
        subdir = wiki_root / sub
        if not subdir.exists():
            continue

        for f in sorted(subdir.glob("*.md"), key=lambda x: x.name.lower()):
            items.append(
                {
                    "index": idx,
                    "category": sub,
                    "name": f.name,
                    "rel_path": f"{sub}/{f.name}",
                    "abs_path": str(f),
                }
            )
            idx += 1

    return items


def write_index_map(skill_dir: Path, docs: List[Dict[str, str]]) -> Path:
    out_dir = skill_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "_wiki_index_map.json"
    out.write_text(
        json.dumps(
            {
                "generated_at": int(time.time()),
                "count": len(docs),
                "docs": docs,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    return out


def parse_index_expr(expr: str, max_index: int) -> List[int]:
    s = expr.strip()
    if not s:
        raise ValueError("empty")

    parts = re.split(r"[\s,，]+", s)
    selected = set()

    for p in parts:
        if not p:
            continue
        if "-" in p:
            a_str, b_str = p.split("-", 1)
            if not a_str.isdigit() or not b_str.isdigit():
                raise ValueError(f"bad-range:{p}")
            a, b = int(a_str), int(b_str)
            if a > b:
                raise ValueError(f"reversed-range:{p}")
            if a < 1 or b > max_index:
                raise ValueError(f"out-of-range:{p}")
            for i in range(a, b + 1):
                selected.add(i)
        else:
            if not p.isdigit():
                raise ValueError(f"bad-token:{p}")
            i = int(p)
            if i < 1 or i > max_index:
                raise ValueError(f"out-of-range:{p}")
            selected.add(i)

    if not selected:
        raise ValueError("empty")

    return sorted(selected)


def cmd_bootstrap(args: argparse.Namespace) -> int:
    skill_dir = detect_skill_dir()
    cfg = check_llm_config(skill_dir)

    print(f"SKILL_DIR={skill_dir}")
    print(f"LLM_CONFIG_OK={cfg.get('ok')}")
    if cfg.get("ok") != "true":
        print(f"LLM_CONFIG_REASON={cfg.get('reason')}")
        print(f"LLM_CONFIG_PATH={cfg.get('path')}")
        return 2

    server = ensure_server(skill_dir, args.port)
    print(f"SERVER_OK={server.get('ok')}")
    print(f"SERVER_STATUS={server.get('status')}")
    print(f"SERVER_URL={server.get('url')}")
    if server.get("ok") != "true":
        return 3

    docs = list_wiki(skill_dir)
    print(f"WIKI_DOC_COUNT={len(docs)}")
    if not docs:
        print("WIKI_EMPTY=true")
        return 4

    map_file = write_index_map(skill_dir, docs)
    print(f"WIKI_INDEX_MAP={map_file}")
    print("\n=== WIKI 文档编号列表（用于第①步输入）===")

    current_cat = ""
    for d in docs:
        if d["category"] != current_cat:
            current_cat = d["category"]
            print(f"\n── {current_cat} ──")
        print(f"{d['index']:>3}. {d['rel_path']}")

    print("\n请输入编号（支持逗号和区间），示例: 1,3,8-12")
    return 0


def _load_docs_from_map(skill_dir: Path) -> List[Dict[str, str]]:
    p = skill_dir / "output" / "_wiki_index_map.json"
    if p.exists():
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            docs = data.get("docs", [])
            if isinstance(docs, list) and docs:
                return docs
        except Exception:
            pass
    return list_wiki(skill_dir)


def cmd_parse_selection(args: argparse.Namespace) -> int:
    skill_dir = detect_skill_dir()
    docs = _load_docs_from_map(skill_dir)
    if not docs:
        print("ERROR: wiki 文档为空，请先 ingest")
        return 4

    max_idx = max(int(d["index"]) for d in docs)
    try:
        selected = parse_index_expr(args.selection, max_idx)
    except ValueError as exc:
        print(f"ERROR: 输入编号无效: {exc}")
        return 5

    by_idx = {int(d["index"]): d for d in docs}
    picked = [by_idx[i] for i in selected]

    out_dir = skill_dir / "output"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / "_selected_wiki_docs.json"
    out.write_text(
        json.dumps({"selection": args.selection, "docs": picked}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"SELECTED_COUNT={len(picked)}")
    print(f"SELECTED_FILE={out}")
    for d in picked:
        print(f"{d['index']:>3}. {d['rel_path']}")

    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Fast-path helpers for /pipeline-ppt")
    sub = p.add_subparsers(dest="cmd", required=True)

    b = sub.add_parser("bootstrap", help="Detect/validate/start/list in one command")
    b.add_argument("--port", type=int, default=5679)
    b.set_defaults(func=cmd_bootstrap)

    s = sub.add_parser("parse-selection", help="Parse user index input")
    s.add_argument("selection", help="e.g. 1,3,8-12")
    s.set_defaults(func=cmd_parse_selection)

    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
