基于知识维基生成交互式 Live PPT 演示文稿。

使用方法：/pipeline-ppt $ARGUMENTS

$ARGUMENTS 是演示主题，例如：`AI安全分析` 或 `RAG技术详解 --theme apple`

可选标志（追加在主题后面）：
- `--pages N`：指定幻灯片数量（默认自动）
- `--theme THEME`：主题风格 dark|light|apple|warm|minimal（默认 dark）
- `--sources LIST`：逗号分隔的源 slug 列表（默认使用全部）
- `--open`：生成后自动在浏览器中打开

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/.agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**后续所有操作中的 wiki/、tools/、graph/ 都指 SKILL_DIR 下的子目录。**

### 第二步：检查 LLM 配置

读取 `SKILL_DIR/.llm_config.json`。
- 如果不存在 → 提示用户先运行 `/pipeline-config`，然后停止。
- 如果存在 → 继续。

### 第三步：执行 PPT 生成

在终端运行：
```
python "SKILL_DIR/tools/pipeline_ppt.py" "$ARGUMENTS" --open
```

默认输出到 `SKILL_DIR/graph/liveppt.html`。

示例：
```
python "SKILL_DIR/tools/pipeline_ppt.py" "AI安全趋势分析" --theme apple --open
python "SKILL_DIR/tools/pipeline_ppt.py" "竞品对比" --pages 10 --sources claude-code-leak,rag-tech --open
python "SKILL_DIR/tools/pipeline_ppt.py" "项目总结汇报" --theme warm --open
```

### 第四步：展示结果

告诉用户：
- PPT 已生成并在浏览器中打开
- 可用键盘 ← → 翻页，F 全屏，Home/End 首尾页
- 支持 5 种主题风格切换（页面右上角圆点选择器）
- 所有内容来自 Wiki 知识库，每页标注来源

### 第五步：Python 失败时的回退

如果 Python 脚本失败，手动生成：
1. 读取 `SKILL_DIR/wiki/index.md` 识别相关页面
2. 读取这些页面
3. 基于内容构建幻灯片结构（JSON 数组）
4. 将结构嵌入到 HTML 模板中输出
