交互式 PPT 创建与编辑工作流 — 全程用自然语言完成，一键交互。

使用方法：/pipeline-ppt $ARGUMENTS

$ARGUMENTS 可选，作为主题提示词。

---

## 执行步骤

### 第一步：获取 Python 路径（Read 工具，不使用终端）

**用 Read 工具**（不是终端命令）读取**当前工作区根目录**的 `.claude_settings.json`，取 `python_path` 字段。

- **如果找到且 `python_path` 非空** → 记为 PYTHON
- **找不到文件或缺少 `python_path`** → 再用 Read 工具读取 `~/.agents/skills/knowledge-pipline/.claude_settings.json`
- **仍然找不到** → **必须用 AskUserQuestion 询问用户（不可跳过、不可猜测、不可用终端探测）**：
  ```
  ⚠️ 未找到 Python 路径配置。本命令需要 Python 来运行脚本。
  请输入您的 python.exe 完整路径
  （例如：C:\Users\86187\AppData\Local\Programs\Python\Python312\python.exe）
  ```
  用户输入后：
  1. 用终端验证：`"用户输入的路径" --version`
     - 失败 → 提示路径无效，重新询问
  2. 保存到**当前工作区根目录**的 `.claude_settings.json`：
     ```json
     { "python_path": "用户输入的路径" }
     ```
  3. 记为 PYTHON，继续

**⚠️ 禁止在此步骤使用终端命令（bash/PowerShell）。** 只用 Read 工具读取 JSON 文件即可。

### 第二步：定位脚本并一键初始化

#### 2a. 定位 fastpath 脚本（Read 工具，不使用终端）

**用 Read 工具**依次尝试读取以下路径，取第一个存在的作为 FASTPATH：
1. `~/.agents/skills/knowledge-pipline/tools/pipeline_ppt_fastpath.py`
2. `~/.claude/skills/knowledge-pipline/tools/pipeline_ppt_fastpath.py`

> Windows 上 `~` = `C:\Users\{用户名}`，即检查：
> - `C:\Users\86187\.agents\skills\knowledge-pipline\tools\pipeline_ppt_fastpath.py`
> - `C:\Users\86187\.claude\skills\knowledge-pipline\tools\pipeline_ppt_fastpath.py`

如果都不存在 → 提示用户安装 knowledge-pipline skill，**立即停止**。

#### 2b. 执行初始化（一条终端命令）

```
"PYTHON" "FASTPATH" bootstrap --port 5679
```

> **PYTHON 和 FASTPATH 都必须是绝对路径**，示例：
> `"C:\Users\86187\AppData\Local\Programs\Python\Python312\python.exe" "C:\Users\86187\.agents\skills\knowledge-pipline\tools\pipeline_ppt_fastpath.py" bootstrap --port 5679`

**⚠️ 绝对禁止使用相对路径 `tools/pipeline_ppt_fastpath.py`** — bash 的 CWD 不一定是工作区根目录或 SKILL_DIR，会导致 "No such file" 错误。

**该脚本内部自动完成以下全部工作：**
1. ✅ 自动定位 SKILL_DIR（搜索 `~/.agents/skills/` 和 `~/.claude/skills/`）
2. ✅ 校验 `SKILL_DIR/.llm_config.json` LLM 配置
3. ✅ 启动或复用预览服务器（`http://localhost:5679`）
4. ✅ 按分类打印 wiki 下所有 `.md` 的完整编号列表
5. ✅ 生成 `SKILL_DIR/output/_wiki_index_map.json`

**从输出第一行捕获 `SKILL_DIR=<路径>`**，后续所有步骤均使用该路径。

同时从输出捕获 `WIKI_DOC_LIST=<路径>`，这是人类可读的文档编号列表文件。

**⚠️ 终端输出的文档列表可能被截断（Claude Code 限制行数）。第①步必须用 Read 工具读取 `WIKI_DOC_LIST` 文件来展示完整列表，不要依赖终端滚动输出。**

若输出包含以下任一失败标记，必须立即停止并提示用户：
- `LLM_CONFIG_OK=false` → 提示运行 `/pipeline-config` 配置 LLM
- `SERVER_OK=false` → 提示检查端口占用，查看 `SKILL_DIR/output/_server_stderr.log`
- `WIKI_EMPTY=true` → 提示先运行 `/pipeline-ingest` 摄入文档

**⚠️ 绝对禁止以下行为（历史上造成 20 分钟级超时的根因）：**
- 用 `test -d`、`Test-Path`、bash `if/elif/fi` 探测 SKILL_DIR
- 用终端命令检查 `.llm_config.json` 是否存在
- 拆分初始化为多条 shell 命令
- 使用相对路径调用 Python 脚本
- 上述全部已封装在 Python 脚本中，**一条命令完成**

### 第三步：Python 失败时的回退

如果第二步 Python 脚本报错或无法运行：
1. 用 Read 工具手动定位 SKILL_DIR：依次读取 `~/.agents/skills/knowledge-pipline/wiki/index.md` 和 `~/.claude/skills/knowledge-pipline/wiki/index.md`，哪个存在取哪个
2. 用 Read 工具读取 `SKILL_DIR/.llm_config.json`，不存在则提示 `/pipeline-config`
3. 用 `list_dir` 列出 `SKILL_DIR/wiki/sources/`、`entities/`、`concepts/`、`syntheses/` 下的 `.md` 文件
4. 按分类编号打印给用户
5. 继续后续交互步骤

### 第四步：交互式三步选择（严格顺序，逐步提问，全程中文）

快路径脚本执行完后，再按顺序交互。

输出示例：
```
── sources ──
  1. sources/claude-code-leak.md
  2. sources/demo-example.md
── entities ──
  3. entities/OpenAI.md
── concepts ──
  4. concepts/RAG.md
  5. concepts/ReinforcementLearning.md
── syntheses ──
  6. syntheses/analysis-2024.md
```

如果 wiki 下没有任何 .md 文件，提示用户先运行 `/pipeline-ingest` 摄入文档，**立即停止**。

---

#### 第 ① 步 — 手动输入编号选择 Wiki 文档（必选，禁止跳过，禁止 Claude 自行决定）

**⚠️ 关键约束：Claude 不得自行决定使用哪些文档，必须让用户明确输入编号。**

由于 AskUserQuestion 存在选项数量限制，**第①步禁止使用 options 列表承载全部文档**。

第①步必须这样做：
1. **用 Read 工具读取 `WIKI_DOC_LIST` 文件**（上一步捕获的路径，通常是 `SKILL_DIR/output/_wiki_doc_list.txt`），将完整文档编号列表展示给用户
   - **⚠️ 绝对不要说"请参考上方终端的完整列表"** — 终端输出会被截断，用户看不到完整列表
   - 必须把读到的列表内容直接展示在对话中
2. 用 AskUserQuestion 仅提一个中文自由输入问题，让用户手动输入编号
3. 收到用户输入后，执行固定解析命令（不要让 LLM 手写解析逻辑）

```bash
python "SKILL_DIR/tools/pipeline_ppt_fastpath.py" parse-selection "用户输入原文"
```

解析结果会写入：`SKILL_DIR/output/_selected_wiki_docs.json`

AskUserQuestion 要求：
- `allowFreeformInput: true`
- 不提供文档 options（或仅提供“查看上方终端完整列表后输入编号”的提示项）
- 问题文案必须明确支持多选与区间

推荐提问文案：

```
📂 请输入要使用的文档编号（必选，可多选）
请参考上方列表，输入编号，支持逗号与区间。
示例：1,3,8-12
```

**规则：**
- 用户必须输入具体编号，至少 1 个（如 `5`、`1,4,9`、`2-6`、`1,3,8-10`）
- **禁止** Claude 替用户决定选哪些、跳过选择、或聚合分组后让用户选"主题"
- **禁止**把选择入口做成“安全类/技术类/分析类/产品类”等分类入口
- 收到输入后，必须调用 `parse-selection` 命令解析并校验
- 若输入非法（非数字、范围错误、越界、空输入），必须用中文提示重输
- 解析成功后，从 `_selected_wiki_docs.json` 读取选中路径，再用 `read_file` 完整读取每个选中文件内容，作为第五步素材

#### 交互语言硬约束（必须遵守）

- 从第 ① 步到导出提示，**所有交互文案必须是中文**
- AskUserQuestion 的标题、问题、选项、错误提示、确认提示都必须是中文
- 不得出现英文交互文案（文件路径与命令本身除外）

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

#### 第 ③ 步 — 选择主题模板（必选，用户手动输入单选编号）

**不要分批展示模板，不要用“更多模板”分流，也不要让 Claude 代替用户选。**

第 ③ 步必须这样做：
1. 读取 `SKILL_DIR/demo/ppt_live/templates.json` 中的**全部内置模板**
2. 再读取 `SKILL_DIR/demo/ppt_live/user_templates.json` 中的**全部用户上传模板**（如果文件存在）
3. 将两者合并后，**一次性完整列出当前所有可用模板**，按 1 开始连续编号
4. 在列表最后额外加一个编号项：`上传新 PPTX 模板`
5. 用 AskUserQuestion **仅提一个中文自由输入问题**，让用户手动输入**一个单选编号**
6. 收到输入后，必须校验：
   - 必须是纯数字
   - 只能选一个编号，**禁止多选**、禁止区间、禁止逗号分隔
   - 编号必须在合法范围内
   - 非法则必须中文提示并要求重输

**⚠️ 上传模板必须持久化：**
- 用户上传的模板不是一次性临时选项
- `upload-template` 成功后，模板会保存到 `user_templates.json`
- 后续再次执行 `/pipeline-ppt` 时，必须再次读取 `user_templates.json`，把这些用户模板继续列入可选项
- **禁止**把上传模板只放在当前对话的临时 options 里，下一轮又丢失

推荐展示格式：

```
🎨 当前所有可用模板（单选）

  1. 🌑 深色科技 [内置] — dark-tech
  2. 🌊 午夜商务 [内置] — midnight-exec
  3. 🪸 活力珊瑚 [内置] — coral-energy
  ...
  9. 📎 浅色版模板 [用户上传] — my-light-template
  10. 📤 上传新 PPTX 模板
```

推荐提问文案：

```
🎨 请输入模板编号（必选，只能单选）
请从上方完整模板列表中输入 1 个编号。
例如：3
```

**处理逻辑：**
- **选中某个内置模板** → 从对应 theme 读取色值 → 进入 **HTML 模式生成**（第五步）
- **选中某个用户上传模板** → 使用该持久化模板 → 进入相应生成流程
- **选中最后一个“上传新 PPTX 模板”编号** → 进入 **模板识别子流程**（见下方）

---

#### 模板识别子流程（选了「上传新 PPTX 模板」时触发）

1. 用 AskUserQuestion 询问 PPTX 文件路径（允许自由输入）
2. 终端执行上传识别：
   ```
   python "SKILL_DIR/demo/ppt_live/pptx_live.py" upload-template "用户给的路径"
   ```
3. 读取识别结果，展示模板的布局信息给用户确认
4. 识别成功后，**回到第 ① 步重新开始** — 再次让用户选择 Wiki 文档
5. 第二轮到达第 ③ 步时，必须重新读取 `templates.json + user_templates.json`，完整列表里会包含用户刚上传的模板，用户再输入单选编号

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

**⚠️ 推送方式（关键 — 必须使用目录模式，禁止 JSON 模式）：**

HTML 含大量双引号，嵌入 JSON 后极易转义失败导致 `Expecting ',' delimiter` 解析错误。
**因此必须使用目录模式 — 每页一个 .html 文件，彻底规避 JSON 转义问题。**

**⚠️ 写文件前必须先处理输出目录：**
- `create_file` / `Write` 只适合创建新文件，**不会稳定覆盖已存在的同名文件**
- 如果继续复用 `SKILL_DIR/output/_tmp_slides/`，而里面已经有 `slide-01.html`、`slide-02.html` 等旧文件，就会出现“Error writing file”
- 因此每次生成前必须二选一：
  1. 使用**全新目录名**，例如 `SKILL_DIR/output/_tmp_slides_run_20260416_153000/`
  2. 或先清空旧的 `_tmp_slides/` 目录，再开始写入
- **优先推荐全新目录名**，这样不会和上一次生成残留文件冲突

**正确做法 — 两步：**
1. 先选定一个**当前这次生成专用的空目录**（记为 `SLIDES_DIR`），然后用 `create_file` 为每页创建独立 HTML 文件：
  - 推荐：`SLIDES_DIR=SKILL_DIR/output/_tmp_slides_run_<时间戳>/`
  - 如果坚持使用固定目录 `SKILL_DIR/output/_tmp_slides/`，必须先删除其中旧文件
  - `SLIDES_DIR/slide-01.html` — 封面页的完整 HTML
  - `SLIDES_DIR/slide-02.html` — 第二页的完整 HTML
  - `SLIDES_DIR/slide-03.html` — 以此类推...
   - 每个文件只包含一个 `<div style="width:960px;height:540px;...">...</div>`
   - **文件名必须用零填充两位数字**（`slide-01`，不是 `slide-1`），确保排序正确
   - 无需任何 JSON 转义，HTML 原样写入即可

2. 终端执行推送（一条命令推送整个目录）：
   ```
  python "SKILL_DIR/demo/ppt_live/pptx_live.py" push "SLIDES_DIR"
   ```

**⚠️ 绝对禁止以下做法（历史上反复导致 JSON 解析失败的根因）：**
- 在旧目录里直接重写同名 `slide-01.html`、`slide-02.html` 等文件
- 把 HTML 嵌入 JSON 字符串（`{"html": "<div style=\"...\">"}` — 引号转义极易出错）
- 写入 `_tmp_slides.json` 单文件（已废弃）
- 用 `python -c "..."` 内联推送
- 用 `--inline` 参数推送

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
| 复杂批量修改 | `state` → 修改后写入 `_tmp_slides/` 目录 → `push` 目录 |

**执行稳定性要求（减少 20 分钟级重试）：**
- 编辑后必须立即执行一次 `state`，确认页数、标题和顺序已落盘
- 若是结构变更（插入/删除/换页），必须再执行 `goto N` 验证目标页可见
- 如验证失败，优先重推完整 `push`，禁止连续盲改

### 第八步：导出

当用户说"导出"时，**不要使用终端 CLI 导出**（服务器端导出不稳定），直接提示用户：

```
📥 请在浏览器页面中点击左上角的「导出 PPTX」按钮下载文件。
浏览器端导出使用 html2canvas + PptxGenJS，效果更准确。
```

---

## 关键原则

1. **所有路径必须是绝对路径** — PYTHON、FASTPATH、SKILL_DIR 全部用绝对路径，禁止相对路径
2. **两步启动** — 第一步 Read 工具取 Python 路径 → 第二步 Read 工具定位脚本 + 一条命令完成全部初始化
3. **禁止终端探测目录** — 不用 `test -d`、`Test-Path`、`if/elif/fi`，全部由 Read 工具或 Python 脚本完成
3. **三步严格交互** — ① 必选 wiki 文档 ② 描述需求 ③ 必选模板编号，按顺序逐步提问
4. **选项受限** — 第 ③ 步禁止自由输入（`allowFreeformInput: false`），只能从选项中选择
5. **第①步只能手动输入原始文件编号** — 不得使用分类选项，不得只展示少量“热门文档”
6. **全程中文交互** — 用户可见的提问与提示必须全部中文
7. **上传模板触发子流程** — 识别完毕后回到第 ① 步重新选择，第 ③ 步会多出第 9 个选项
8. **不写临时 Python 脚本** — 只用 `create_file` 写 JSON + CLI 推送
9. **绝不嵌入 HTML 到 shell** — 先写 JSON 文件，再 push 文件路径
10. **每次编辑后先验证再继续** — `state` / `goto` 失败时先修复状态同步，避免错误累积到导出
