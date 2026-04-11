检查知识维基的健康状况。

使用方法：/pipline-lint

**技能目录定位**：
- 首先检查 `~/.agents/skills/knowledge-pipline/`
- 然后检查 `~/.claude/skills/knowledge-pipline/`
- 最后检查当前项目目录

**执行方式**：
```bash
python <skill-dir>/tools/pipeline_lint.py
```

遵循检查工作流程：

结构检查（使用 Grep 和 Glob 工具）：
1. 孤立页面 — 没有其他页面的入链 [[wikilinks]] 的维基页面
2. 损坏的链接 — 指向不存在页面的 [[维基链接]]
3. 缺失的实体页面 — 在 3+ 个页面中被引用但没有自己页面的名称

语义检查（阅读并推理页面内容）：
4. 矛盾 — 页面之间冲突的主张
5. 过时的摘要 — 在新来源改变了情况后未更新的页面
6. 数据空白 — 维基无法回答的重要问题；建议找到的具体来源

输出结构化的 markdown 检查报告。最后，询问用户是否要将其保存到 wiki/lint-report.md。

追加到 wiki/log.md：## [今天的日期] lint | 维基健康检查
