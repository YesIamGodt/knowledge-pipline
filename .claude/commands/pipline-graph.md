构建知识维基图谱。

使用方法：/pipline-graph

**技能目录定位**：
- 首先检查 `~/.agents/skills/knowledge-pipline/`
- 然后检查 `~/.claude/skills/knowledge-pipline/`
- 最后检查当前项目目录

首先尝试从配置中读取 Python 路径：

**第一步：检查 Python 路径配置**

1. **检查配置文件**：首先检查项目根目录下的 `.claude_settings.json` 是否有 `python_path` 配置
2. **验证 Python 路径**：如果配置了路径，测试它是否可用
3. **如果没有配置或路径无效**：提示用户运行 `/pipline-config` 配置 Python 路径

**第二步：尝试运行 graph 工具**

如果找到了可用的 Python：
```bash
# 假设已从配置中获取到 PYTHON_CMD
$PYTHON_CMD <skill-dir>/tools/build_graph.py --open
```

**第三步：备选方案**

如果仍然无法运行 Python 工具，使用 Claude Code 手动构建图谱：
1. 读取所有维基页面
2. 识别所有 `[[wikilink]]`
3. 构建节点和边列表
4. 直接生成 `graph/graph.json` 和 `graph/graph.html`

构建后，提供摘要：节点计数、边计数、按类型分类、最连接的节点（中心节点）。

追加到 wiki/log.md：## [今天的日期] graph | 知识图谱已重建

如果失败（缺少依赖），则手动构建图谱：

1. 使用 Grep 在 wiki/ 中的每个文件中查找所有 [[wikilinks]]
2. 构建节点列表：每个维基页面一个节点，id=相对路径，label=标题，type 来自 frontmatter
3. 构建边列表：每个 [[wikilink]] 一条边，标记为 EXTRACTED
4. 推断页面之间未被维基链接捕获的额外隐式关系 — 将这些标记为 INFERRED 并附带置信度分数（0.0–1.0）；将低置信度的标记为 AMBIGUOUS
5. 编写 graph/graph.json，包含 {nodes, edges, built: 今天}
6. 编写 graph/graph.html 作为独立的 vis.js 页面（节点按类型着色，边按类型着色，可交互，可搜索）

构建后，提供摘要：节点计数、边计数、按类型分类、最连接的节点（中心节点）。

追加到 wiki/log.md：## [今天的日期] graph | 知识图谱已重建
