"""
LivePPT v2 Flask 服务器
提供 SSE 流式生成和 REST API
"""
import os
import sys
import json
import uuid
import threading
import webbrowser
from pathlib import Path
from flask import Flask, Response, stream_with_context, request, jsonify, send_from_directory, send_file
from flask_cors import CORS

import re
import tempfile

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ppt.pipeline import PPTPipeline
from backend.ppt.state_manager import GenerationStateManager
from backend.ppt.streaming_engine import StreamingEngine
from core.llm_config import check_llm_config

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://localhost:5678'], supports_credentials=True)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Directories
UPLOAD_DIR = project_root / 'uploads' / 'templates'
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# 全局状态管理器
state_manager = GenerationStateManager()
pipeline = None

def init_pipeline():
    """初始化 pipeline"""
    global pipeline
    wiki_dir = project_root / 'wiki'
    pipeline = PPTPipeline(wiki_dir)

@app.route('/')
def index():
    """服务前端应用"""
    frontend_dir = project_root / 'demo' / 'liveppt_v2' / 'dist'
    if frontend_dir.exists():
        return send_from_directory(frontend_dir, 'index.html')
    else:
        return jsonify({
            'error': 'Frontend not built. Run: cd demo/liveppt_v2 && npm run build'
        }), 404

@app.route('/assets/<path:path>')
def serve_assets(path):
    """服务前端静态资源"""
    frontend_dir = project_root / 'demo' / 'liveppt_v2' / 'dist'
    return send_from_directory(frontend_dir / 'assets', path)

@app.route('/api/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'llm_configured': check_llm_config() is not None
    })

@app.route('/api/wiki/list')
def wiki_list():
    """获取 Wiki 页面列表"""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500
    return jsonify(pipeline.scan_wiki())

@app.route('/api/generate', methods=['POST'])
def generate():
    """启动 PPT 生成（SSE 流式）"""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500

    data = request.json

    # Input validation
    if not data or not data.get('wiki_ids'):
        return jsonify({'error': 'wiki_ids is required'}), 400
    if not data.get('instruction'):
        return jsonify({'error': 'instruction is required'}), 400

    wiki_ids = data.get('wiki_ids', [])
    instruction = data.get('instruction', '')
    template_path = data.get('template_path')

    # 创建任务 ID
    job_id = str(uuid.uuid4())

    # 分析模板（如果提供）
    template_layouts = []
    if template_path:
        try:
            template_layouts = pipeline.analyze_template(template_path)
        except Exception as e:
            return jsonify({'error': f'Template analysis failed: {str(e)}'}), 400

    # 创建生成状态
    from backend.ppt.models import GenerationState

    state_manager.create_job(job_id, wiki_ids, instruction, template_layouts)

    def event_stream():
        """SSE 事件流"""
        try:
            # Send job_id FIRST so frontend can pause/resume
            yield f"data: {json.dumps({'type': 'job_id', 'job_id': job_id}, ensure_ascii=False)}\n\n"

            for event in pipeline.generate(
                wiki_ids=wiki_ids,
                instruction=instruction,
                template_style=template_layouts[0] if template_layouts else None,
                should_stop=lambda: (state_manager.get_state(job_id) or type('', (), {'status': 'generating'})).status == 'paused'
            ):
                # 发送 SSE 事件
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

                # 如果完成或错误，退出
                if event.get('type') in ['done', 'error', 'stopped']:
                    break
        except GeneratorExit:
            # 客户端断开连接
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/pause', methods=['POST'])
def pause_generation():
    """暂停生成"""
    data = request.json
    job_id = data.get('job_id')
    state_manager.pause(job_id)
    return jsonify({'status': 'paused', 'job_id': job_id})

@app.route('/api/resume', methods=['POST'])
def resume_generation():
    """恢复生成"""
    data = request.json
    job_id = data.get('job_id')
    user_edits = data.get('user_edits', {})
    state_manager.resume(job_id, user_edits)
    return jsonify({'status': 'resumed', 'job_id': job_id})

@app.route('/api/edit', methods=['POST'])
def edit_slide():
    """编辑单页幻灯片（SSE流式输出）"""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500

    data = request.json
    slide_dict = data.get('slide', {})
    instruction = data.get('instruction', '')
    page_index = data.get('page_index', 0)
    context = data.get('context', '')

    if not slide_dict:
        return jsonify({'error': 'Missing slide data'}), 400

    if not instruction:
        return jsonify({'error': 'Missing instruction'}), 400

    def event_stream():
        """SSE 事件流"""
        try:
            for event in pipeline.edit_slide(
                slide_dict=slide_dict,
                instruction=instruction,
                page_index=page_index,
                context=context
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(
        event_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/api/command/interpret', methods=['POST'])
def interpret_command():
    """Interpret textbox input into a structured PPT action using current context."""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500

    data = request.json or {}
    instruction = data.get('instruction', '').strip()
    slides = data.get('slides', [])
    current_slide_index = data.get('current_slide_index', 0)
    can_continue_generation = data.get('can_continue_generation', False)
    generation_status = data.get('generation_status', 'idle')
    last_generation_instruction = data.get('last_generation_instruction', '')

    if not instruction:
        return jsonify({'error': 'instruction is required'}), 400

    try:
        result = pipeline.interpret_command(
            instruction=instruction,
            slides=slides,
            current_slide_index=current_slide_index,
            can_continue_generation=can_continue_generation,
            generation_status=generation_status,
            last_generation_instruction=last_generation_instruction,
        )
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/continue', methods=['POST'])
def continue_generation():
    """Continue an interrupted PPT generation from existing slides."""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500

    data = request.json or {}
    wiki_ids = data.get('wiki_ids', [])
    original_instruction = data.get('original_instruction', '')
    continue_instruction = data.get('instruction', '继续')
    existing_slides = data.get('existing_slides', [])

    if not existing_slides:
        return jsonify({'error': 'Missing existing slides'}), 400
    if not original_instruction:
        return jsonify({'error': 'Missing original instruction'}), 400

    def event_stream():
        try:
            for event in pipeline.continue_generation(
                wiki_ids=wiki_ids,
                original_instruction=original_instruction,
                continue_instruction=continue_instruction,
                existing_slides=existing_slides,
            ):
                yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)}, ensure_ascii=False)}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/export', methods=['POST'])
def export_pptx():
    """导出 PPTX"""
    if pipeline is None:
        return jsonify({'error': 'Pipeline not initialized'}), 500

    data = request.json
    slides = data.get('slides', [])
    title = data.get('title', 'Presentation')

    try:
        from backend.ppt.exporter import PPTXExporter
        import tempfile
        import os

        exporter = PPTXExporter()

        # Create a temp file that auto-deletes
        with tempfile.NamedTemporaryFile(suffix='.pptx', delete=False) as tmp:
            output_path = tmp.name

        exporter.export(slides, output_path, title=title)

        response = send_file(
            output_path,
            as_attachment=True,
            download_name=f'{title}.pptx'
        )

        # Clean up temp file after sending
        @response.call_on_close
        def cleanup():
            try:
                os.unlink(output_path)
            except:
                pass

        return response
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def start_server(port=5678, open_browser=True):
    """启动服务器"""
    init_pipeline()

    if open_browser:
        # 延迟 1 秒打开浏览器，让服务器先启动
        def open_browser_delayed():
            import time
            time.sleep(1)
            webbrowser.open(f'http://localhost:{port}')

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    print(f"\n{'='*60}")
    print(f"🚀 LivePPT Server running at http://localhost:{port}")
    print(f"{'='*60}\n")

    app.run(host='0.0.0.0', port=port, debug=False)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=5678)
    parser.add_argument('--no-browser', action='store_true')
    args = parser.parse_args()

    start_server(port=args.port, open_browser=not args.no_browser)
