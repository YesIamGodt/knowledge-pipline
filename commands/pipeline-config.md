配置 Knowledge Pipeline 的 LLM API 信息。

使用方法：/pipeline-config

---

## 执行步骤

### 第一步：确定技能目录 SKILL_DIR

按顺序检查以下目录，取第一个存在的作为 SKILL_DIR：
1. `~/.agents/skills/knowledge-pipline`
2. `~/.claude/skills/knowledge-pipline`

在 Windows 上 `~` 展开为 `C:\Users\{用户名}`。
用终端的 `Test-Path`（PowerShell）或 `test -d`（bash）验证目录存在。

**配置文件存放在 SKILL_DIR 下。**

### 第二步：检测当前配置

读取 `SKILL_DIR/.llm_config.json`（如果存在）。

### 第三步：显示配置菜单

询问用户想做什么：
- 选项 1：「配置 LLM API」
- 选项 2：「查看当前配置」
- 选项 3：「退出」

---

### 分支 A：配置 LLM API

1. 如果已有配置，显示当前值（隐藏 API 密钥）
2. 询问是否修改：「保留现有配置」、「重新配置」

**向导步骤：**

1. **选择提供商**
   - 选项：OpenAI、自定义 OpenAI 兼容端点、Ollama（本地）

2. **输入基础 URL**（仅"自定义"时）
   - 例如：`https://api.deepseek.com/v1`

3. **输入模型名称**
   - 默认：OpenAI → `gpt-4o-mini`，Ollama → `llama3.2`

4. **输入 API 密钥**
   - Ollama 跳过

5. **确认保存**
   - 显示配置预览（隐藏密钥）

6. **保存配置**
   - 直接写入 `SKILL_DIR/.llm_config.json`：
   ```json
   {
     "base_url": "https://api.openai.com/v1",
     "model": "gpt-4o-mini",
     "api_key": "sk-..."
   }
   ```

7. 显示成功消息

---

### 分支 B：查看当前配置

显示：
- LLM API 配置（隐藏 API 密钥）
- 配置文件路径：`SKILL_DIR/.llm_config.json`

然后返回菜单。
