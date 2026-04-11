检查知识维基的健康状况。

使用方法：/pipeline-lint

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/.agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**后续所有操作中的 wiki/ 都指 SKILL_DIR 下的子目录。**

### 第二步：执行检查

在终端运行：
```
python "SKILL_DIR/tools/pipeline_lint.py"
```

### 第三步：Python 失败时的回退

手动检查 `SKILL_DIR/wiki/`：

**结构检查**（使用 Grep 和 Glob）：
1. 孤立页面 — 没有其他页面入链 `[[wikilinks]]` 的维基页面
2. 损坏的链接 — 指向不存在页面的 `[[维基链接]]`
3. 缺失的实体页面 — 在 3+ 个页面中被引用但没有自己页面的名称

**语义检查**（阅读并推理页面内容）：
4. 矛盾 — 页面之间冲突的主张
5. 过时的摘要 — 在新来源改变了情况后未更新的页面
6. 数据空白 — 维基无法回答的重要问题

### 第四步：输出报告

输出结构化的 markdown 检查报告。
询问用户是否要将其保存到 `SKILL_DIR/wiki/lint-report.md`。
追加到 `SKILL_DIR/wiki/log.md`：`## [YYYY-MM-DD] lint | 维基健康检查`
