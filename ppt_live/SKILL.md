# LivePPT — 双模式 PPT 生成技能

> **架构**：LLM 直接生成 HTML slides → Flask SSE 推送 → 浏览器渲染（预览模式）
> 　　　　LLM 生成结构化 JSON → python-pptx 填充模板 → 原生可编辑 PPTX（模板模式）
> **预览**：http://localhost:5679 | **导出**：模板模式 = 原生 PPTX；HTML 模式 = PptxGenJS + html2canvas

---

## 一、核心概念

每张幻灯片 = **一个自包含的 HTML `<div>`**，尺寸固定 960×540px。

LLM 拥有完全的创意自由 — 用 HTML + inline CSS 画出任何你想要的视觉效果。不再受限于固定的 15 种 JSON 布局类型。

### 数据格式

Server 接收的 JSON：
```json
{
  "slides": [
    {"html": "<div style='width:960px;height:540px;...'>...</div>"},
    {"html": "<div style='width:960px;height:540px;...'>...</div>"}
  ],
  "current": 0
}
```

每个 slide 对象只有一个字段：`html`，包含完整的 HTML 字符串。

### 硬性约束

1. **根元素必须是** `<div style="width:960px;height:540px;...">`
2. **所有样式必须 inline** — 无外部 CSS，无 `<style>` 块
3. **字体** — 只用：`Inter, 'Noto Sans SC', sans-serif`（已由 shell 加载）
4. **不要用 `<script>`** — 纯视觉，不需要交互
5. **图片** — 用 `<img>` 标签，`src` 指向 `/uploads/images/xxx.png` 或公共 URL
6. **不超过 3000 字符/slide** — 保持 HTML 精简

---

## 二、配色主题

从 `templates.json` 加载 8 套预设主题。生成时选定一套，所有 slide 统一配色：

| 主题 | 背景 bg | 标题 title | 正文 body | 强调 accent | 弱化 muted |
|------|---------|-----------|----------|------------|-----------|
| dark-tech 深色科技 | `#0f1318` | `#ffffff` | `#c9d1d9` | `#58a6ff` | `#8b949e` |
| midnight-exec 午夜商务 | `#1E2761` | `#ffffff` | `#CADCFC` | `#CADCFC` | `#8899bb` |
| coral-energy 活力珊瑚 | `#2F3C7E` | `#F9E795` | `#f0f0f0` | `#F96167` | `#b0b8d0` |
| forest-sage 森林翠 | `#1B2A21` | `#ffffff` | `#d0e0d8` | `#4EBF8B` | `#7ca090` |
| sunset-warm 暖阳橙 | `#2B1B11` | `#FFF0D4` | `#e8d5c0` | `#FF8C42` | `#a08060` |
| arctic-clean 极光白 | `#0C1B33` | `#ffffff` | `#c0d8f0` | `#70C1FF` | `#6090b0` |
| purple-dream 紫韵 | `#1A0A2E` | `#ffffff` | `#d5c8e8` | `#B07DFF` | `#8060a0` |
| minimal-mono 极简黑白 | `#121212` | `#ffffff` | `#b0b0b0` | `#ffffff` | `#666666` |

**用法**：在生成所有 slide 前确定主题颜色，然后在每个 HTML 的 inline style 中使用对应的色值。

---

## 三、PPT 生成策略（核心 — 必须遵循）

### 阶段 A：内容分析

从用户素材（wiki 文档、自然语言描述）中提取结构化信息，映射到幻灯片类型：

| 素材类型 | 适合的幻灯片 |
|----------|-------------|
| 核心论点 / 主标题 | → 封面页 |
| 大章节分组 | → 章节分隔页 |
| 关键数字 / KPI | → 数据指标页 |
| 引言 / 金句 | → 引言页 |
| 对比关系（A vs B） | → 对比页 |
| 时间线 / 里程碑 | → 时间线页 |
| 顺序流程 / 步骤 | → 流程步骤页 |
| 功能特性列表 | → 图标卡片页 |
| 要点列表 | → 要点列表页 |
| 图片素材 | → 图文混排页 |
| 结构化数据 | → 表格页 |
| 结论 / 行动号召 | → 结尾页 |

**关键：素材不足以填某类页面时不要硬凑。**

### 阶段 B：大纲规划

遵守硬约束：

1. **相邻两页禁止使用相同布局类型**
2. **封面必须是第 1 页，结尾必须是最后 1 页**
3. **纯列表页不超过总页数的 40%**
4. **特殊布局（数据/时间线/对比/引言/表格/流程）至少出现 2 种**
5. **每 3-5 页内容前放一个章节分隔页**（总页数 > 8 时）
6. **总页数 6-15 页**

### 阶段 C：逐页生成 HTML

每页独立生成 HTML `<div>`。下面的模板是参考起点，你可以自由调整和创新。

---

## 四、幻灯片 HTML 模板参考

以下用 `${bg}` `${title}` `${accent}` `${body}` `${muted}` 表示主题色。生成时替换为实际色值。

**每种模板都给出一个参考布局，但鼓励变体**。每种类型至少有 2-3 种可行布局——选择时考虑内容量和上下文：

| 类型 | 变体思路 |
|------|----------|
| 封面 | 居中式 / 左对齐式 / 全图背景+半透明文字 |
| 要点 | 编号列表 / 图标列表 / 卡片网格 |
| 图标卡片 | 2×2 / 3列 / 2列大卡 |
| 对比 | 左右分栏 / 上下对照 / 表格式 |
| 数据指标 | 横排大数字 / 2×2网格 / 单指标突出+辅助指标 |
| 时间线 | 横向连线 / 纵向列表 / 蛇形曲线 |
| 流程步骤 | 横向箭头 / 纵向步骤卡 / 圆形迭代 |
| 表格 | 标准表格 / 矩阵点阵 / 对比卡片组 |

### 1. 封面页 (Cover)

```html
<div style="width:960px;height:540px;background:linear-gradient(135deg,${bg},#1a2332);display:flex;flex-direction:column;justify-content:center;padding:48px 72px;font-family:Inter,'Noto Sans SC',sans-serif;position:relative;overflow:hidden">
  <div style="position:absolute;width:400px;height:400px;border-radius:50%;top:-80px;right:-100px;background:${accent};opacity:0.06"></div>
  <span style="display:inline-block;font-size:12px;font-weight:600;padding:4px 14px;border-radius:14px;background:${accent}22;color:${accent};margin-bottom:12px;width:fit-content">标签文字</span>
  <div style="font-size:42px;font-weight:700;color:${title};line-height:1.2">主标题</div>
  <div style="width:64px;height:3px;background:${accent};border-radius:2px;margin:16px 0 20px"></div>
  <div style="font-size:19px;color:${muted}">副标题描述</div>
  <div style="position:absolute;bottom:32px;left:72px;font-size:14px;color:${muted}">作者  ·  2024-01</div>
  <div style="position:absolute;bottom:0;left:0;width:100%;height:5px;background:${accent}"></div>
</div>
```

### 2. 章节分隔页 (Section)

```html
<div style="width:960px;height:540px;background:linear-gradient(135deg,${bg},#1a2332);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-family:Inter,'Noto Sans SC',sans-serif;position:relative;overflow:hidden">
  <div style="position:absolute;left:0;top:0;width:5px;height:100%;background:${accent}"></div>
  <div style="font-size:110px;font-weight:900;color:${accent};opacity:0.1;position:absolute;top:50%;left:50%;transform:translate(-50%,-65%)">01</div>
  <div style="font-size:34px;font-weight:700;color:${title};position:relative;z-index:2">章节名称</div>
  <div style="font-size:17px;color:${muted};margin-top:14px;max-width:60%;position:relative;z-index:2">一句话描述</div>
</div>
```

### 3. 要点列表页 (Bullets)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 52px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:16px">页面标题</div>
  <div style="display:flex;flex-direction:column;gap:10px;flex:1">
    <div style="display:flex;align-items:center;gap:14px;padding:14px 18px;background:rgba(255,255,255,0.04);border-radius:10px;border:1px solid rgba(255,255,255,0.06)">
      <span style="width:28px;height:28px;border-radius:50%;background:${accent};display:flex;align-items:center;justify-content:center;font-size:13px;font-weight:700;color:#fff;flex-shrink:0">1</span>
      <span style="font-size:15px;color:${body};line-height:1.5">要点内容 15-25 字</span>
    </div>
    <!-- 重复 3-6 条 -->
  </div>
</div>
```

### 4. 图标卡片页 (Icon Cards)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:20px">核心能力</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;flex:1">
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;border:1px solid rgba(255,255,255,0.06);padding:24px 20px;display:flex;flex-direction:column;align-items:center;text-align:center;gap:8px">
      <div style="font-size:32px">🚀</div>
      <div style="font-size:16px;font-weight:600;color:${title}">卡片标题</div>
      <div style="font-size:13px;color:${muted};line-height:1.5">一句话描述</div>
    </div>
    <!-- 重复 3-6 个卡片 -->
  </div>
</div>
```

### 5. 对比页 (Comparison / VS)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:20px;text-align:center">方案对比</div>
  <div style="display:flex;gap:20px;flex:1;align-items:stretch">
    <div style="flex:1;background:rgba(255,255,255,0.04);border-radius:12px;padding:24px;border:1px solid rgba(255,255,255,0.06)">
      <div style="font-size:18px;font-weight:600;color:${accent};margin-bottom:16px">方案 A</div>
      <div style="font-size:14px;color:${body};line-height:1.8">• 特点一<br>• 特点二<br>• 特点三</div>
    </div>
    <div style="display:flex;align-items:center;font-size:20px;font-weight:900;color:${accent};opacity:0.5">VS</div>
    <div style="flex:1;background:rgba(255,255,255,0.04);border-radius:12px;padding:24px;border:1px solid rgba(255,255,255,0.06)">
      <div style="font-size:18px;font-weight:600;color:${accent};margin-bottom:16px">方案 B</div>
      <div style="font-size:14px;color:${body};line-height:1.8">• 特点一<br>• 特点二<br>• 特点三</div>
    </div>
  </div>
</div>
```

### 6. 数据指标页 (Stats / KPI)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:24px">关键指标</div>
  <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:20px;flex:1;align-content:center">
    <div style="background:rgba(255,255,255,0.04);border-radius:12px;padding:28px 24px;text-align:center;border:1px solid rgba(255,255,255,0.06)">
      <div style="font-size:14px;margin-bottom:8px">📊</div>
      <div style="font-size:36px;font-weight:800;color:${accent}">99.9%</div>
      <div style="font-size:14px;color:${muted};margin-top:8px">服务可用性</div>
    </div>
    <!-- 重复 2-4 个指标 -->
  </div>
</div>
```

### 7. 时间线页 (Timeline)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:24px">发展里程碑</div>
  <div style="display:flex;align-items:flex-start;flex:1;padding:0 20px;position:relative">
    <!-- 横线 -->
    <div style="position:absolute;top:16px;left:40px;right:40px;height:2px;background:${accent};opacity:0.3"></div>
    <!-- 节点 -->
    <div style="flex:1;display:flex;flex-direction:column;align-items:center;position:relative;z-index:2">
      <div style="width:14px;height:14px;border-radius:50%;background:${accent};margin-bottom:12px"></div>
      <div style="font-size:14px;font-weight:700;color:${accent}">2020</div>
      <div style="font-size:13px;color:${body};text-align:center;margin-top:8px;max-width:120px">项目启动</div>
    </div>
    <!-- 重复 3-5 个节点 -->
  </div>
</div>
```

### 8. 引言页 (Quote)

```html
<div style="width:960px;height:540px;background:linear-gradient(135deg,${bg},#1a2332);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;padding:48px 80px;font-family:Inter,'Noto Sans SC',sans-serif;position:relative;overflow:hidden">
  <div style="position:absolute;top:60px;left:40px;font-size:240px;font-family:Georgia,serif;color:${accent};opacity:0.06;line-height:1">"</div>
  <div style="font-size:24px;font-style:italic;font-family:Georgia,'Noto Sans SC',serif;line-height:1.65;color:${title};max-width:75%;position:relative;z-index:2">引言内容，50 字以内</div>
  <div style="width:48px;height:2px;background:${accent};border-radius:1px;margin:18px auto"></div>
  <div style="font-size:15px;color:${muted}">—— 署名</div>
</div>
```

### 9. 流程步骤页 (Process)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:24px">实施步骤</div>
  <div style="display:flex;gap:12px;flex:1;align-items:center">
    <div style="flex:1;background:rgba(255,255,255,0.04);border-radius:12px;padding:20px 16px;text-align:center;border:1px solid rgba(255,255,255,0.06)">
      <div style="width:36px;height:36px;border-radius:50%;background:${accent};display:flex;align-items:center;justify-content:center;font-size:16px;font-weight:700;color:#fff;margin:0 auto 10px">1</div>
      <div style="font-size:14px;font-weight:600;color:${title}">需求分析</div>
      <div style="font-size:12px;color:${muted};margin-top:6px">短描述</div>
    </div>
    <div style="font-size:18px;color:${accent};opacity:0.4">→</div>
    <!-- 重复 3-5 步 -->
  </div>
</div>
```

### 10. 表格页 (Table)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;flex-direction:column;padding:36px 48px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:20px">功能矩阵</div>
  <table style="width:100%;border-collapse:separate;border-spacing:0;border-radius:10px;overflow:hidden;font-size:14px">
    <thead>
      <tr style="background:${accent}">
        <th style="padding:12px 16px;text-align:left;color:#fff;font-weight:600">功能</th>
        <th style="padding:12px 16px;text-align:left;color:#fff;font-weight:600">方案 A</th>
        <th style="padding:12px 16px;text-align:left;color:#fff;font-weight:600">方案 B</th>
      </tr>
    </thead>
    <tbody>
      <tr style="background:rgba(255,255,255,0.03)">
        <td style="padding:10px 16px;color:${body};border-bottom:1px solid rgba(255,255,255,0.06)">性能</td>
        <td style="padding:10px 16px;color:${body};border-bottom:1px solid rgba(255,255,255,0.06)">★★★</td>
        <td style="padding:10px 16px;color:${body};border-bottom:1px solid rgba(255,255,255,0.06)">★★</td>
      </tr>
      <!-- 斑马纹：偶数行 background:transparent -->
    </tbody>
  </table>
</div>
```

### 11. 图文混排页 (Image + Text)

```html
<div style="width:960px;height:540px;background:${bg};display:flex;padding:36px 48px;gap:32px;font-family:Inter,'Noto Sans SC',sans-serif;overflow:hidden">
  <div style="flex:1;display:flex;flex-direction:column;justify-content:center">
    <div style="font-size:26px;font-weight:700;color:${title};margin-bottom:12px">产品架构</div>
    <div style="font-size:15px;color:${body};line-height:1.7;margin-bottom:16px">描述文字，2-3 句话。</div>
    <div style="font-size:14px;color:${muted};line-height:1.8">• 补充要点一<br>• 补充要点二</div>
  </div>
  <div style="flex:1;display:flex;align-items:center;justify-content:center">
    <img src="/uploads/images/xxx.png" style="max-width:100%;max-height:100%;border-radius:10px;object-fit:contain" alt="">
  </div>
</div>
```

没有图片时，右侧用占位框：
```html
<div style="flex:1;display:flex;align-items:center;justify-content:center;background:rgba(255,255,255,0.03);border-radius:12px;border:2px dashed rgba(255,255,255,0.1)">
  <span style="font-size:48px;opacity:0.3">🖼️</span>
</div>
```

### 12. 结尾页 (Ending)

```html
<div style="width:960px;height:540px;background:linear-gradient(135deg,${bg},#1a2332);display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;font-family:Inter,'Noto Sans SC',sans-serif;position:relative;overflow:hidden">
  <div style="font-size:36px;margin-bottom:16px">🎯</div>
  <div style="font-size:40px;font-weight:700;color:${title}">感谢聆听</div>
  <div style="font-size:18px;color:${muted};margin-top:16px;max-width:55%">欢迎交流讨论</div>
  <div style="position:absolute;bottom:40px;font-size:13px;color:${muted}">email@example.com</div>
  <div style="position:absolute;bottom:0;left:0;width:100%;height:5px;background:${accent}"></div>
</div>
```

---

## 五、设计系统

### 视觉风格配方

同一套内容可以用不同的视觉风格呈现。根据演示场景选择合适的风格：

| 风格 | 圆角 | 间距 | 适用场景 |
|------|------|------|----------|
| **Sharp 利落** | 0~2px | 紧凑 | 数据报告、财务汇报、专业分析 |
| **Soft 柔和** | 6~10px | 适中 | 企业展示、商务提案、通用汇报 |
| **Rounded 圆润** | 12~20px | 宽松 | 产品介绍、营销方案、创意展示 |
| **Pill 胶囊** | 24px+ | 开阔 | 品牌发布、发布会、高端展示 |

**风格映射到 CSS：**
```
Sharp:   border-radius: 0~2px;   padding: 10~14px; gap: 8~12px;
Soft:    border-radius: 6~10px;  padding: 14~20px; gap: 12~18px;
Rounded: border-radius: 12~20px; padding: 20~28px; gap: 18~28px;
Pill:    border-radius: 24px+;   padding: 24~36px; gap: 24~36px;
```

### 排版层级

| 用途 | 字号 | 字重 | 说明 |
|------|------|------|------|
| 数据大字 | 48~72px | 800 | KPI 数字、核心指标 |
| 封面/节标题 | 36~44px | 700 | 封面、章节分隔页 |
| 页面标题 | 24~28px | 700 | 内容页标题 |
| 副标题 | 18~22px | 600 | 二级标题 |
| 正文 | 14~16px | 400 | 正文、要点（**不要加粗**） |
| 注释/来源 | 11~13px | 400 | 脚注、数据来源（用 muted 色） |

**关键规则**：
- **正文禁止加粗** — bold 只用于标题和 heading，正文永远 `font-weight: 400`
- **标题左对齐** — 正文段落和要点列表左对齐，不要居中
- **字号对比** — 标题必须 ≥ 24px 以与 14~16px 正文形成层级差

### 间距系统

| 用途 | 推荐值 |
|------|--------|
| 图标与文字间距 | 6~12px |
| 列表项间距 | 12~18px |
| 卡片内边距 | 16~28px |
| 元素组间距 | 20~36px |
| 页面安全边距 | 36~52px |
| 大区块间距 | 36~60px |

### 演示风格（扩展）

除了配色主题外，可叠加以下视觉风格，适应不同场合：

| 风格名 | 视觉特征 | 适合场景 |
|--------|----------|----------|
| **Glassmorphism 毛玻璃** | 半透明卡片 + backdrop-filter + 微弱边框 | 科技、AI、未来感 |
| **Neo-Brutalist 新粗野** | 粗黑边框 + 明亮色块 + 高对比 | 创意、设计、独立品牌 |
| **Editorial 杂志** | 大留白 + 衬线字体 + 精致排版 | 文化、学术、编辑内容 |
| **Minimal Swiss 瑞士极简** | 网格系统 + 无衬线 + 几何构成 | 设计、建筑、极简主义 |
| **Gradient Modern 渐变现代** | 大面积渐变 + 发光效果 + 圆形装饰 | 互联网、SaaS、产品发布 |
| **Dark Premium 暗夜高端** | 深色底 + 金/白点缀 + 精致排版 | 金融、奢侈品、高端汇报 |

**Glassmorphism 卡片模板**：
```
background: rgba(255,255,255,0.05);
backdrop-filter: blur(12px);
border: 1px solid rgba(255,255,255,0.08);
border-radius: 12px;
```

**Neo-Brutalist 卡片模板**：
```
background: #FFE500;
border: 3px solid #000;
border-radius: 0;
box-shadow: 6px 6px 0 #000;
color: #000;
```

### 字体搭配

| 标题字体 | 正文字体 | 风格 |
|----------|----------|------|
| Inter (默认) | Inter | 现代中性 |
| Georgia, serif | Inter | 严肃优雅 |
| 'Noto Sans SC' bold | 'Noto Sans SC' | 中文主导 |
| Inter Black | Inter Light | 极致对比 |

> 注：当前系统已加载 `Inter` 和 `Noto Sans SC`，引言页可用 `Georgia, serif` 增加变化。

### 页码

**每页必须包含页码**（封面页除外）。标准位置：右下角。

```html
<div style="position:absolute;bottom:16px;right:24px;font-size:11px;color:${muted};opacity:0.6">3 / 12</div>
```

格式：`当前页 / 总页数`。页码用 muted 色 + 低透明度，不抢视觉焦点。

---

## 六、创意自由 — 超越模板

上面的模板只是参考。LLM 直接写 HTML，意味着你可以创造任何布局：

- **多列不等宽布局** — `display:flex` + 不同 `flex` 值
- **叠加装饰元素** — 渐变圆、斜条纹、几何图形（用 `position:absolute`）
- **渐变文字** — `background:linear-gradient(...); -webkit-background-clip:text; -webkit-text-fill-color:transparent`
- **进度条 / 仪表盘** — 嵌套 div 实现
- **卡片阴影** — `box-shadow` 层次感
- **强调某条数据** — 更大字号、不同颜色、单独卡片

**目标**：每张幻灯片都应该有独特的视觉表达，不要千篇一律。

### 设计原则

1. **留白** — 不要塞满整页，至少留 30% 空间
2. **层级** — 标题 > 关键数字 > 正文 > 注释，字号递减
3. **对比** — 用强调色突出最重要的信息
4. **对齐** — 元素之间保持对齐和间距一致
5. **避免 AI 味** — 不要加底部强调线到每一页、不要每页都用相同的装饰圆

### 内容深度要求（核心 — 防止内容空洞）

**问题**：最大的败笔不是视觉不好看，而是内容太水、太空洞。每一页必须有实质性信息。

**硬性要求**：
1. **标题要具体** — ❌ "项目概述" → ✅ "Q3 营收增长 37%：三大核心业务全面领跑"
2. **数据要有来源感** — 不要凭空写 "99.9%"，要和素材对应的真实数据一致
3. **要点要有洞见** — ❌ "团队协作很重要" → ✅ "跨部门审批周期从 14 天压缩到 3 天"
4. **对比要有结论** — 不要只列特点，要明确说哪个更优、为什么
5. **时间线要有因果** — 不只是年份+事件，要说明关键转折的因果逻辑
6. **引言要有重量** — 选最有冲击力的原文金句，不要自己编
7. **结尾要有行动** — 不要只写 "谢谢"，要有明确的 Next Steps 或 Call to Action

**每页内容检查清单**：
- [ ] 这页删掉后，听众会少获得什么信息？（如果答案是 "没什么" → 删掉或重写）
- [ ] 标题能否让观众不看正文就知道核心结论？
- [ ] 正文里有没有至少一个具体数字、案例、或引用？

### 高级视觉技巧（提升质感）

**渐变背景** — 不要用纯色背景，至少用两色渐变：
```
background: linear-gradient(135deg, #0f1318 0%, #1a2332 50%, #0d1825 100%);
```

**多层装饰** — 用 2-3 个半透明几何图形叠加，避免单调：
```html
<div style="position:absolute;width:500px;height:500px;border-radius:50%;top:-200px;right:-150px;background:radial-gradient(circle,${accent}15 0%,transparent 70%)"></div>
<div style="position:absolute;width:200px;height:200px;border:2px solid ${accent}15;border-radius:50%;bottom:60px;left:-80px"></div>
```

**发光强调** — 给关键数字加辉光效果：
```
text-shadow: 0 0 40px ${accent}40, 0 0 80px ${accent}20;
```

**毛玻璃卡片** — 比纯色卡片高级：
```
background: rgba(255,255,255,0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.08);
```

**渐变文字** — 用于关键数字或标题：
```
background: linear-gradient(135deg, ${accent}, #fff);
-webkit-background-clip: text;
-webkit-text-fill-color: transparent;
```

**进度条/仪表** — 用嵌套 div 实现可视化：
```html
<div style="width:100%;height:8px;background:rgba(255,255,255,0.1);border-radius:4px;overflow:hidden">
  <div style="width:73%;height:100%;background:linear-gradient(90deg,${accent},#50e3c2);border-radius:4px"></div>
</div>
```

**不同页面差异化装饰** — 避免所有页面看起来一样：
- 封面：大面积渐变 + 透明装饰圆
- 数据页：网格点阵背景（用 radial-gradient 的 repeating-radial-gradient）
- 对比页：中间分割线 + 左右不同底色
- 引言页：超大引号装饰 + 居中布局
- 结尾页：放射渐变中心聚焦效果

---

## 七、CLI 命令速查

```bash
# ── HTML 预览模式 ──

# 推送完整 PPT（从文件）— ✅ 推荐方式
python ppt_live/pptx_live.py push slides.json

# ❌ 绝对不要用 --inline 传含引号的 HTML！会因引号嵌套导致 shell 解析失败
# python ppt_live/pptx_live.py push --inline '[{"html": "..."}]'

# 编辑单页（替换整页 HTML）
python ppt_live/pptx_live.py edit 3 --html "<div style='width:960px;height:540px;...'>新内容</div>"

# 删除 / 插入 / 交换
python ppt_live/pptx_live.py delete 4
python ppt_live/pptx_live.py insert 3 --html "<div style='width:960px;height:540px;...'>插入的页</div>"
python ppt_live/pptx_live.py swap 2 5

# 批量修改（主题色替换）
python ppt_live/pptx_live.py batch --theme-bg "#1a1a2e" --theme-accent "#e94560"

# 导航 / 状态 / 导出
python ppt_live/pptx_live.py goto 3
python ppt_live/pptx_live.py state
python ppt_live/pptx_live.py export output/演示.pptx
```

**HTML 模式实际操作**：生成完整 PPT 时，**必须**先用 create_file 工具写 JSON 文件再 push：

⚠️ **绝对不要把 HTML 内容嵌入 `python -c "..."` 等 shell 命令！** HTML 中的引号会导致 shell 解析失败（`unexpected EOF while looking for matching '`）。

```python
# ✅ 正确：用 create_file 工具写入 slides.json，然后在终端执行：
# python ppt_live/pptx_live.py push slides.json

# ❌ 错误：不要把 HTML 放进 python -c 或 bash -c 命令
```

**模板模式实际操作**：先上传模板，再写结构化 JSON 生成：

```python
import json
```

---

## 八、编辑模式指南

| 用户说 | 你执行 |
|--------|--------|
| "第 N 页标题改成 X" | `state` → 获取当前 slide HTML → 修改标题 → `edit N --html "..."` |
| "所有页换颜色" | `state` → 批量替换色值 → `push` |
| "第 A 和 B 对调" | `swap A B` |
| "删掉第 N 页" | `delete N` |
| "在第 N 页后插入..." | 新建 HTML slide → `insert N+1 --html "..."` |
| "导出" | `export output/文件名.pptx` |
| 复杂批量修改 | `state` → 修改 JSON → `push` |

---

## 九、内容密度规则

- **标题**：10 字以内
- **要点**：每条 15-25 字，一眼可读
- **每页要点不超过 6 条**（推荐 3-4）
- **引言**：50 字以内
- **KPI 数字**：大字 + 短描述，不超过 4 个
- **内容太多则拆页** — 宁可多一页也不要塞满

## 十、Emoji 图标选择

- 选择语义相关的 emoji
- 同组 items 风格一致（如都用实物 📊📈📉 或都用抽象 ⚡🔒🚀）
- 推荐图标集：
  - 通用：🎯 📊 ⚡ 🔒 🚀 💡 🌟 ✅
  - 技术：🔧 💻 🖥️ ⚙️ 🛠️ 📡 🔌 🧠
  - 商务：📈 💰 🏢 👥 🤝 📋 🎯 🏆
  - 安全：🛡️ 🔐 🚨 ⚠️ 🔍 👁️ 🛑 ✋

## 十一、QA 检查与常见陷阱

### 自检流程

**生成完 PPT 后，假设存在问题，逐页检查**：

1. **内容检查** — 标题是否具体？数据是否真实？要点有洞见？
2. **布局多样性** — 相邻两页是否用了不同布局？有没有连续 3 页看起来一样？
3. **视觉一致性** — 色值是否统一？字号层级是否一致？间距是否整齐？
4. **页码** — 除封面外每页都有页码？
5. **可读性** — 字号够大？对比度够？文字不会被装饰元素遮挡？

### 常见 AI 生成陷阱（必须避免）

| 陷阱 | 修正 |
|------|------|
| ❌ 每页底部都加一条强调线 | ✅ 只在封面和结尾用，内容页不要 |
| ❌ 每页都放一个装饰圆 | ✅ 差异化装饰：数据页用网格点、对比页用分割线、引言页用引号 |
| ❌ 所有标题都居中 | ✅ 内容页标题左对齐，只有封面/引言/章节页居中 |
| ❌ 正文全部加粗 | ✅ 正文 `font-weight: 400`，只有标题加粗 |
| ❌ 配色太多 | ✅ 严格使用选定主题的 5~6 个色值，不随意引入新颜色 |
| ❌ 空洞标题（"项目概述"） | ✅ 带结论的标题（"Q3 营收增长 37%"） |
| ❌ 6 页长得一模一样 | ✅ 每页至少变一个维度：布局方向、装饰风格、信息密度 |
| ❌ 所有卡片都是 3 列等宽 | ✅ 混用 2 列、3 列、4 列、不等宽 |

### 视觉一致性检查清单

- [ ] 所有页面使用相同的背景色（或同系渐变）
- [ ] 标题字号在 24~28px 范围内统一
- [ ] 正文字号在 14~16px 范围内统一
- [ ] 强调色只用主题的 accent 色
- [ ] 卡片圆角保持一致（同一风格配方）
- [ ] 安全边距一致（推荐 36~48px）

---

## 十二、关键原则

1. **直接生成 HTML** — 每张 slide 是自包含的 `<div>`，不是 JSON 对象
2. **布局多样性** — 相邻不重复，特殊布局至少 2 种
3. **每次操作后浏览器自动刷新** — 不需要手动刷新
4. **用户永远不需要接触 HTML** — 你负责翻译自然语言到 HTML
5. **先写 JSON 文件再 push** — `[{"html":"..."}, {"html":"..."}]`
6. **使用 `state` 了解当前状态** — 编辑前先看
7. **统一主题配色** — 选定主题后所有 slide 使用同一套色值
8. **从 wiki 获取内容** — 读取 wiki 文档作为素材
9. **内容精炼** — 宁缺毋滥，不硬凑
10. **创意自由** — 模板只是起点，请创造独特的视觉效果

---

## 十三、PPTX 导出功能

浏览器内置一键导出：点击预览界面左上角的 **「📥 导出 PPTX」** 按钮即可下载可编辑的 PPTX 文件。

### 导出原理

1. **html2canvas** — 对每页 HTML 截图为 PNG（2x 清晰度）作为幻灯片背景图
2. **DOM 文字提取** — 遍历 DOM 树，提取每个文字元素的位置、字号、颜色、对齐方式
3. **PptxGenJS** — 在浏览器中生成 PPTX 文件，背景图 + 文字叠加层 = 可编辑的 PPTX

### 导出效果

- ✅ 视觉 100% 还原（因为背景是截图）
- ✅ 文字可选中、可编辑（因为提取了文字层）
- ✅ 完全离线，无需服务器
- ⚠️ 表格和复杂布局的文字提取可能有偏差，但视觉保真

### 导出适配最佳实践

为了获得最佳导出效果，生成 HTML 时注意：
- **文字用 `<div>` 或 `<span>` 包裹** — 方便 DOM 提取
- **避免 `transform: rotate()`** — 旋转文字在导出时位置可能偏移
- **不用 `overflow: hidden` 的嵌套裁剪** — 截图可以正确渲染，但文字提取可能遗漏
- **装饰性文字（如大号背景 "01"）** — 导出时自动跳过 `fontSize > 80` 的元素

---
