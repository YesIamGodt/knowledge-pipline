将源文档摄入到知识维基中。

使用方法：/pipeline-ingest $ARGUMENTS

$ARGUMENTS 是文件的**绝对路径**，例如：`D:\docs\my-paper.pdf`

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/. agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**后续所有操作中的 wiki/、tools/、core/、backend/ 都指 SKILL_DIR 下的子目录。**

### 第二步：检查 LLM 配置

读取 `SKILL_DIR/.llm_config.json`。
- 如果不存在 → 提示用户先运行 `/pipeline-config`，然后停止。
- 如果存在 → 继续。

### 第三步：执行摄入

在终端运行（将 SKILL_DIR 替换为实际绝对路径）：
```
python "SKILL_DIR/tools/pipeline_ingest.py" "$ARGUMENTS"
```

支持格式：PDF、图片、视频、Word、Excel、PPT、HTML、Markdown。

可选环境变量 `PIPELINE_PDF_STRATEGY`：`balanced`（默认）、`accurate`、`fast`。

### 第四步：Python 失败时的回退

手动在 SKILL_DIR/wiki/ 下操作：
1. 读取 $ARGUMENTS 文件内容
2. 读取 `SKILL_DIR/wiki/index.md` 和 `SKILL_DIR/wiki/overview.md`
3. 在 `SKILL_DIR/wiki/sources/` 下创建源页面
4. 更新 index.md、overview.md
5. 更新/创建 entities/ 和 concepts/ 下的页面
6. 追加 `SKILL_DIR/wiki/log.md`

### 第五步：输出摘要

完成后告诉用户：添加了什么、创建或更新了哪些页面、发现的矛盾。
