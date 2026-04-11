构建知识维基图谱。

使用方法：/pipeline-graph

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

### 第三步：执行图谱构建

在终端运行：
```
python "SKILL_DIR/tools/build_graph.py" --open
```

### 第四步：Python 失败时的回退

手动构建图谱：
1. 用 Grep 在 `SKILL_DIR/wiki/` 中查找所有 `[[wikilinks]]`
2. 构建节点列表：每个维基页面一个节点，id=相对路径，label=标题，type 来自 frontmatter
3. 构建边列表：每个 `[[wikilink]]` 一条边，标记为 EXTRACTED
4. 推断隐式关系 → 标记为 INFERRED 并附带置信度分数（0.0–1.0）
5. 写入 `SKILL_DIR/graph/graph.json`：`{nodes, edges, built: 日期}`
6. 写入 `SKILL_DIR/graph/graph.html`：独立的 vis.js 可视化页面

### 第五步：输出摘要

提供：节点计数、边计数、按类型分类、最连接的节点。
追加到 `SKILL_DIR/wiki/log.md`：`## [YYYY-MM-DD] graph | 知识图谱已重建`
