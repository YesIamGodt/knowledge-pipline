交互式 PPT 创建与编辑工作流 — 全程用自然语言完成，一键交互。

使用方法：/pipeline-ppt $ARGUMENTS

$ARGUMENTS 可选，作为主题提示词。

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR（一次性检测，禁止分两次检查）

**只运行这一条 PowerShell 命令**，一次性输出 SKILL_DIR：

```powershell
$p1 = "$env:USERPROFILE\.agents\skills\knowledge-pipline"; $p2 = "$env:USERPROFILE\.claude\skills\knowledge-pipline"; if (Test-Path $p1) { "SKILL_DIR=$p1" } elseif (Test-Path $p2) { "SKILL_DIR=$p2" } else { "ERROR: knowledge-pipline skill not found" }
```

- 输出 `SKILL_DIR=C:\Users\xxx\...` → 将该完整路径设为 SKILL_DIR，继续执行
- 输出 `ERROR` → 提示用户安装 skill，**立即停止**

⚠️ **禁止分两次单独检查两个路径再判断** — 这是已知 BUG：分开检查时，第二次的 `NOT_FOUND` 输出会被误拼入路径，导致后续所有步骤使用错误的 SKILL_DIR。

**后续所有路径都指 SKILL_DIR 下的子目录：**
- `demo/ppt_live/` — 服务器、CLI、模板
- `wiki/` — 知识库文档
- `uploads/templates/` — 用户上传的 PPTX 模板
- `output/` — 输出文件
- `backend/ppt/` — 生成引擎

### 第二步：检查 LLM 配置

读取 `SKILL_DIR/.llm_config.json`。
- 如果不存在 → 提示用户先运行 `/pipeline-config`，然后停止。
- 如果存在 → 继续。

### 第三步：启动预览服务器（异步后台）

在异步终端中启动（不阻塞 Agent）：

```
python "SKILL_DIR/demo/ppt_live/server.py"
```

- 服务器会自动杀死旧进程（内置 `_kill_existing_server`）
- **不要加 `--open`**，VS Code / IDE 会自动检测端口弹出预览
- 等待看到 `LivePPT Preview Server` 输出后继续
- 如果启动失败，告诉用户手动在终端执行此命令，但**不要跳过**

### 第四步：交互式三步选择（严格顺序，逐步提问）

在服务器启动的同时，用 Agent 工具准备数据，然后**按顺序**逐步与用户交互。

#### 准备：用终端列举 wiki 下所有 .md 文件（必须用终端，禁止用 list_dir 自行推断）

**在终端运行以下命令**，按目录结构列出 `SKILL_DIR/wiki/` 下所有 .md 文件并编号：

```powershell
$wiki = "SKILL_DIR\wiki"; $n=1; foreach ($sub in @("sources","entities","concepts","syntheses")) { $dir="$wiki\$sub"; if (Test-Path $dir) { Write-Host "── $sub ──"; Get-ChildItem $dir -Filter "*.md" | Sort-Object Name | ForEach-Object { Write-Host "  $n. $($_.Name)"; $n++ } } }
```

（将 `SKILL_DIR` 替换为第一步得到的实际路径）

输出示例：
```
── sources ──
  1. claude-code-leak.md
  2. demo-example.md
── entities ──
  3. OpenAI.md
── concepts ──
  4. RAG.md
  5. ReinforcementLearning.md
── syntheses ──
  6. analysis-2024.md
```

如果 wiki 下没有任何 .md 文件，提示用户先运行 `/pipeline-ingest` 摄入文档，**立即停止**。

---

#### 第 ① 步 — 按编号选择 Wiki 文档（必选，禁止跳过，禁止 Claude 自行决定）

**⚠️ 关键约束：Claude 不得自行决定使用哪些文档，必须让用户明确选择编号。**

使用 AskUserQuestion，**必须提供 options 列表，`allowFreeformInput: false`，`multiSelect: true`**。

将终端输出的每个编号文件作为独立 option，格式为 `编号. 目录/文件名`：

```
📂 请选择 PPT 素材文档（必选，可多选）
选择后将读取对应文件的完整内容作为 PPT 素材。

options:
  1. sources/claude-code-leak.md
  2. sources/demo-example.md
  3. entities/OpenAI.md
  4. concepts/RAG.md
  5. concepts/ReinforcementLearning.md
  6. syntheses/analysis-2024.md
```

**规则：**
- 用户必须从列表中**选择具体编号**，至少选 1 个
- **禁止** Claude 替用户决定选哪些、跳过选择、或聚合分组后让用户选"主题"
- options 数组必须与终端输出的编号文件一一对应，一行一个
- 用户选择后，用 `read_file` 完整读取每个选中文件的内容，作为第五步的 PPT 素材

---

#### 第 ② 步 — 描述 PPT 内容需求

使用 AskUserQuestion，**允许自由输入（`allowFreeformInput: true`）**。

Claude 先基于第 ① 步选中的文档内容，给出一段理解摘要和建议的 PPT 主题方向，作为默认选项供用户直接选择：

```
📝 PPT 内容方向

根据您选择的文档，我理解的主题方向：
  「XXX 分析报告 — 涵盖 A、B、C 三个方面，建议 10 页左右」

您可以选择此方向，或自己描述：
```

options 中放 Claude 生成的建议选项（可以 1-2 个），用户也可以自由输入修改。

如果 $ARGUMENTS 非空，将其作为推荐选项的一部分。

---

#### 第 ③ 步 — 选择主题模板（必选，禁止自由输入）

使用 AskUserQuestion，**必须提供 options 列表，`allowFreeformInput: false`，`multiSelect: false`**。

**基础 8 个内置主题 + 可选的用户已上传模板：**

```
🎨 选择 PPT 风格（必选）

  1. 🌑 深色科技 dark-tech
  2. 🌊 午夜商务 midnight-exec
  3. 🪸 活力珊瑚 coral-energy
  4. 🌿 森林苔藓 forest-moss
  5. 🏺 暖色陶土 warm-terra
  6. ⬜ 极简浅色 light-minimal
  7. 🫐 莓果奶油 berry-cream
  8. 🍒 樱桃大胆 cherry-bold
  9. [用户已上传模板名称]    ← 仅当用户之前上传过模板时才出现
  📤 上传新 PPTX 模板
```

**规则：**
- 用户只能选 1-8（或 1-9 如果有已上传模板），或选「上传新 PPTX 模板」
- **禁止自由输入**

**处理逻辑：**
- **选 1-8** → 从 `SKILL_DIR/demo/ppt_live/templates.json` 读取对应 theme 色值 → 进入 **HTML 模式生成**（第五步）
- **选 9（已上传模板）** → 进入 **克隆模式生成**（第五步）
- **选「上传新 PPTX 模板」** → 进入 **模板识别子流程**（见下方）

---

#### 模板识别子流程（选了「上传新 PPTX 模板」时触发）

1. 用 AskUserQuestion 询问 PPTX 文件路径（允许自由输入）
2. 终端执行上传识别：
   ```
   python "SKILL_DIR/demo/ppt_live/pptx_live.py" upload-template "用户给的路径"
   ```
3. 读取识别结果，展示模板的布局信息给用户确认
4. 识别成功后，**回到第 ① 步重新开始** — 再次让用户选择 Wiki 文档
5. 第二轮到达第 ③ 步时，选项列表中会多出第 9 个选项（用户刚上传的模板），用户此时选 1-9

**为什么要回到第 ① 步？** 因为模板识别可能改变用户对内容的想法，需要重新确认素材和需求。

---

### 第五步：生成 PPT（三阶段流程）

无论哪种模式，都经过「内容分析 → 大纲规划 → 逐页生成」三阶段。

#### 阶段 A：内容分析

阅读 wiki 文档 + 用户需求，提取结构化信息映射到幻灯片类型：

| 提取项 | → 幻灯片类型 |
|--------|-------------|
| 核心论点 / 主标题 | 封面 cover |
| 3-5 个大主题分组 | 章节 section + 内容页 |
| 关键数字 / KPI | 数据 stats |
| 引用 / 金句 | 引言 quote |
| 对比关系 | 对比 comparison |
| 时间线 / 流程 | 时间线 timeline |
| 要点列表 | 要点 bullets |
| 表格数据 | 表格 table |
| 结论 | 结尾 ending |

素材不足不硬凑 — 宁缺毋滥。

#### 阶段 B：大纲规划

**约束：**
- 总页数 6-15 页
- 相邻两页**禁止相同布局**
- 封面 = 第 1 页，结尾 = 最后 1 页
- 每 3-5 页内容前放 section 分隔页（总页 > 8 时）
- bullets 类不超总页数 40%
- 特殊布局至少出现 2 种

#### 阶段 C-1：HTML 模式（选了内置主题 1-8）

每张幻灯片 = 自包含 `<div style="width:960px;height:540px;...">`，inline CSS。

**硬性约束：**
1. 根元素 `<div style="width:960px;height:540px;overflow:hidden;...">`
2. 所有样式 inline — 无 `<style>` 块
3. 字体 `Inter, 'Noto Sans SC', sans-serif`
4. 无 `<script>`
5. 统一使用选定主题色值
6. **内容绝不能溢出 960×540** — 根 div 必须加 `overflow:hidden`，内容过多必须拆页

**内容密度（严格遵守，宁少勿多）：**
- 标题 ≤10 字
- 要点 15-25 字/条，每页 ≤4 条（绝不超过 5 条）
- 引言 ≤50 字
- 正文段落 ≤3 行，每行 ≤30 字
- 内容放不下 → **必须拆成多页**，绝不压缩字号塞进一页
- 每页底部保留至少 40px 空白，防止内容贴底

参考 `SKILL_DIR/demo/ppt_live/SKILL.md` 中的 12 种 HTML 模板，但 LLM 有完全创意自由。

**⚠️ 推送方式（关键 — 必须遵守）：**

HTML 含引号，**绝对不要**嵌入 `python -c "..."` 等 shell 命令！

**正确做法 — 两步：**
1. 用 `create_file` 写入 JSON 文件 `SKILL_DIR/output/_tmp_slides.json`：
   ```json
   [{"html": "<div style=\"width:960px;height:540px;...\">...</div>"},
    {"html": "<div style=\"width:960px;height:540px;...\">...</div>"}]
   ```
2. 终端执行推送：
   ```
   python "SKILL_DIR/demo/ppt_live/pptx_live.py" push "SKILL_DIR/output/_tmp_slides.json"
   ```

#### 阶段 C-2：克隆模式（选了上传的 PPTX 模板）

通过 CLI 完成克隆生成（不需要写 Python 脚本）：

1. 用 `create_file` 写入 outline JSON 到 `SKILL_DIR/output/_tmp_outline.json`：
   ```json
   [
     {"purpose": "Cover", "topic": "标题", "content": "副标题"},
     {"purpose": "Content", "topic": "核心发现", "content": "从wiki获取的内容..."},
     {"purpose": "Section", "topic": "第二部分"},
     {"purpose": "Content", "topic": "数据分析", "content": "..."},
     {"purpose": "Ending", "topic": "谢谢", "content": "联系方式"}
   ]
   ```
2. 终端执行克隆生成：
   ```
   python "SKILL_DIR/demo/ppt_live/pptx_live.py" clone-generate "模板路径" "SKILL_DIR/output/_tmp_outline.json" -o "SKILL_DIR/output/文件名.pptx"
   ```

### 第六步：进入编辑模式

生成完成后告诉用户：
```
✅ PPT 已生成 N 页，浏览器已实时显示。

💡 你可以继续用自然语言编辑：
- "第 3 页标题改成 XXX"
- "第 5 和第 6 页对调"
- "删掉最后一页"
- "在第 4 页后插入一页关于 XXX 的内容"
- "把背景色全部换成深蓝色"

📥 导出 PPTX：请点击浏览器页面左上角的「导出 PPTX」按钮
```

### 第七步：处理后续编辑

用户的每句话翻译为 CLI 命令（所有命令前缀 `python "SKILL_DIR/demo/ppt_live/pptx_live.py"`）：

| 用户说 | CLI 命令 |
|--------|----------|
| 第 N 页标题改成 X | `edit N --title "X"` |
| 第 A 和 B 页对调 | `swap A B` |
| 删掉第 N 页 | `delete N` |
| 所有页背景改成 X | `batch --theme-bg "X"` |
| 复杂批量修改 | `state` → 修改 JSON → `push` |

### 第八步：导出

当用户说"导出"时，**不要使用终端 CLI 导出**（服务器端导出不稳定），直接提示用户：

```
📥 请在浏览器页面中点击左上角的「导出 PPTX」按钮下载文件。
浏览器端导出使用 html2canvas + PptxGenJS，效果更准确。
```

---

## 关键原则

1. **所有路径基于 SKILL_DIR** — 安装后统一在 `~/.agents/skills/knowledge-pipline` 下
2. **服务器必须启动** — 实时预览 + CLI 推送都依赖它
3. **三步严格交互** — ① 必选 wiki 文档 ② 描述需求 ③ 必选模板编号，按顺序逐步提问
4. **选项受限** — 第 ① ③ 步禁止自由输入（`allowFreeformInput: false`），只能从选项中选择
5. **上传模板触发子流程** — 识别完毕后回到第 ① 步重新选择，第 ③ 步会多出第 9 个选项
6. **不写临时 Python 脚本** — 只用 `create_file` 写 JSON + CLI 推送
7. **绝不嵌入 HTML 到 shell** — 先写 JSON 文件，再 push 文件路径
