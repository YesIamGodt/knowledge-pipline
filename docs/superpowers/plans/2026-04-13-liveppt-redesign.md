# LivePPT 系统重构实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建一个具有真实直播体验、人机协作、模板学习能力的 LivePPT 系统

**Architecture:**
- 前端：React + Fabric.js 可视化编辑器，SSE 接收 AI 流式输出
- 后端：Flask API，内存状态管理，支持暂停/恢复
- 核心引擎：智能分批流式引擎，PPTAgent SlideInducter 布局归纳
- LLM 集成：PlannerAgent 大纲规划，GeneratorAgent 流式生成，EditorAgent 自然语言编辑

**Tech Stack:**
- 前端：React 18, Fabric.js 6.0, TypeScript
- 后端：Flask 3.0, python-pptx, OpenCV
- LLM：OpenAI API (通过 core.llm_config)

**实施周期:** 10-13 周（本计划覆盖阶段 1-4，约 7-8 周）

---

## 文件结构

```
backend/ppt/
├── __init__.py
├── pipeline.py              # 主管道（已有，需扩展）
├── agents.py                # LLM agents（已有，需扩展）
├── wiki_context.py          # Wiki 集成（已有）
├── template_analyzer.py     # 模板分析（已有）
├── exporter.py              # PPTX 导出（已有）
├── models.py                # 数据模型（已有，需扩展）
├── inductor.py              # NEW: 布局归纳器
├── streaming_engine.py      # NEW: 智能分批流式引擎
├── state_manager.py         # NEW: 生成状态管理器
├── liveppt_server.py        # NEW: Flask 服务器
└── schemas.py               # NEW: 数据验证模式

demo/liveppt_v2/             # NEW: 前端应用
├── index.html
├── App.jsx
├── main.jsx
├── components/
│   ├── WikiSelector.jsx
│   ├── SlideCanvas.jsx
│   ├── ControlPanel.jsx
│   ├── ChatPanel.jsx
│   └── StatusIndicator.jsx
├── fabric/
│   ├── CanvasManager.js
│   ├── ObjectFactory.js
│   ├── EditHandler.js
│   └── FabricUtils.js
├── api/
│   └── client.js
├── hooks/
│   ├── useSSE.js
│   └── useFabricCanvas.js
├── styles/
│   └── main.css
└── utils/
    ├── constants.js
    └── helpers.js

tests/
├── unit/
│   ├── test_inductor.py
│   ├── test_streaming_engine.py
│   ├── test_state_manager.py
│   └── test_models.py
├── integration/
│   ├── test_full_flow.py
│   └── test_pause_edit_resume.py
└── fixtures/
    ├── sample_template.pptx
    └── sample_wiki_content.md
```

---

## 阶段 1：基础设施（1-2周）

### Task 1.1: 创建项目基础结构和配置文件

**Files:**
- Create: `demo/liveppt_v2/package.json`
- Create: `demo/liveppt_v2/vite.config.js`
- Create: `demo/liveppt_v2/tsconfig.json`
- Create: `demo/liveppt_v2/.gitignore`

- [ ] **Step 1: 创建 package.json**

```json
{
  "name": "liveppt-v2",
  "version": "2.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "fabric": "^6.0.0",
    "eventsource": "^2.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.0.0",
    "vite": "^4.3.0"
  }
}
```

- [ ] **Step 2: 创建 vite.config.js**

```javascript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:5678',
        changeOrigin: true
      }
    }
  }
});
```

- [ ] **Step 3: 创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 4: 创建 .gitignore**

```
node_modules/
dist/
.env
.DS_Store
*.log
```

- [ ] **Step 5: 提交**

```bash
git add demo/liveppt_v2/
git commit -m "feat: add frontend project structure with Vite + React + TypeScript"
```

---

### Task 1.2: 创建后端数据模型和模式

**Files:**
- Modify: `backend/ppt/models.py` (扩展已有文件)
- Create: `backend/ppt/schemas.py`

- [ ] **Step 1: 扩展 models.py，添加新数据模型**

```python
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class SlideLayout:
    """幻灯片布局模式（从模板归纳）"""
    name: str
    description: str
    elements: List['LayoutElement']
    sample_slide_index: int  # 来自模板的第几页

@dataclass
class LayoutElement:
    """布局元素"""
    type: str  # 'title', 'subtitle', 'text', 'image', 'shape'
    x: float  # 相对位置 (0-1)
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    align: str = 'left'  # 'left', 'center', 'right'

@dataclass
class FabricObject:
    """Fabric.js 对象表示"""
    type: str  # 'text', 'image', 'shape', 'group'
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: float = 0
    # 文字特有
    text: Optional[str] = None
    fontSize: Optional[int] = None
    fontFamily: Optional[str] = None
    fill: Optional[str] = None
    # 图片特有
    src: Optional[str] = None
    # 其他属性
    props: Dict[str, Any] = field(default_factory=dict)

@dataclass
class GenerationState:
    """生成任务状态"""
    job_id: str
    status: str  # 'idle', 'generating', 'paused', 'completed', 'error'
    slides: List[Dict[str, Any]]  # Fabric JSON 格式的幻灯片列表
    current_index: int
    wiki_ids: List[str]
    instruction: str
    template_layouts: List[SlideLayout]
    user_edits: Dict[int, Dict[str, Any]]  # slide_index -> fabric_json
    context_stack: List[Dict[str, Any]]  # LLM 上下文
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
```

- [ ] **Step 2: 创建 schemas.py，定义 API 请求/响应模式**

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from models import SlideLayout, FabricObject

class GenerateRequest(BaseModel):
    wiki_ids: List[str]
    instruction: str
    template_path: Optional[str] = None

class GenerateResponse(BaseModel):
    job_id: str
    status: str

class PauseRequest(BaseModel):
    job_id: str

class ResumeRequest(BaseModel):
    job_id: str
    user_edits: Dict[int, Dict[str, Any]] = {}

class ExportRequest(BaseModel):
    slides: List[Dict[str, Any]]
    title: str = "Presentation"

class TemplateAnalyzeRequest(BaseModel):
    file_path: str

class TemplateAnalyzeResponse(BaseModel):
    layouts: List[Dict[str, Any]]
    total_slides: int
```

- [ ] **Step 3: 创建单元测试文件**

```python
# tests/unit/test_models.py
import pytest
from backend.ppt.models import SlideLayout, LayoutElement, FabricObject, GenerationState

def test_slide_layout_creation():
    layout = SlideLayout(
        name='title-center',
        description='标题居中',
        elements=[],
        sample_slide_index=0
    )
    assert layout.name == 'title-center'
    assert len(layout.elements) == 0

def test_layout_element():
    element = LayoutElement(
        type='title',
        x=0.5,
        y=0.3,
        align='center'
    )
    assert element.type == 'title'
    assert element.x == 0.5

def test_fabric_object():
    obj = FabricObject(
        type='text',
        x=100,
        y=200,
        text='Hello',
        fontSize=48
    )
    assert obj.type == 'text'
    assert obj.text == 'Hello'

def test_generation_state():
    state = GenerationState(
        job_id='test-job',
        status='idle',
        slides=[],
        current_index=0,
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    assert state.job_id == 'test-job'
    assert state.status == 'idle'
```

- [ ] **Step 4: 运行测试验证**

```bash
pytest tests/unit/test_models.py -v
```

预期输出：PASS (3 tests)

- [ ] **Step 5: 提交**

```bash
git add backend/ppt/models.py backend/ppt/schemas.py tests/unit/test_models.py
git commit -m "feat: add data models and API schemas for LivePPT v2"
```

---

### Task 1.3: 创建 Flask 服务器基础框架

**Files:**
- Create: `backend/ppt/liveppt_server.py`
- Create: `backend/ppt/__init__.py` (如果不存在)

- [ ] **Step 1: 创建 Flask 服务器**

```python
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
from flask import Flask, Response, stream_with_context, request, jsonify, send_from_directory
from flask_cors import CORS

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.ppt.pipeline import PPTPipeline
from backend.ppt.state_manager import GenerationStateManager
from backend.ppt.streaming_engine import StreamingEngine
from core.llm_config import check_llm_config

app = Flask(__name__)
CORS(app)

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
    from backend.ppt.inductor import SlideInducter
    
    # 如果提供了模板，使用 inductor 提取布局
    if template_path:
        inductor = SlideInducter()
        template_layouts = inductor.analyze(template_path)
    
    state_manager.create_job(job_id, wiki_ids, instruction, template_layouts)
    
    def event_stream():
        """SSE 事件流"""
        try:
            for event in pipeline.generate(
                wiki_ids=wiki_ids,
                instruction=instruction,
                template_style=template_layouts[0] if template_layouts else None,
                should_stop=lambda: state_manager.get_state(job_id).status == 'paused'
            ):
                # 发送 SSE 事件
                yield f"data: {json.dumps(event)}\n\n"
                
                # 如果完成或错误，退出
                if event.get('type') in ['done', 'error', 'stopped']:
                    break
        except GeneratorExit:
            # 客户端断开连接
            pass
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
    
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
        
        exporter = PPTXExporter()
        output_path = tempfile.mktemp(suffix='.pptx')
        exporter.export({'slides': slides, 'title': title}, output_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=f'{title}.pptx'
        )
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
```

- [ ] **Step 2: 创建 __init__.py**

```python
"""
LivePPT Backend Module
"""
__version__ = '2.0.0'
```

- [ ] **Step 3: 创建基础测试**

```python
# tests/integration/test_server.py
import pytest
import json
from backend.ppt.liveppt_server import app, init_pipeline

@pytest.fixture
def client():
    app.config['TESTING'] = True
    init_pipeline()
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/api/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data['status'] == 'ok'

def test_wiki_list(client):
    rv = client.get('/api/wiki/list')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert 'sources' in data or 'entities' in data
```

- [ ] **Step 4: 运行测试**

```bash
pytest tests/integration/test_server.py -v
```

预期输出：PASS (2 tests)

- [ ] **Step 5: 提交**

```bash
git add backend/ppt/liveppt_server.py backend/ppt/__init__.py tests/integration/test_server.py
git commit -m "feat: add Flask server with SSE streaming support"
```

---

### Task 1.4: 创建前端入口和路由

**Files:**
- Create: `demo/liveppt_v2/src/main.jsx`
- Create: `demo/liveppt_v2/src/App.jsx`
- Create: `demo/liveppt_v2/index.html`

- [ ] **Step 1: 创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Live PPT - Knowledge Pipeline</title>
</head>
<body>
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
</html>
```

- [ ] **Step 2: 创建 main.jsx**

```jsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './styles/main.css';

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

- [ ] **Step 3: 创建 App.jsx（基础版本）**

```jsx
import React, { useState, useEffect } from 'react';
import WikiSelector from './components/WikiSelector';
import SlideCanvas from './components/SlideCanvas';
import ControlPanel from './components/ControlPanel';
import ChatPanel from './components/ChatPanel';
import { useSSE } from './hooks/useSSE';
import './App.css';

function App() {
  const [wikiPages, setWikiPages] = useState({});
  const [selectedWikiIds, setSelectedWikiIds] = useState([]);
  const [slides, setSlides] = useState([]);
  const [currentSlideIndex, setCurrentSlideIndex] = useState(0);
  const [isWikiPanelCollapsed, setIsWikiPanelCollapsed] = useState(false);
  const [generationStatus, setGenerationStatus] = useState('idle'); // idle, generating, paused
  const [jobId, setJobId] = useState(null);

  // 加载 Wiki 列表
  useEffect(() => {
    fetch('/api/wiki/list')
      .then(res => res.json())
      .then(data => setWikiPages(data))
      .catch(err => console.error('Failed to load wiki:', err));
  }, []);

  // SSE 连接
  const { events, isConnected, error } = useSSE(
    generationStatus === 'generating' ? `/api/generate` : null,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        wiki_ids: selectedWikiIds,
        instruction: 'Generate PPT',
        template_path: null
      })
    }
  );

  // 处理 SSE 事件
  useEffect(() => {
    if (events.length > 0) {
      const latestEvent = events[events.length - 1];
      console.log('SSE Event:', latestEvent);
      
      switch (latestEvent.type) {
        case 'outline':
          console.log('Outline received:', latestEvent.slides);
          break;
        case 'slide':
          setSlides(prev => [...prev, latestEvent.slide]);
          break;
        case 'done':
          setGenerationStatus('idle');
          break;
        case 'error':
          console.error('Generation error:', latestEvent.message);
          setGenerationStatus('idle');
          break;
      }
    }
  }, [events]);

  const handleGenerate = (instruction) => {
    setSlides([]);
    setCurrentSlideIndex(0);
    setGenerationStatus('generating');
  };

  const handlePause = async () => {
    if (!jobId) return;
    await fetch('/api/pause', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId })
    });
    setGenerationStatus('paused');
  };

  const handleResume = async () => {
    if (!jobId) return;
    await fetch('/api/resume', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_id: jobId, user_edits: {} })
    });
    setGenerationStatus('generating');
  };

  return (
    <div className="app">
      <div className={`panel-left ${isWikiPanelCollapsed ? 'collapsed' : ''}`}>
        <WikiSelector
          wikiPages={wikiPages}
          selectedIds={selectedWikiIds}
          onSelect={setSelectedWikiIds}
          onToggleCollapse={() => setIsWikiPanelCollapsed(!isWikiPanelCollapsed)}
          isCollapsed={isWikiPanelCollapsed}
        />
      </div>
      
      <div className="panel-right">
        <SlideCanvas
          slides={slides}
          currentIndex={currentSlideIndex}
          onSelectIndex={setCurrentSlideIndex}
        />
        
        <ChatPanel
          onSend={handleGenerate}
          disabled={generationStatus === 'generating'}
        />
        
        <ControlPanel
          status={generationStatus}
          onPause={handlePause}
          onResume={handleResume}
          slideCount={slides.length}
          currentIndex={currentSlideIndex}
        />
      </div>
    </div>
  );
}

export default App;
```

- [ ] **Step 4: 创建 App.css**

```css
.app {
  display: flex;
  height: 100vh;
  background: var(--bg-deep, #06090f);
  color: var(--text, #e6edf3);
  font-family: 'Space Grotesk', 'Noto Sans SC', sans-serif;
}

.panel-left {
  width: 280px;
  min-width: 280px;
  border-right: 1px solid var(--border, #1b2230);
  background: var(--bg-card, #0d1117);
  transition: width 0.3s ease;
}

.panel-left.collapsed {
  width: 40px;
  min-width: 40px;
}

.panel-right {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--bg-deep, #06090f);
}
```

- [ ] **Step 5: 提交**

```bash
git add demo/liveppt_v2/
git commit -m "feat: add frontend app structure and routing"
```

---

## 阶段 2：核心引擎（2-3周）

### Task 2.1: 实现智能分批流式引擎

**Files:**
- Create: `backend/ppt/streaming_engine.py`
- Create: `tests/unit/test_streaming_engine.py`

- [ ] **Step 1: 创建 streaming_engine.py**

```python
"""
智能分批流式输出引擎
监控 LLM 输出速度，动态调整发送节奏，提供真实的直播体验
"""
import time
import random
from typing import Generator, Dict, Any, Callable

class StreamingEngine:
    """智能分批流式输出引擎"""
    
    THINKING_THRESHOLD = 2.0  # tokens/秒 - 低于此速度显示思考提示
    FAST_THRESHOLD = 10.0     # tokens/秒 - 高于此速度人为延迟
    
    def __init__(self):
        self.thinking_messages = [
            "🤔 正在分析知识库...",
            "📚 正在整理内容...",
            "💡 正在规划布局...",
            "🎨 正在选择样式...",
            "✨ 正在优化设计..."
        ]
    
    def stream_with_pacing(
        self,
        llm_generator: Generator[str, None, None],
        on_should_stop: Callable[[], bool] = lambda: False
    ) -> Generator[Dict[str, Any], None, None]:
        """
        监控 LLM 输出速度，动态调整发送节奏
        
        Args:
            llm_generator: LLM token 生成器
            on_should_stop: 检查是否应该停止的回调函数
        
        Yields:
            SSE 事件字典:
            - {'type': 'thinking', 'message': str}
            - {'type': 'token', 'text': str}
        """
        token_buffer = []
        last_token_time = time.time()
        last_yield_time = time.time()
        
        for token in llm_generator:
            # 检查是否应该停止
            if on_should_stop():
                yield {'type': 'stopped', 'message': '用户已停止生成'}
                return
            
            now = time.time()
            time_delta = now - last_token_time
            speed = 1.0 / time_delta if time_delta > 0 else 0
            last_token_time = now
            
            token_buffer.append(token)
            
            # 状态 1: 思考中（速度过慢）
            if speed < self.THINKING_THRESHOLD and len(token_buffer) < 5:
                # 如果等待超过 3 秒，发送思考提示
                if now - last_yield_time > 3.0:
                    yield {
                        'type': 'thinking',
                        'message': random.choice(self.thinking_messages)
                    }
                    last_yield_time = now
                    continue
            
            # 状态 2: 输出太快，放慢节奏
            if speed > self.FAST_THRESHOLD:
                # 人为延迟，让用户看清
                time.sleep(0.05)
            
            # 状态 3: 正常输出，批量发送
            # 积累 3-5 个 token 或等待超过 80ms 后发送
            if len(token_buffer) >= 3 or (now - last_yield_time > 0.08):
                yield {
                    'type': 'token',
                    'text': ''.join(token_buffer)
                }
                token_buffer = []
                last_yield_time = now
        
        # 发送剩余内容
        if token_buffer:
            yield {'type': 'token', 'text': ''.join(token_buffer)}
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/test_streaming_engine.py
import pytest
import time
from backend.ppt.streaming_engine import StreamingEngine

class MockLLMGenerator:
    """模拟 LLM 生成器"""
    
    def __init__(self, tokens, delays):
        """
        Args:
            tokens: token 列表
            delays: 每个 token 之前的延迟（秒）
        """
        self.tokens = tokens
        self.delays = delays
    
    def __iter__(self):
        for token, delay in zip(self.tokens, self.delays):
            time.sleep(delay)
            yield token

def test_thinking_detection():
    """测试思考状态检测"""
    engine = StreamingEngine()
    
    # 模拟慢速生成（2 tokens/秒）
    slow_generator = MockLLMGenerator(
        tokens=['Hello', ' ', 'World'],
        delays=[0.5, 0.5, 0.5]
    )
    
    events = list(engine.stream_with_pacing(slow_generator))
    
    # 应该包含 thinking 事件
    thinking_events = [e for e in events if e['type'] == 'thinking']
    assert len(thinking_events) > 0
    
    # 应该包含 token 事件
    token_events = [e for e in events if e['type'] == 'token']
    assert len(token_events) > 0

def test_normal_streaming():
    """测试正常流式输出"""
    engine = StreamingEngine()
    
    # 模拟正常速度（5 tokens/秒）
    normal_generator = MockLLMGenerator(
        tokens=['Fast', ' ', 'output'],
        delays=[0.2, 0.2, 0.2]
    )
    
    events = list(engine.stream_with_pacing(normal_generator))
    
    # 不应该包含 thinking 事件
    thinking_events = [e for e in events if e['type'] == 'thinking']
    assert len(thinking_events) == 0
    
    # 应该包含完整的 token
    all_text = ''.join([e['text'] for e in events if e['type'] == 'token'])
    assert 'Fast output' in all_text

def test_stop_callback():
    """测试停止回调"""
    engine = StreamingEngine()
    
    # 创建一个在第 2 个 token 后返回 True 的回调
    stop_after_two = [False]
    def should_stop():
        if stop_after_two[0]:
            return True
        stop_after_two[0] = True
        return False
    
    generator = MockLLMGenerator(
        tokens=['1', '2', '3', '4'],
        delays=[0.1, 0.1, 0.1, 0.1]
    )
    
    events = list(engine.stream_with_pacing(generator, on_should_stop=should_stop))
    
    # 最后一个事件应该是 stopped
    assert events[-1]['type'] == 'stopped'
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_streaming_engine.py -v
```

预期输出：PASS (3 tests)

- [ ] **Step 4: 提交**

```bash
git add backend/ppt/streaming_engine.py tests/unit/test_streaming_engine.py
git commit -m "feat: implement intelligent streaming engine with pacing"
```

---

### Task 2.2: 实现生成状态管理器

**Files:**
- Create: `backend/ppt/state_manager.py`
- Create: `tests/unit/test_state_manager.py`

- [ ] **Step 1: 创建 state_manager.py**

```python
"""
生成状态管理器
管理所有活跃的生成任务，支持暂停/恢复、编辑记录
"""
import threading
from typing import Dict, List, Optional, Any
from datetime import datetime
from backend.ppt.models import GenerationState, SlideLayout

class GenerationStateManager:
    """管理生成任务状态，支持暂停/恢复"""
    
    def __init__(self):
        self.states: Dict[str, GenerationState] = {}
        self.lock = threading.Lock()
    
    def create_job(
        self,
        job_id: str,
        wiki_ids: List[str],
        instruction: str,
        template_layouts: List[SlideLayout]
    ) -> GenerationState:
        """创建新的生成任务"""
        with self.lock:
            state = GenerationState(
                job_id=job_id,
                status='idle',
                slides=[],
                current_index=0,
                wiki_ids=wiki_ids,
                instruction=instruction,
                template_layouts=template_layouts,
                user_edits={},
                context_stack=[],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            self.states[job_id] = state
            return state
    
    def get_state(self, job_id: str) -> Optional[GenerationState]:
        """获取任务状态"""
        with self.lock:
            return self.states.get(job_id)
    
    def pause(self, job_id: str) -> bool:
        """暂停任务"""
        with self.lock:
            state = self.states.get(job_id)
            if state and state.status == 'generating':
                state.status = 'paused'
                state.updated_at = datetime.now()
                # 保存当前上下文到 stack
                state.context_stack.append({
                    'slides': state.slides.copy(),
                    'current_index': state.current_index
                })
                return True
            return False
    
    def resume(
        self,
        job_id: str,
        user_edits: Dict[int, Dict[str, Any]] = None
    ) -> bool:
        """恢复任务"""
        with self.lock:
            state = self.states.get(job_id)
            if state and state.status == 'paused':
                state.status = 'generating'
                state.updated_at = datetime.now()
                
                # 合并用户编辑
                if user_edits:
                    state.user_edits.update(user_edits)
                
                return True
            return False
    
    def add_slide(self, job_id: str, slide_data: Dict[str, Any]) -> bool:
        """添加幻灯片"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                state.slides.append(slide_data)
                state.current_index = len(state.slides) - 1
                state.updated_at = datetime.now()
                return True
            return False
    
    def add_edit(self, job_id: str, slide_index: int, fabric_json: Dict[str, Any]) -> bool:
        """记录用户编辑"""
        with self.lock:
            state = self.states.get(job_id)
            if state:
                state.user_edits[slide_index] = fabric_json
                state.updated_at = datetime.now()
                return True
            return False
    
    def get_context_for_resume(self, job_id: str) -> Optional[Dict[str, Any]]:
        """生成恢复时的上下文（包含用户编辑）"""
        state = self.get_state(job_id)
        if not state:
            return None
        
        return {
            'original_instruction': state.instruction,
            'slides_so_far': state.slides.copy(),
            'recent_user_edits': self._get_recent_edits(state),
            'next_slide_index': state.current_index,
            'template_layouts': [l.__dict__ for l in state.template_layouts]
        }
    
    def _get_recent_edits(self, state: GenerationState) -> Dict[int, Dict[str, Any]]:
        """获取最近的用户编辑（最近 3 个）"""
        if not state.user_edits:
            return {}
        
        # 按索引排序，返回最近的 3 个
        sorted_edits = sorted(state.user_edits.items(), key=lambda x: x[0], reverse=True)
        return dict(sorted_edits[:3])
    
    def cleanup_old_jobs(self, max_age_hours: int = 24):
        """清理超过指定时间的旧任务"""
        with self.lock:
            now = datetime.now()
            to_delete = []
            
            for job_id, state in self.states.items():
                age = now - state.created_at
                if age.total_seconds() > max_age_hours * 3600:
                    to_delete.append(job_id)
            
            for job_id in to_delete:
                del self.states[job_id]
            
            return len(to_delete)
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/test_state_manager.py
import pytest
import time
from backend.ppt.state_manager import GenerationStateManager
from backend.ppt.models import SlideLayout

def test_create_job():
    """测试创建任务"""
    manager = GenerationStateManager()
    
    state = manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    
    assert state.job_id == 'test-job'
    assert state.status == 'idle'
    assert len(state.slides) == 0

def test_pause_and_resume():
    """测试暂停和恢复"""
    manager = GenerationStateManager()
    
    # 创建任务
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    
    # 暂停
    assert manager.pause('test-job') == False  # 不能暂停 idle 状态
    
    # 先设为 generating
    state = manager.get_state('test-job')
    state.status = 'generating'
    
    # 现在可以暂停
    assert manager.pause('test-job') == True
    assert manager.get_state('test-job').status == 'paused'
    
    # 恢复
    assert manager.resume('test-job') == True
    assert manager.get_state('test-job').status == 'generating'

def test_add_slide():
    """测试添加幻灯片"""
    manager = GenerationStateManager()
    
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    
    slide_data = {'type': 'title', 'text': 'Test Slide'}
    assert manager.add_slide('test-job', slide_data) == True
    
    state = manager.get_state('test-job')
    assert len(state.slides) == 1
    assert state.slides[0] == slide_data
    assert state.current_index == 0

def test_user_edits():
    """测试用户编辑记录"""
    manager = GenerationStateManager()
    
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    
    edit_data = {'type': 'text', 'x': 100, 'y': 200}
    assert manager.add_edit('test-job', 0, edit_data) == True
    
    state = manager.get_state('test-job')
    assert 0 in state.user_edits
    assert state.user_edits[0] == edit_data

def test_cleanup_old_jobs():
    """测试清理旧任务"""
    manager = GenerationStateManager()
    
    # 创建一个任务
    manager.create_job(
        job_id='test-job',
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[]
    )
    
    # 立即清理，应该没有删除
    deleted = manager.cleanup_old_jobs(max_age_hours=0)
    assert deleted == 0
    
    # 手动修改创建时间，模拟旧任务
    state = manager.get_state('test-job')
    state.created_at = datetime.fromtimestamp(0)  # 1970年
    
    deleted = manager.cleanup_old_jobs(max_age_hours=0)
    assert deleted == 1
    assert manager.get_state('test-job') is None
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_state_manager.py -v
```

预期输出：PASS (5 tests)

- [ ] **Step 4: 提交**

```bash
git add backend/ppt/state_manager.py tests/unit/test_state_manager.py
git commit -m "feat: implement generation state manager with pause/resume support"
```

---

### Task 2.3: 实现 PPTAgent SlideInducter 集成

**Files:**
- Create: `backend/ppt/inductor.py`
- Create: `tests/unit/test_inductor.py`

- [ ] **Step 1: 创建 inductor.py**

```python
"""
PPTAgent SlideInducter 集成
从 PPT 模板中提取布局模式
"""
import os
from typing import List
from collections import defaultdict
from pptx import Presentation
from pptx.util import Inches
import cv2
import numpy as np

from backend.ppt.models import SlideLayout, LayoutElement

class SlideInducter:
    """
    从 PPT 模板中提取布局模式
    
    基于 PPTAgent 的 SlideInducter 设计，简化实现：
    1. 读取 PPT 幻灯片
    2. 分析每页的形状位置和类型
    3. 聚类相似的布局
    4. 生成布局 schema
    """
    
    def __init__(self):
        self.layouts: List[SlideLayout] = []
    
    def analyze(self, pptx_path: str) -> List[SlideLayout]:
        """
        分析 PPT 模板，提取布局模式
        
        Args:
            pptx_path: PPT 文件路径
        
        Returns:
            布局模式列表
        """
        if not os.path.exists(pptx_path):
            raise FileNotFoundError(f"Template file not found: {pptx_path}")
        
        try:
            prs = Presentation(pptx_path)
            
            # 提取每页的元素
            slides_data = []
            for slide_idx, slide in enumerate(prs.slides):
                elements = self._extract_slide_elements(slide, slide_idx)
                slides_data.append({
                    'index': slide_idx,
                    'elements': elements
                })
            
            # 聚类相似的布局
            layout_clusters = self._cluster_similar_layouts(slides_data)
            
            # 为每个聚类生成 layout schema
            self.layouts = []
            for cluster_name, cluster_data in layout_clusters.items():
                layout = self._generate_layout_schema(cluster_name, cluster_data)
                self.layouts.append(layout)
            
            return self.layouts
            
        except Exception as e:
            raise RuntimeError(f"Failed to analyze template: {str(e)}")
    
    def _extract_slide_elements(self, slide, slide_idx: int) -> List[LayoutElement]:
        """提取幻灯片中的元素"""
        elements = []
        
        slide_width = slide.parent.slide_width
        slide_height = slide.parent.slide_height
        
        for shape in slide.shapes:
            # 跳过隐藏的形状
            if not shape.visible:
                continue
            
            # 获取位置（归一化到 0-1）
            x = shape.left / slide_width
            y = shape.top / slide_height
            width = shape.width / slide_width
            height = shape.height / slide_height
            
            # 判断类型
            if hasattr(shape, 'text') and shape.text.strip():
                # 文本框
                element_type = self._classify_text_element(shape)
                elements.append(LayoutElement(
                    type=element_type,
                    x=x,
                    y=y,
                    width=width,
                    height=height,
                    align=self._detect_alignment(shape)
                ))
            
            elif shape.shape_type == 13:  # Picture
                elements.append(LayoutElement(
                    type='image',
                    x=x,
                    y=y,
                    width=width,
                    height=height
                ))
        
        return elements
    
    def _classify_text_element(self, shape) -> str:
        """判断文本元素的类型"""
        text = shape.text.strip()
        
        # 根据字体大小判断
        if hasattr(shape, 'text_frame'):
            for paragraph in shape.text_frame.paragraphs:
                for run in paragraph.runs:
                    font_size = run.font.size
                    if font_size:
                        # 转换为磅
                        size_pt = font_size.pt if hasattr(font_size, 'pt') else font_size
                        
                        if size_pt > 32:
                            return 'title'
                        elif size_pt > 20:
                            return 'subtitle'
                        else:
                            return 'text'
        
        # 根据文本长度判断
        if len(text) < 20 and '\n' not in text:
            return 'title'
        elif len(text) < 50:
            return 'subtitle'
        else:
            return 'text'
    
    def _detect_alignment(self, shape) -> str:
        """检测文本对齐方式"""
        if hasattr(shape, 'text_frame'):
            for paragraph in shape.text_frame.paragraphs:
                alignment = paragraph.alignment
                if alignment == 0:  # Left
                    return 'left'
                elif alignment == 1:  # Center
                    return 'center'
                elif alignment == 2:  # Right
                    return 'right'
                elif alignment == 3:  # Justify
                    return 'left'
        return 'left'
    
    def _cluster_similar_layouts(self, slides_data: List[dict]) -> dict:
        """聚类相似的布局"""
        # 简化实现：根据元素数量和位置分组
        clusters = defaultdict(list)
        
        for slide_data in slides_data:
            elements = slide_data['elements']
            
            # 生成布局签名（元素类型 + 位置区间）
            signature = self._generate_layout_signature(elements)
            
            clusters[signature].append(slide_data)
        
        # 为每个聚类生成名称
        layout_clusters = {}
        for signature, cluster_slides in clusters.items():
            layout_name = self._generate_layout_name(signature, cluster_slides[0]['elements'])
            layout_clusters[layout_name] = {
                'slides': cluster_slides,
                'sample_slide': cluster_slides[0]
            }
        
        return layout_clusters
    
    def _generate_layout_signature(self, elements: List[LayoutElement]) -> str:
        """生成布局签名"""
        parts = []
        
        # 按元素类型分组
        type_counts = defaultdict(int)
        for elem in elements:
            type_counts[elem.type] += 1
        
        # 生成签名
        if type_counts['title'] > 0:
            parts.append('title')
        if type_counts['subtitle'] > 0:
            parts.append('subtitle')
        if type_counts['text'] > 0:
            parts.append(f"text{type_counts['text']}")
        if type_counts['image'] > 0:
            parts.append(f"img{type_counts['image']}")
        
        return '-'.join(parts) if parts else 'blank'
    
    def _generate_layout_name(self, signature: str, elements: List[LayoutElement]) -> str:
        """生成布局名称"""
        # 根据签名和元素位置生成描述性名称
        if 'title' in signature and 'subtitle' in signature:
            return 'title-center'
        elif 'text2' in signature:
            return 'two-column-text'
        elif 'img1' in signature and 'text1' in signature:
            return 'image-with-text'
        else:
            return signature.replace('-', '-')
    
    def _generate_layout_schema(self, name: str, cluster_data: dict) -> SlideLayout:
        """生成布局 schema"""
        sample_elements = cluster_data['sample_slide']['elements']
        
        # 生成描述
        description = self._generate_layout_description(name, sample_elements)
        
        return SlideLayout(
            name=name,
            description=description,
            elements=sample_elements,
            sample_slide_index=cluster_data['sample_slide']['index']
        )
    
    def _generate_layout_description(self, name: str, elements: List[LayoutElement]) -> str:
        """生成布局描述"""
        if name == 'title-center':
            return '标题居中，副标题下方'
        elif name == 'two-column-text':
            return '双栏文字布局'
        elif name == 'image-with-text':
            return '图片配文字说明'
        else:
            return f'自定义布局: {name}'
```

- [ ] **Step 2: 创建单元测试**

```python
# tests/unit/test_inductor.py
import pytest
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from backend.ppt.inductor import SlideInducter

@pytest.fixture
def sample_template(tmp_path):
    """创建测试用 PPT 模板"""
    prs = Presentation()
    
    # 幻灯片 1: 标题页
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide1.shapes.title
    title.text = "Title Slide"
    
    # 幻灯片 2: 双栏文本
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    left_box = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(3), Inches(4))
    left_box.text = "Left Column"
    right_box = slide2.shapes.add_textbox(Inches(5), Inches(2), Inches(3), Inches(4))
    right_box.text = "Right Column"
    
    # 保存
    template_path = tmp_path / "test_template.pptx"
    prs.save(str(template_path))
    return str(template_path)

def test_analyze_template(sample_template):
    """测试模板分析"""
    inductor = SlideInducter()
    layouts = inductor.analyze(sample_template)
    
    # 应该提取出至少 1 种布局
    assert len(layouts) >= 1
    
    # 检查布局属性
    for layout in layouts:
        assert layout.name is not None
        assert layout.description is not None
        assert isinstance(layout.elements, list)

def test_nonexistent_file():
    """测试不存在的文件"""
    inductor = SlideInducter()
    
    with pytest.raises(FileNotFoundError):
        inductor.analyze('/nonexistent/file.pptx')
```

- [ ] **Step 3: 运行测试**

```bash
pytest tests/unit/test_inductor.py -v
```

预期输出：PASS (2 tests)

- [ ] **Step 4: 提交**

```bash
git add backend/ppt/inductor.py tests/unit/test_inductor.py
git commit -m "feat: implement PPTAgent SlideInducter for template layout induction"
```

---

## 计划总结

本计划涵盖了 LivePPT 系统重构的前两个阶段：

**阶段 1：基础设施（1-2周）**
- ✅ 前端项目结构（Vite + React + TypeScript）
- ✅ 后端数据模型和 API 模式
- ✅ Flask 服务器基础框架（SSE 流式）
- ✅ 前端入口和路由

**阶段 2：核心引擎（2-3周）**
- ✅ 智能分批流式引擎（解决"假直播"问题）
- ✅ 生成状态管理器（暂停/恢复支持）
- ✅ PPTAgent SlideInducter 集成（模板布局学习）

**下一步：**
- 阶段 3：UI/UX 实现（Fabric 编辑器，Wiki 选择器等）
- 阶段 4：LLM 集成（PlannerAgent，GeneratorAgent，EditorAgent）
- 阶段 5-7：模板系统、导出功能、测试优化

**实施说明：**
1. 使用 TDD 方法：先写测试，再写实现
2. 每个任务完成后立即提交
3. 保持代码简洁，遵循 YAGNI 原则
4. 每周进行一次代码审查和重构

---

**计划版本:** 1.0
**创建日期:** 2026-04-13
**覆盖阶段:** 阶段 1-2（约 3-5 周）
