查询 LLM 维基并综合答案。

使用方法：/pipeline-query $ARGUMENTS

$ARGUMENTS 是要回答的问题，例如：`所有来源中的主要主题是什么？`

遵循 CLAUDE.md 中定义的查询工作流程：
1. 阅读 wiki/index.md 以识别最相关的页面
2. 阅读这些页面（最多约 10 个最相关的）
3. 综合一个详尽的 markdown 答案，使用 [[页面名称]] 维基链接引用
4. 在末尾包含 ## 来源 部分，列出参考的页面
5. 询问用户是否要将答案保存为 wiki/syntheses/<slug>.md

如果维基为空，请说明并建议先运行 /pipeline-ingest。
