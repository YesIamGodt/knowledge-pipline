配置 pipline LLM API 相关信息，以及 Python 路径配置。

使用方法：/pipeline-config

---

**第一步：检测当前配置**

Claude Code 会直接检查以下配置文件：
- `.llm_config.json` - LLM API 配置
- `.claude_settings.json` - Claude Code 配置（包含 Python 路径）

---

**第二步：显示配置菜单**

询问用户想配置什么：
- 选项 1：「配置 LLM API」
- 选项 2：「配置 Python 路径」
- 选项 3：「查看当前配置」
- 选项 4：「退出」

---

**分支 A：配置 LLM API**

1. 如果已有配置，显示当前配置（隐藏 API 密钥）
2. 询问是否修改：
   - 问题："检测到已有 LLM 配置，是否需要修改？"
   - 选项：「保留现有配置」、「重新配置」
3. 选择「保留」→ 返回菜单。选择「重新配置」→ 进入向导。

**向导步骤：**

1. **选择提供商**
   - 问题："您使用哪个 LLM 提供商？"
   - 选项：OpenAI、自定义 OpenAI 兼容端点、Ollama（本地）

2. **输入基础 URL**（仅选择"自定义"时）
   - 用户输入，例如：`https://api.deepseek.com/v1`

3. **输入模型名称**
   - 提供默认值：OpenAI → `gpt-4o-mini`，Ollama → `llama3.2`，自定义 → 用户自填

4. **输入 API 密钥**
   - Ollama：跳过（本地无需密钥）
   - 其他：用户输入

5. **确认保存**
   - 显示配置预览（隐藏密钥）
   - 问题："确认保存此配置？"
   - 选项：「确认保存」、「取消」

6. **保存配置**
   - Claude Code 直接写入 `.llm_config.json`，不依赖 Python！

7. **验证配置**
   - 读取并确认写入成功

8. 显示成功消息，返回菜单

---

**分支 B：配置 Python 路径**

1. 首先检查是否已有 `.claude_settings.json` 中的 Python 路径配置
2. 如果有，显示当前配置
3. 询问用户：
   - 问题："检测到已有 Python 路径配置，是否需要修改？"
   - 选项：「保留现有配置」、「重新配置」、「自动检测」

**如果选择「自动检测」或没有配置：**

1. 尝试常见的 Python 路径（按顺序）：
   - `python` (如果可用)
   - `python3` (如果可用)
   - Windows 常见路径：
     - `C:\Users\$USER\AppData\Local\Programs\Python\Python312\python.exe`
     - `C:\Users\$USER\AppData\Local\Programs\Python\Python311\python.exe`
     - `C:\Program Files\Python312\python.exe`
     - `C:\Python312\python.exe`
   - Linux/Mac 常见路径：
     - `/usr/bin/python3`
     - `/usr/local/bin/python3`
     - `/usr/bin/python`

2. 对于每个找到的 Python，测试它是否可用
3. 如果找到多个，让用户选择使用哪个
4. 如果没找到，提示用户手动输入

**手动输入路径：**
- 问题："无法自动找到 Python，请输入 Python 可执行文件的完整路径："
- 示例：`C:\Python312\python.exe` 或 `/usr/bin/python3`

**验证并保存：**
1. 测试输入的路径是否可用
2. 确认后，保存到 `.claude_settings.json`：
   ```json
   {
     "python_path": "C:\\Python312\\python.exe"
   }
   ```
3. 显示成功消息，返回菜单

---

**分支 C：查看当前配置**

显示以下信息：
- LLM API 配置（隐藏 API 密钥）
- Python 路径配置（如果有）
- 配置文件位置

然后返回菜单。

---

**配置文件格式：**

`.llm_config.json` (LLM API 配置):
```json
{
  "base_url": "https://api.openai.com/v1",
  "model": "gpt-4o-mini",
  "api_key": "sk-..."
}
```

`.claude_settings.json` (Claude Code 配置):
```json
{
  "python_path": "C:\\Python312\\python.exe"
}
```

---

**使用配置的 Python：**

其他命令（如 `/pipeline-graph`）需要 Python 时：
1. 首先读取 `.claude_settings.json` 中的 `python_path`
2. 如果有配置，直接使用
3. 如果没有配置，提示用户运行 `/pipeline-config` 配置 Python 路径
