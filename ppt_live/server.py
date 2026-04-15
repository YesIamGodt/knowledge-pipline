"""
LivePPT Preview Server — real-time slide preview driven by Claude Code.

Claude edits slides via python-pptx → pushes JSON via HTTP → browser updates via SSE.
No React, no Fabric.js, no build step. Just Flask + SSE + static HTML.

Usage:
    python ppt_live/server.py [--port 5679] [--open]

API:
    POST /api/push       Push slides JSON → SSE broadcast to all browsers
    POST /api/goto       Navigate to slide { index: N }
    GET  /api/state      Get current presentation state
    GET  /api/stream     SSE endpoint for browser
    POST /api/export     Export to PPTX { path: "output.pptx" }
"""

import json
import os
import sys
import queue
import signal
import threading
import webbrowser
import argparse
from pathlib import Path

from flask import Flask, Response, request, send_from_directory, jsonify

app = Flask(__name__)

# ── Thread-safe state ──
_lock = threading.Lock()
_state = {"slides": [], "current": 0}
_clients = []  # list of queue.Queue, one per SSE listener


@app.after_request
def _cors(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    return response


# ── Pages ──

@app.route("/")
def index():
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), "index.html")


@app.route("/uploads/<path:filename>")
def serve_upload(filename):
    uploads_dir = Path(__file__).resolve().parents[2] / "uploads"
    return send_from_directory(str(uploads_dir), filename)


# ── API ──

@app.route("/api/push", methods=["POST", "OPTIONS"])
def push():
    if request.method == "OPTIONS":
        return "", 204
    data = request.json or {}
    # Accept both [{...}] array and {"slides": [{...}]} object formats
    if isinstance(data, list):
        data = {"slides": data}
    with _lock:
        if "slides" in data:
            _state["slides"] = data["slides"]
        if "current" in data:
            _state["current"] = data["current"]
        # Keep current index valid after structural changes (insert/delete/reset).
        n = len(_state["slides"])
        _state["current"] = max(0, min(int(_state.get("current", 0)), n - 1)) if n else 0
        snapshot = json.dumps(_state, ensure_ascii=False)
        dead = []
        for q in _clients:
            try:
                q.put_nowait(snapshot)
            except queue.Full:
                dead.append(q)
        for q in dead:
            _clients.remove(q)
    return jsonify({"ok": True, "count": len(_state["slides"]), "current": _state["current"]})


@app.route("/api/goto", methods=["POST", "OPTIONS"])
def goto():
    if request.method == "OPTIONS":
        return "", 204
    data = request.json or {}
    idx = data.get("index", 0)
    with _lock:
        n = len(_state["slides"])
        _state["current"] = max(0, min(idx, n - 1)) if n else 0
        snapshot = json.dumps(_state, ensure_ascii=False)
        for q in _clients:
            try:
                q.put_nowait(snapshot)
            except queue.Full:
                pass
    return jsonify({"ok": True, "current": _state["current"]})


@app.route("/api/state")
def get_state():
    with _lock:
        return jsonify(_state)


@app.route("/api/stream")
def stream():
    q = queue.Queue(maxsize=50)
    with _lock:
        _clients.append(q)

    def generate():
        try:
            with _lock:
                yield f"data: {json.dumps(_state, ensure_ascii=False)}\n\n"
            while True:
                try:
                    data = q.get(timeout=30)
                    yield f"data: {data}\n\n"
                except queue.Empty:
                    yield ": keepalive\n\n"
        except GeneratorExit:
            pass
        finally:
            with _lock:
                if q in _clients:
                    _clients.remove(q)

    return Response(
        generate(),
        mimetype="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.route("/api/upload-image", methods=["POST", "OPTIONS"])
def upload_image():
    """Upload an image file and return its URL for use in slides."""
    if request.method == "OPTIONS":
        return "", 204
    if "file" not in request.files:
        return jsonify({"ok": False, "error": "No file uploaded"}), 400
    f = request.files["file"]
    if not f.filename:
        return jsonify({"ok": False, "error": "Empty filename"}), 400
    # Sanitize filename
    import re
    safe_name = re.sub(r'[^\w\-.]', '_', f.filename)
    uploads_dir = Path(__file__).resolve().parents[2] / "uploads" / "images"
    uploads_dir.mkdir(parents=True, exist_ok=True)
    dest = uploads_dir / safe_name
    f.save(str(dest))
    url = f"/uploads/images/{safe_name}"
    return jsonify({"ok": True, "url": url, "path": str(dest)})


def _esc(s):
    """Escape HTML special chars."""
    if not s:
        return ""
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


@app.route("/api/reset", methods=["POST", "OPTIONS"])
def reset():
    """Clear all slides and reset to empty state."""
    if request.method == "OPTIONS":
        return "", 204
    with _lock:
        _state["slides"] = []
        _state["current"] = 0
        snapshot = json.dumps(_state, ensure_ascii=False)
        for q in _clients:
            try:
                q.put_nowait(snapshot)
            except queue.Full:
                pass
    return jsonify({"ok": True, "message": "State cleared"})


@app.route("/api/shutdown", methods=["POST", "OPTIONS"])
def shutdown():
    """Gracefully shut down the server."""
    if request.method == "OPTIONS":
        return "", 204
    func = request.environ.get("werkzeug.server.shutdown")
    if func:
        func()
    else:
        # Fallback: signal the main thread to exit
        os.kill(os.getpid(), signal.SIGTERM)
    return jsonify({"ok": True, "message": "Server shutting down"})


@app.route("/api/export", methods=["POST", "OPTIONS"])
def export_pptx():
    if request.method == "OPTIONS":
        return "", 204
    try:
        project_root = Path(__file__).resolve().parents[2]
        sys.path.insert(0, str(project_root))
        from backend.ppt.exporter import PPTXExporter

        data = request.json or {}
        output = data.get("path", str(project_root / "output" / "presentation.pptx"))
        template_path = data.get("template_path")

        exporter = PPTXExporter()
        with _lock:
            slides = list(_state["slides"])
        path = exporter.export(slides, output, template_path=template_path)
        return jsonify({"ok": True, "path": path})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


# ── Helpers ──

def _kill_existing_server(port):
    """Kill any existing process on the given port before starting."""
    import subprocess
    try:
        if sys.platform == "win32":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True, text=True, timeout=5
            )
            for line in result.stdout.splitlines():
                if f":{port}" in line and "LISTENING" in line:
                    parts = line.split()
                    pid = parts[-1]
                    if pid.isdigit() and int(pid) != os.getpid():
                        subprocess.run(["taskkill", "/F", "/PID", pid],
                                       capture_output=True, timeout=5)
                        print(f"  Killed old server process (PID {pid})")
        else:
            result = subprocess.run(
                ["lsof", "-ti", f":{port}"],
                capture_output=True, text=True, timeout=5
            )
            for pid in result.stdout.strip().split():
                if pid.isdigit() and int(pid) != os.getpid():
                    os.kill(int(pid), signal.SIGTERM)
                    print(f"  Killed old server process (PID {pid})")
    except Exception:
        pass  # Best-effort cleanup


# ── Entry ──

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LivePPT Preview Server")
    parser.add_argument("--port", type=int, default=5679)
    parser.add_argument("--open", action="store_true", help="Open browser on start")
    args = parser.parse_args()

    # Kill any existing server on the same port
    _kill_existing_server(args.port)

    # Handle Ctrl+C gracefully
    def _signal_handler(sig, frame):
        print("\n  Server stopped.")
        sys.exit(0)

    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    url = f"http://localhost:{args.port}"
    print(f"""
╔══════════════════════════════════════════════════════╗
║  🎯 LivePPT Preview Server                          ║
║  {url:<50} ║
║                                                      ║
║  Waiting for slides from Claude Code...              ║
║  POST /api/push to update slides                     ║
║  Press Ctrl+C to stop                                ║
╚══════════════════════════════════════════════════════╝
""")

    if args.open:
        threading.Timer(1.0, lambda: webbrowser.open(url)).start()

    app.run(host="0.0.0.0", port=args.port, threaded=True)
