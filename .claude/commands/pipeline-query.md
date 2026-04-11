查询知识维基并综合答案。

使用方法：/pipeline-query $ARGUMENTS

$ARGUMENTS 是要回答的问题，例如：`所有来源中的主要主题是什么？`

可选标志（追加在问题后面）：
- `--reasoning-chain` 或 `--rc`：展示深度推理链，显示知识节点间的推理路径并生成交互式推理子图可视化

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/.agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**后续所有操作中的 wiki/、tools/ 都指 SKILL_DIR 下的子目录。**

### 第二步：检查 LLM 配置

读取 `SKILL_DIR/.llm_config.json`。
- 如果不存在 → 提示用户先运行 `/pipeline-config`，然后停止。
- 如果存在 → 继续。

### 第三步：执行查询

在终端运行：
```
python "SKILL_DIR/tools/pipeline_query.py" "$ARGUMENTS"
```

如果用户请求推理链、推理路径、深度分析等，自动添加 `--reasoning-chain` 标志：
```
python "SKILL_DIR/tools/pipeline_query.py" "$ARGUMENTS" --reasoning-chain
```

### 第四步：Python 失败时的回退

手动查询：
1. 读取 `SKILL_DIR/wiki/index.md` 识别最相关的页面
2. 读取这些页面（最多约 10 个）
3. 综合详尽的 markdown 答案，使用 `[[页面名称]]` 维基链接引用
4. 在末尾包含 `## 来源` 部分，列出参考的页面
5. 询问用户是否要将答案保存为 `SKILL_DIR/wiki/syntheses/<slug>.md`

如果维基为空，请说明并建议先运行 `/pipeline-ingest`。
