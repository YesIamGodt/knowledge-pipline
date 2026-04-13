# LivePPT 系统重构设计文档

**项目**: llm-wiki-agent - LivePPT 模块完整重构
**日期**: 2026-04-13
**设计者**: Claude Code (Sonnet 4.6)
**状态**: 待实施

---

## 文档概述

本文档描述了 LivePPT 系统的完整重构设计，旨在解决当前实现的核心问题并提供真正的人机协作 PPT 生成体验。

### 当前问题

1. **UI 体验差** - Wiki 选择栏过长、布局不合理
2. **模板功能缺失** - 无法真正学习用户上传的 PPT 模板
3. **假直播效果** - LLM 思考时间长无反馈，生成过快一闪而过
4. **缺少人机协作** - 无法在生成过程中干预和编辑

### 设计目标

1. ✅ 真实直播体验 - 智能分批流式，思考时有透明提示
2. ✅ 人机协作 - 暂停-编辑-继续，AI 感知用户修改
3. ✅ 模板学习 - PPTAgent 布局归纳，复用用户模板风格
4. ✅ 高级编辑 - Fabric.js 完整 PPT 编辑器
5. ✅ Wiki 集成 - 语料来自项目知识库
6. ✅ PPTX 导出 - 高质量导出，保持格式

---

## 第 1 部分：整体架构

### 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                      用户交互层                               │
├─────────────────────────────────────────────────────────────┤
│  终端命令: /pipeline-ppt                                    │
│       ↓                                                     │
│  自动启动 Flask 服务器 + 打开浏览器                           │
│       ↓                                                     │
│  ┌──────────────────────────────────────────────────┐       │
│  │  前端单页应用 (React + Fabric.js)                 │       │
│  │  ┌─────────────┬─────────────────┬─────────────┐ │       │
│  │  │ Wiki 选择器  │  Fabric 画布     │  控制面板    │ │       │
│  │  │ (可折叠)     │  (主编辑区)      │  (生成控制)  │ │       │
│  │  └─────────────┴─────────────────┴─────────────┘ │       │
│  └──────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
                          ↓ SSE/WebSocket
┌─────────────────────────────────────────────────────────────┐
│                      后端 API 层                              │
├─────────────────────────────────────────────────────────────┤
│  Flask 路由:                                                 │
│  • GET  /api/wiki/list          - Wiki 扫描                 │
│  • POST /api/generate (SSE)      - 流式生成                  │
│  • POST /api/pause              - 暂停生成                  │
│  • POST /api/resume             - 继续生成                  │
│  • POST /api/template/analyze   - 模板布局归纳              │
│  • POST /api/export             - PPTX 导出                 │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      核心引擎层                               │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ SlideInducter    │  │ StreamingEngine  │                │
│  │ (布局归纳)        │  │ (智能分批流式)    │                │
│  └──────────────────┘  └──────────────────┘                │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │ WikiContext      │  │ PPTXExporter     │                │
│  │ (知识库集成)      │  │ (导出引擎)        │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                      LLM 层                                   │
├─────────────────────────────────────────────────────────────┤
│  • PlannerAgent    - 大纲规划                                │
│  • GeneratorAgent  - 流式生成（带状态感知）                   │
│  • EditorAgent     - 单页编辑                                │
└─────────────────────────────────────────────────────────────┘
```

### 技术栈选择

**前端：** React + Fabric.js
- Fabric.js 提供强大的 Canvas 编辑能力（拖拽、缩放、旋转、图层管理）
- React 管理组件状态和生命周期
- SSE (Server-Sent Events) 接收 AI 流式输出

**后端：** Flask (保持不变)
- 已有代码库，无需重构
- SSE 用于 AI 输出流
- 内存中保存生成任务状态

**核心引擎：** 集成 PPTAgent 的 SlideInducter
- 从上传的模板中提取 5-10 种布局模式
- 根据内容自动选择最合适的布局

---

## 第 2 部分：核心组件设计

### 2.1 前端组件架构

```
App
├── WikiSelector (可折叠侧边栏)
│   ├── WikiCategory
│   └── WikiItem (checkbox)
│
├── SlideCanvas (Fabric.js 主画布)
│   ├── SlideViewport (当前幻灯片显示)
│   ├── FabricCanvas (可编辑区域)
│   │   ├── TextObject (文字)
│   │   ├── ImageObject (图片)
│   │   ├── ShapeObject (形状)
│   │   └── GroupObject (组合元素)
│   └── SlideNavigation (幻灯片切换)
│
├── ControlPanel
│   ├── GenerationControls
│   │   ├── StartButton (开始生成)
│   │   ├── PauseButton (暂停)
│   │   ├── ResumeButton (继续)
│   │   └── StatusIndicator (状态显示)
│   ├── TemplateUploader
│   │   ├── FileInput
│   │   └── TemplatePreview
│   └── ExportButton
│
└── ChatPanel (自然语言交互)
    ├── MessageList
    └── TextInput
```

### 2.2 Fabric.js 编辑器核心功能

**基础对象类型：**
```javascript
// 文字对象
{
  type: 'text',
  text: '标题内容',
  fontSize: 48,
  fontFamily: 'Noto Sans SC',
  fill: '#58a6ff',
  x: 100, y: 100,
  width: 600,
  editable: true
}

// 图片对象
{
  type: 'image',
  src: '/uploads/image.png',
  x: 200, y: 150,
  width: 300, height: 200,
  scalable: true,
  rotatable: true
}

// 容器对象（用于布局）
{
  type: 'container',
  layout: 'two-column', // 或 'title-center', 'full-image'
  children: [obj1, obj2, obj3]
}
```

**编辑操作：**
- ✅ 点击选择 → 显示控制点（缩放、旋转）
- ✅ 拖拽移动 → 实时更新位置
- ✅ 双击文字 → 进入编辑模式
- ✅ 右键菜单 → 复制/粘贴/删除/图层调整
- ✅ 属性面板 → 精确调整（颜色、字体、对齐）

### 2.3 后端核心引擎

#### 2.3.1 SlideInducter（布局归纳器）

```python
class SlideInducter:
    """从 PPT 模板中提取布局模式"""

    def analyze(self, pptx_path: str) -> List[SlideLayout]:
        """
        输入: 用户上传的 .pptx 文件
        输出: 5-10 种布局模式

        流程:
        1. 使用 python-pptx 读取幻灯片
        2. 提取每页的形状位置、类型
        3. 使用视觉模型分析布局结构
        4. 聚类相似的布局
        5. 为每种布局生成 schema
        """

        # 示例输出
        return [
            SlideLayout(
                name='title-center',
                description='标题居中，副标题下方',
                elements=[
                    LayoutElement(type='title', x=0.5, y=0.3, align='center'),
                    LayoutElement(type='subtitle', x=0.5, y=0.5, align='center')
                ]
            ),
            SlideLayout(
                name='two-column-text',
                description='双栏文字布局',
                elements=[
                    LayoutElement(type='text', x=0.25, y=0.3, width=0.4),
                    LayoutElement(type='text', x=0.75, y=0.3, width=0.4)
                ]
            )
        ]
```

#### 2.3.2 StreamingEngine（智能分批流式引擎）

```python
class StreamingEngine:
    """智能分批流式输出引擎"""

    THINKING_THRESHOLD = 2.0  # tokens/秒
    FAST_THRESHOLD = 10.0     # tokens/秒

    def stream_with_pacing(self, llm_generator):
        """
        监控 LLM 输出速度，动态调整发送节奏
        """
        token_buffer = []
        last_token_time = time.time()

        for token in llm_generator:
            now = time.time()
            speed = 1.0 / (now - last_token_time)
            last_token_time = now

            token_buffer.append(token)

            # 状态 1: 思考中
            if speed < self.THINKING_THRESHOLD:
                yield {'type': 'thinking', 'message': self._get_thinking_message()}
                continue

            # 状态 2: 输出太快，放慢
            if speed > self.FAST_THRESHOLD:
                time.sleep(0.05)  # 人为延迟

            # 状态 3: 正常输出，批量发送
            if len(token_buffer) >= 3:
                yield {'type': 'token', 'text': ''.join(token_buffer)}
                token_buffer = []

        # 发送剩余内容
        if token_buffer:
            yield {'type': 'token', 'text': ''.join(token_buffer)}

    def _get_thinking_message(self):
        messages = [
            "🤔 正在分析知识库...",
            "📚 正在整理内容...",
            "💡 正在规划布局...",
            "🎨 正在选择样式..."
        ]
        return random.choice(messages)
```

#### 2.3.3 GenerationStateManager（生成状态管理器）

```python
class GenerationStateManager:
    """管理生成任务状态，支持暂停/恢复"""

    def __init__(self):
        self.states = {}  # job_id -> GenerationState

    def create_job(self, job_id, wiki_ids, instruction, template_layouts):
        self.states[job_id] = GenerationState(
            status='idle',
            slides=[],
            current_index=0,
            wiki_ids=wiki_ids,
            instruction=instruction,
            template_layouts=template_layouts,
            user_edits={},  # slide_index -> fabric_json
            context_stack=[]  # LLM 上下文
        )

    def pause(self, job_id):
        state = self.states[job_id]
        state.status = 'paused'
        # 保存当前 LLM 上下文，以便恢复

    def resume(self, job_id):
        state = self.states[job_id]
        state.status = 'generating'
        # 从上下文恢复，传入用户的编辑

    def add_edit(self, job_id, slide_index, fabric_json):
        """记录用户编辑"""
        state = self.states[job_id]
        state.user_edits[slide_index] = fabric_json

    def get_context_for_resume(self, job_id):
        """生成恢复时的上下文（包含用户编辑）"""
        state = self.states[job_id]
        return {
            'original_instruction': state.instruction,
            'slides_so_far': state.slides[:state.current_index],
            'recent_user_edits': self._get_recent_edits(state),
            'next_slide_index': state.current_index
        }
```

### 2.4 PPTX 导出引擎

```python
class PPTXExporter:
    """Fabric.js JSON → python-pptx"""

    def export(self, fabric_json: dict, output_path: str):
        """
        将前端 Fabric.js 的 JSON 导出为 .pptx

        处理:
        - 文字（字体、大小、颜色）
        - 图片（位置、缩放）
        - 形状（矩形、圆形、线条）
        - 组合对象
        """
        from pptx import Presentation
        from pptx.util import Inches, Pt

        prs = Presentation()

        for slide_data in fabric_json['slides']:
            slide = prs.slides.add_slide()

            for obj in slide_data['objects']:
                if obj['type'] == 'text':
                    self._add_textbox(slide, obj)
                elif obj['type'] == 'image':
                    self._add_image(slide, obj)
                elif obj['type'] == 'shape':
                    self._add_shape(slide, obj)

        prs.save(output_path)
```

---

## 第 3 部分：数据流与交互流程

### 3.1 完整的用户交互流程

```
步骤 1: 启动系统
  用户: /pipeline-ppt
  系统:
    1. 检查 LLM 配置
    2. 启动 Flask 服务器
    3. 自动打开浏览器 (http://localhost:5678)
    4. 加载前端单页应用

步骤 2: 准备知识
  前端:
    1. 调用 GET /api/wiki/list
    2. 显示 Wiki 选择器（可折叠）
  用户:
    3. 勾选相关 Wiki 页面
  (可选)
    4. 上传 PPT 模板
    5. 调用 POST /api/template/analyze
    6. 后端提取布局模式 → 前端显示预览

步骤 3: 开始生成
  用户: 输入指令 "做一个关于 RAG 技术的 PPT"
  前端: POST /api/generate (SSE)

  后端流程:
    1. 创建 GenerationState
    2. WikiContextProvider.gather() → 知识文本
    3. PlannerAgent.plan() → 大纲
    4. 发送 SSE: {"type": "outline", "slides": [...]}

  前端:
    5. 显示导航点（N 个幻灯片）
    6. 准备接收流式内容

步骤 4: 实时流式生成
  后端 GeneratorAgent.generate_streaming():
    for slide_outline in outline:
      for token in llm.stream():
        → StreamingEngine 智能分批
        → 发送 SSE:
           {"type": "thinking", "message": "🤔 正在思考..."}
           {"type": "token", "text": "## RAG 简介"}

  前端实时渲染:
    1. 接收 token → 解析 JSON
    2. 当前 token 拼接到完整内容
    3. Fabric.js 渲染
    4. 用户看到文字"逐字"出现

  当一页完成:
    → 发送 SSE: {"type": "slide", "index": 0, "slide": {...}}
    → 前端: 添加到幻灯片列表，更新进度

步骤 5: 用户暂停并编辑
  用户: 点击"暂停"按钮
  前端:
    1. POST /api/pause {job_id}
    2. AbortController 中断 SSE
    3. Fabric 画布进入编辑模式

  后端:
    1. GenerationStateManager.pause(job_id)
    2. 保存当前 LLM 上下文
    3. 停止生成循环

  用户编辑:
    1. 点击标题 → 拖拽到新位置
    2. 双击文字 → 修改内容
    3. 点击图片按钮 → 上传图片
    4. 调整字体大小、颜色
    5. 前端记录所有修改到 user_edits

步骤 6: 继续生成
  用户: 点击"继续"按钮
  前端: POST /api/resume {job_id, user_edits}

  后端:
    1. GenerationStateManager.resume(job_id)
    2. 获取用户编辑
    3. 构建恢复上下文（包含用户修改）
    4. GeneratorAgent 从上下文恢复
    5. 继续 SSE 流式输出

  AI 感知用户修改:
    - 提示词中包含用户编辑摘要
    - 后续生成参考用户的新布局

步骤 7: 导出 PPTX
  用户: 点击"导出 PPTX"
  前端:
    1. 收集所有幻灯片的 Fabric JSON
    2. POST /api/export {slides: [...], title: "..."}

  后端 PPTXExporter.export():
    1. 遍历所有幻灯片 JSON
    2. 使用 python-pptx 创建 PPT
    3. 转换 Fabric 对象 → PPTX 形状
    4. 保存到临时文件
    5. 返回文件流

  前端:
    6. 触发下载
    7. 完成 ✅
```

### 3.2 SSE 事件协议

```typescript
// 事件类型定义
interface SSEEvent {
  type: 'outline' | 'thinking' | 'token' | 'slide' | 'paused' | 'error';
  data: any;
}

// 1. 大纲事件
{
  type: 'outline',
  total: 8,
  slides: [
    {title: 'RAG 技术简介', layout: 'title-center'},
    {title: '什么是 RAG', layout: 'bullets'},
    {title: 'RAG 架构', layout: 'flowchart'}
  ]
}

// 2. 思考状态
{
  type: 'thinking',
  message: '🤔 正在分析知识库...'
}

// 3. Token 流
{
  type: 'token',
  text: '## RAG 简介\n\nRAG (Retrieval-Augmented Generation) 是...'
}

// 4. 完整幻灯片
{
  type: 'slide',
  index: 0,
  slide: {
    layout: 'title-center',
    objects: [
      {type: 'text', text: 'RAG 技术简介', fontSize: 48, x: 200, y: 150},
      {type: 'text', text: '检索增强生成', fontSize: 24, x: 250, y: 300}
    ]
  }
}

// 5. 暂停确认
{
  type: 'paused',
  message: '已暂停，您可以编辑当前幻灯片'
}

// 6. 错误
{
  type: 'error',
  message: 'LLM 调用超时，请重试'
}
```

### 3.3 暂停-编辑-继续状态机

```
IDLE → GENERATING → PAUSED → EDITING → GENERATING
  ↓                                              ↓
EXPORTED                                    COMPLETED
```

---

## 第 4 部分：UI/UX 设计

### 4.1 界面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Live PPT  -  Knowledge Pipeline                               [_][□][×] │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─────────────┬──────────────────────────────────────────────────────┐ │
│  │             │                                                      │ │
│  │  Wiki       │           ┌─────────────────────────────────────┐   │ │
│  │  选择器      │           │                                     │   │ │
│  │             │           │         Fabric Canvas                │   │ │
│  │  ☐ RAG      │           │                                     │   │ │
│  │  ☐ Transformer         │                                     │   │ │
│  │  ☐ Attention            │                                     │   │ │
│  │             │           │                                     │   │ │
│  │             │           │                                     │   │ │
│  │  ━━━━━━━━━│           │                                     │   │ │
│  │             │           └─────────────────────────────────────┘   │ │
│  │  模板        │                                                      │ │
│  │  📤 上传    │    ◀ 1/8 ▶     ●●●○●○○                            │ │
│  │             │                                                      │ │
│  └─────────────┴──────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ 💬 做一个关于 RAG 技术的 PPT                              [发送] │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                           │
│  [▶ 开始生成]  [⏸ 暂停]  [⏯ 继续]  [📥 导出PPTX]  [⚙️ 设置]            │
│                                                                           │
└─────────────────────────────────────────────────────────────────────────┘
```

### 4.2 Wiki 选择器（可折叠）

**展开状态：**
- 宽度：280px
- 分类显示：Sources、Entities、Concepts
- 每个项目有 checkbox + 标题 + 摘要（一行小字）
- 搜索框：快速过滤
- 全选/取消全选按钮

**折叠状态：**
- 宽度：40px
- 只显示图标
- hover 时显示文字 tooltip

**动画：**
- 平滑过渡 300ms
- 保存用户偏好到 localStorage

### 4.3 Fabric 画布区

**主编辑区：**
- 16:9 比例（1280x720）
- 居中显示，带阴影效果
- 背景网格（辅助对齐）

**编辑模式：**
- 对象选中：显示 8 个控制点
- 多选：Shift + 点击
- 拖拽：实时更新位置
- 缩放：保持比例（按住 Shift）
- 旋转：中心点旋转

**视图控制：**
- 鼠标滚轮：缩放画布（50% - 200%）
- 空格 + 拖拽：平移画布
- 双击对象：进入编辑模式（文字）

### 4.4 主题配色方案

```css
/* 深色科技风格（默认） */
:root {
  --bg-deep: #06090f;
  --bg-card: #0d1117;
  --accent-blue: #58a6ff;
  --accent-cyan: #56d4dd;
  --border: #1b2230;
  --text: #e6edf3;
}

/* 浅色商务风格 */
:root.light {
  --bg-deep: #ffffff;
  --bg-card: #f6f8fa;
  --accent-blue: #0969da;
  --border: #d0d7de;
  --text: #24292f;
}
```

### 4.5 键盘快捷键

- `Ctrl/Cmd + S`: 保存草稿
- `Ctrl/Cmd + Z`: 撤销
- `Ctrl/Cmd + Shift + Z`: 重做
- `Delete`: 删除选中对象
- `Escape`: 取消选择
- `Space + 拖拽`: 平移画布

---

## 第 5 部分：错误处理与边界情况

### 5.1 错误分类与处理策略

| 错误类型 | 检测方式 | 用户提示 | 恢复策略 |
|---------|---------|---------|---------|
| **LLM 未配置** | 检查 `.llm_config.json` | "⚠️ 未配置 LLM，请运行 `/pipeline-config`" | 引导用户配置 |
| **LLM 调用失败** | HTTP 状态码 ≠ 200 | "🔴 AI 连接失败，正在重试..." | 自动重试 3 次 |
| **Wiki 为空** | 扫描返回 0 个页面 | "📚 知识库为空，您可以：1. 先摄入文档<br>2. 使用自由模式（无 Wiki）" | 提供选项 |
| **模板解析失败** | `python-pptx` 异常 | "⚠️ 模板文件损坏，使用默认主题" | 降级到默认主题 |
| **生成超时** | 计时器 > 5 分钟无输出 | "⏱️ 生成超时，是否保存已完成部分？" | 提供保存选项 |
| **用户取消** | AbortController 触发 | "已停止，已生成 N 个幻灯片" | 保存已完成部分 |
| **导出失败** | python-pptx 异常 | "❌ 导出失败：具体原因" | 显示错误日志 |
| **网络断开** | SSE onerror | "🔌 连接断开，尝试重连..." | 自动重连 3 次 |

### 5.2 状态恢复机制

**场景：用户关闭浏览器后重新打开**

```python
class SessionManager:
    """持久化会话状态"""

    def save_session(self, job_id: str):
        """保存到本地存储"""
        state = {
            'job_id': job_id,
            'slides': self.state_manager.get(job_id).slides,
            'user_edits': self.state_manager.get(job_id).user_edits,
            'timestamp': datetime.now().isoformat()
        }
        # 保存到 .liveppt_session.json
        with open('.liveppt_session.json', 'w') as f:
            json.dump(state, f)

    def restore_session(self) -> Optional[str]:
        """恢复上次会话"""
        if os.path.exists('.liveppt_session.json'):
            with open('.liveppt_session.json') as f:
                state = json.load(f)
            return state['job_id']
        return None
```

### 5.3 边界情况处理

**Wiki 内容过多：**
- 限制：最多选择 20 个 Wiki 页面
- 超过时提示："内容过多，可能影响生成质量，建议选择 10 个以内"

**LLM 上下文溢出：**
- 检测：token 数 > 模型上下文窗口
- 策略：智能摘要，保留关键信息

**图片过大：**
- 限制：单个图片 < 5MB
- 自动压缩：前端上传前压缩到 2MB 以内

**用户编辑破坏布局：**
- 检测：对象超出画布边界
- 提示："部分内容超出幻灯片范围，是否自动调整？"

---

## 第 6 部分：性能优化

### 6.1 前端性能优化

**Fabric.js 渲染优化：**
```javascript
// 1. 对象池（复用 Fabric 对象）
const objectPool = new Map();

function getOrCreateText(id, config) {
  if (!objectPool.has(id)) {
    objectPool.set(id, new fabric.Text('', config));
  }
  return objectPool.get(id);
}

// 2. 虚拟滚动（只渲染可见幻灯片）
const visibleRange = [currentSlideIndex - 1, currentSlideIndex + 1];

// 3. 防抖处理（拖拽时减少重绘）
let renderTimeout;
function onObjectMove() {
  clearTimeout(renderTimeout);
  renderTimeout = setTimeout(() => {
    canvas.renderAll();
  }, 16); // 60fps
}
```

**SSE 连接优化：**
```javascript
// 批量处理 token（减少 DOM 操作）
const tokenBatch = [];
const BATCH_INTERVAL = 50; // ms

setInterval(() => {
  if (tokenBatch.length > 0) {
    const text = tokenBatch.join('');
    updateCanvas(text);
    tokenBatch.length = 0;
  }
}, BATCH_INTERVAL);
```

### 6.2 后端性能优化

**LLM 调用优化：**
```python
from functools import lru_cache

class OptimizedGeneratorAgent:
    def __init__(self):
        self.cache = {}

    def generate_with_cache(self, prompt: str):
        cache_key = hashlib.md5(prompt.encode()).hexdigest()
        if cache_key in self.cache:
            return self.cache[cache_key]

        result = self.llm.call_streaming(prompt)
        self.cache[cache_key] = result
        return result
```

**Wiki 内容缓存：**
```python
class CachedWikiProvider:
    def __init__(self):
        self.content_cache = {}
        self.scan_cache = None
        self.last_scan_time = None

    def gather(self, wiki_ids: List[str]):
        # 5分钟内复用扫描结果
        if (self.last_scan_time and
            time.time() - self.last_scan_time < 300):
            pass  # 使用缓存
        else:
            self._scan_all_wiki()
```

### 6.3 性能目标

- **生成速度**: 10 页 PPT < 2 分钟
- **编辑器延迟**: < 100ms
- **首屏加载**: < 3 秒
- **内存占用**: < 500MB
- **SSE 响应时间**: < 200ms

---

## 第 7 部分：实施计划

### 7.1 开发阶段划分

| 阶段 | 时间 | 任务 |
|------|------|------|
| **阶段 1** | 1-2周 | 基础设施：React + Fabric.js 集成，Flask 后端架构调整，SSE 通信 |
| **阶段 2** | 2-3周 | 核心引擎：SlideInducter 集成，StreamingEngine，GenerationStateManager |
| **阶段 3** | 2周 | UI/UX 实现：Fabric 编辑器，Wiki 选择器，控制面板 |
| **阶段 4** | 1-2周 | LLM 集成：PlannerAgent，GeneratorAgent，EditorAgent |
| **阶段 5** | 1周 | 模板系统：模板上传，布局归纳，样式应用 |
| **阶段 6** | 1周 | 导出功能：Fabric JSON → PPTX 转换 |
| **阶段 7** | 1-2周 | 测试与优化：集成测试，性能优化，用户测试 |

**总计：10-13周**

### 7.2 关键里程碑

| 里程碑 | 时间点 | 交付物 |
|--------|--------|--------|
| M1: 基础框架 | 第2周末 | 前后端通信正常，Fabric 画布可显示 |
| M2: 核心引擎 | 第5周末 | LLM 可流式生成，智能分批工作 |
| M3: 编辑器 | 第7周末 | 可视化编辑器完整实现 |
| M4: 模板系统 | 第8周末 | 可上传模板并学习布局 |
| M5: 完整流程 | 第10周末 | 端到端：启动→生成→编辑→导出 |
| M6: 优化发布 | 第13周末 | 性能优化，测试通过，可发布 |

### 7.3 技术依赖

**前端依赖：**
```json
{
  "fabric": "^6.0.0",
  "react": "^18.2.0",
  "react-dom": "^18.2.0",
  "@types/fabric": "^5.3.0",
  "eventsource": "^2.0.0"
}
```

**Python 依赖：**
```requirements
flask>=3.0.0
flask-cors>=4.0.0
python-pptx>=1.0.0
opencv-python>=4.8.0
numpy>=1.24.0
```

### 7.4 文件结构

```
backend/ppt/
├── __init__.py
├── pipeline.py              # 主管道（已有）
├── agents.py                # LLM agents（已有）
├── wiki_context.py          # Wiki 集成（已有）
├── template_analyzer.py     # 模板分析（已有）
├── exporter.py              # PPTX 导出（已有）
├── models.py                # 数据模型（已有）
├── inductor.py              # NEW: 布局归纳（来自 PPTAgent）
├── streaming_engine.py      # NEW: 智能分批流式
├── state_manager.py         # NEW: 生成状态管理
└── liveppt_server.py        # Flask 服务器（迁移到此处）

demo/
├── liveppt_v2/              # NEW: 完整前端
│   ├── index.html
│   ├── App.jsx
│   ├── components/
│   │   ├── WikiSelector.jsx
│   │   ├── SlideCanvas.jsx
│   │   ├── ControlPanel.jsx
│   │   └── ChatPanel.jsx
│   ├── fabric/
│   │   ├── CanvasManager.js
│   │   ├── ObjectFactory.js
│   │   └── EditHandler.js
│   ├── api/
│   │   └── client.js
│   └── styles/
│       └── main.css
```

### 7.5 风险与缓解措施

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|---------|
| PPTAgent 集成复杂 | 高 | 中 | 提前 PoC 验证，必要时简化功能 |
| Fabric.js 性能问题 | 中 | 低 | 使用对象池、虚拟滚动 |
| LLM 成本过高 | 中 | 中 | 添加 token 计数和预算提醒 |
| 时间延期 | 高 | 中 | 分阶段交付，优先核心功能 |

---

## 第 8 部分：测试策略

### 8.1 单元测试

```python
# tests/test_inductor.py
def test_layout_induction_accuracy():
    inductor = SlideInducter()
    layouts = inductor.analyze('testdata/template.pptx')
    assert len(layouts) >= 3
    assert any(l.name == 'title-center' for l in layouts)

# tests/test_streaming_engine.py
def test_thinking_detection():
    engine = StreamingEngine()
    # Mock slow LLM
    events = list(engine.stream_with_pacing(slow_mock_llm()))
    assert any(e['type'] == 'thinking' for e in events)

# tests/test_exporter.py
def test_export_validity():
    exporter = PPTXExporter()
    fabric_json = load_test_json()
    exporter.export(fabric_json, '/tmp/test.pptx')
    # 验证文件可被 PowerPoint 打开
    assert os.path.exists('/tmp/test.pptx')
```

### 8.2 集成测试

```python
# tests/integration/test_full_flow.py
def test_pause_edit_resume():
    # 1. 开始生成
    response = client.post('/api/generate', json={
        'wiki_ids': ['rag'],
        'instruction': '做一个 PPT'
    })

    # 2. 暂停
    client.post(f'/api/pause/{job_id}')

    # 3. 编辑
    client.post(f'/api/slide/{job_id}/0/edit', json={
        'fabric_json': {...}
    })

    # 4. 继续
    client.post(f'/api/resume/{job_id}')

    # 5. 验证生成了完整的幻灯片
    assert len(state.slides) > 0
```

### 8.3 性能测试

```python
# tests/performance/test_generation_speed.py
def test_10_slides_under_2_minutes():
    start = time.time()
    generate_ppt(wiki_ids=['test'], instruction='生成 10 页')
    duration = time.time() - start
    assert duration < 120
```

### 8.4 用户测试

- **测试用户**: 5 人
- **测试场景**: 完整流程（启动→生成→暂停→编辑→继续→导出）
- **收集反馈**: SUS 可用性量表，定性访谈

---

## 总结

### 核心特性

✅ **真实直播体验** - 智能分批流式，思考时有透明提示
✅ **人机协作** - 暂停-编辑-继续，AI 感知用户修改
✅ **模板学习** - PPTAgent 布局归纳，复用用户模板风格
✅ **高级编辑** - Fabric.js 完整 PPT 编辑器
✅ **Wiki 集成** - 语料来自项目知识库
✅ **PPTX 导出** - 高质量导出，保持格式

### 技术亮点

🚀 **前端** - Fabric.js + React，高性能 Canvas 编辑
⚡ **流式引擎** - 智能分批，动态调整节奏
🧠 **布局学习** - PPTAgent SlideInducter 集成
📊 **状态管理** - 暂停/恢复，上下文保持

### 预期成果

- **开发周期**: 10-13 周
- **代码行数**: 约 8000-10000 行（含前端和后端）
- **交付物**: 完整的 LivePPT 系统，用户可通过 `/pipeline-ppt` 启动

---

**文档版本**: 1.0
**最后更新**: 2026-04-13
