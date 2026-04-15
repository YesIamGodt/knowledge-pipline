交互式 PPT 创建与编辑工作流 — 全程用自然语言完成，一键交互。

使用方法：/pipeline-ppt $ARGUMENTS

$ARGUMENTS 可选，作为主题提示词。

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/.agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**后续所有操作中的 wiki/、tools/、demo/ppt_live/、output/、backend/ppt/ 都指 SKILL_DIR 下的子目录。**

### 第二步：检查 LLM 配置

读取 `SKILL_DIR/.llm_config.json`。
- 如果不存在 → 提示用户先运行 `/pipeline-config`，然后停止。
- 如果存在 → 继续。

### 第三步：执行快路径初始化

在终端运行（将 SKILL_DIR 替换为实际绝对路径）：
```
python "SKILL_DIR/tools/pipeline_ppt_fastpath.py" bootstrap --port 5679
```

该命令一次性完成：
- 启动或复用预览服务器（`http://localhost:5679`）
- 按分类打印 wiki 下所有 `.md` 的完整编号列表
- 生成 `SKILL_DIR/output/_wiki_index_map.json`

若输出包含以下任一失败标记，必须立即停止并提示用户：
- `SERVER_OK=false` → 提示检查端口占用或 `server.py` 是否存在
- `WIKI_EMPTY=true` → 提示先运行 `/pipeline-ingest` 摄入文档

### 第四步：Python 失败时的回退

如果 Python 不可用或脚本报错：
1. 手动用 `list_dir` 列出 `SKILL_DIR/wiki/sources/`、`entities/`、`concepts/`、`syntheses/` 下的 `.md` 文件
2. 按分类编号打印给用户
3. 继续后续交互步骤

### 第五步：交互式三步选择（严格顺序，逐步提问，全程中文）

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
1. 上一步终端已打印完整编号列表
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
请参考上方终端的完整列表，输入编号，支持逗号与区间。
示例：1,3,8-12
```

**规则：**
- 用户必须输入具体编号，至少 1 个（如 `5`、`1,4,9`、`2-6`、`1,3,8-10`）
- **禁止** Claude 替用户决定选哪些、跳过选择、或聚合分组后让用户选"主题"
- **禁止**把选择入口做成“安全类/技术类/分析类/产品类”等分类入口
- 收到输入后，必须调用 `parse-selection` 命令解析并校验
- 若输入非法（非数字、范围错误、越界、空输入），必须用中文提示重输
- 解析成功后，从 `_selected_wiki_docs.json` 读取选中路径，再用 `read_file` 完整读取每个选中文件内容，作为第六步素材

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
- **选 1-8** → 从 `SKILL_DIR/demo/ppt_live/templates.json` 读取对应 theme 色值 → 进入 **HTML 模式生成**（第六步）
- **选 9（已上传模板）** → 进入 **克隆模式生成**（第六步）
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

### 第六步：生成 PPT（三阶段流程）

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

### 第七步：进入编辑模式

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

### 第八步：处理后续编辑

用户的每句话翻译为 CLI 命令（所有命令前缀 `python "SKILL_DIR/demo/ppt_live/pptx_live.py"`）：

| 用户说 | CLI 命令 |
|--------|----------|
| 第 N 页标题改成 X | `edit N --title "X"` |
| 第 A 和 B 页对调 | `swap A B` |
| 删掉第 N 页 | `delete N` |
| 所有页背景改成 X | `batch --theme-bg "X"` |
| 复杂批量修改 | `state` → 修改 JSON → `push` |

**执行稳定性要求（减少 20 分钟级重试）：**
- 编辑后必须立即执行一次 `state`，确认页数、标题和顺序已落盘
- 若是结构变更（插入/删除/换页），必须再执行 `goto N` 验证目标页可见
- 如验证失败，优先重推完整 `push`，禁止连续盲改

### 第九步：导出

当用户说"导出"时，**不要使用终端 CLI 导出**（服务器端导出不稳定），直接提示用户：

```
📥 请在浏览器页面中点击左上角的「导出 PPTX」按钮下载文件。
浏览器端导出使用 html2canvas + PptxGenJS，效果更准确。
```

---

## 关键原则

1. **所有路径基于 SKILL_DIR** — 安装后统一在 `~/.agents/skills/knowledge-pipline` 下
2. **快路径脚本** — `python "SKILL_DIR/tools/pipeline_ppt_fastpath.py" bootstrap` 完成服务启动 + wiki 编号
3. **三步严格交互** — ① 必选 wiki 文档 ② 描述需求 ③ 必选模板编号，按顺序逐步提问
4. **选项受限** — 第 ③ 步禁止自由输入（`allowFreeformInput: false`），只能从选项中选择
5. **第①步只能手动输入原始文件编号** — 不得使用分类选项，不得只展示少量“热门文档”
6. **全程中文交互** — 用户可见的提问与提示必须全部中文
7. **上传模板触发子流程** — 识别完毕后回到第 ① 步重新选择，第 ③ 步会多出第 9 个选项
8. **不写临时 Python 脚本** — 只用 `create_file` 写 JSON + CLI 推送
9. **绝不嵌入 HTML 到 shell** — 先写 JSON 文件，再 push 文件路径
10. **每次编辑后先验证再继续** — `state` / `goto` 失败时先修复状态同步，避免错误累积到导出
