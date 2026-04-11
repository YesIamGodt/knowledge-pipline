# LLM Wiki Agent - Demo Application

这是一个完整的演示应用，展示了LLM Wiki Agent的核心功能：从文档摄入到知识图谱，再到智能问答，形成持续的知识循环。

## 功能特性

1. **文档摄入** - 上传文档（Markdown, TXT, PDF），自动提取知识
2. **知识探索** - 浏览wiki中的来源、实体、概念和综合页面
3. **智能问答** - 基于知识图谱回答问题
4. **知识图谱** - 可视化展示知识节点和关系
5. **持续循环** - 问答回案可以保存为新的wiki页面，丰富知识库

## 设计风格

本演示应用严格遵循Apple设计系统，提供：
- 简洁优雅的黑白配色
- SF Pro字体风格
- 流畅的交互动画
- 响应式布局，支持各种设备

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置LLM

在首次运行前，你需要配置LLM API。支持OpenAI兼容的API：

- **OpenAI**: https://api.openai.com/v1
- **DeepSeek**: https://api.deepseek.com/v1
- **Ollama** (本地): http://localhost:11434/v1
- **其他OpenAI兼容端点**

### 3. 启动服务器

```bash
cd demo
python app.py
```

服务器将在 `http://localhost:5000` 启动。

### 4. 使用应用

1. **配置LLM** - 首次访问时，在配置页面输入你的API信息
2. **上传文档** - 将文档拖放到上传区域
3. **探索知识** - 浏览自动生成的wiki页面
4. **提问** - 在查询区域输入问题，获取基于知识库的答案
5. **保存答案** - 将有价值的答案保存为wiki页面
6. **查看图谱** - 观察知识网络如何随时间增长

## 工作流程

```
┌─────────────┐
│  上传文档   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  提取知识   │ → 创建wiki页面（来源、实体、概念）
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  构建图谱   │ → 建立节点和关系
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  智能问答   │ → 基于图谱生成答案
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  保存答案   │ → 创建新的wiki页面
└──────┬──────┘
       │
       └──────► 返回图谱，继续循环
```

## 技术架构

### 前端
- **纯HTML/CSS/JavaScript** - 无需前端框架
- **Apple设计系统** - 严格遵循DESIGN.md规范
- **响应式布局** - 移动端友好
- **实时交互** - 无刷新操作

### 后端
- **Flask** - 轻量级Web框架
- **CORS支持** - 跨域请求
- **RESTful API** - 标准化接口
- **Wiki管理** - 完整的CRUD操作

### 数据存储
- **Markdown文件** - 人类可读的wiki页面
- **JSON图谱** - 结构化的知识网络
- **文件系统** - 无需数据库

## API端点

### 配置
- `GET /api/config` - 获取配置状态
- `POST /api/config` - 更新LLM配置

### Wiki操作
- `GET /api/index` - 获取wiki索引
- `GET /api/page/<path>` - 读取wiki页面
- `POST /api/upload` - 上传文件
- `POST /api/ingest` - 摄入文档到wiki

### 查询
- `POST /api/query` - 查询wiki
- `POST /api/synthesis` - 保存问答为wiki页面

### 图谱
- `GET /api/graph` - 获取知识图谱数据

### 统计
- `GET /api/stats` - 获取wiki统计信息

## 目录结构

```
demo/
├── app.py              # Flask应用
├── templates/
│   └── index.html      # 主页面
├── static/
│   ├── css/
│   │   └── style.css   # 样式文件（Apple设计）
│   └── js/
│       └── app.js      # 前端逻辑
└── README.md           # 本文件
```

## 自定义和扩展

### 添加新的LLM提供商

编辑 `core/llm_config.py`，添加新的提供商配置。

### 自定义设计风格

修改 `demo/static/css/style.css`，调整CSS变量。

### 扩展API

在 `demo/app.py` 中添加新的路由和处理函数。

## 生产部署

对于生产环境，建议：

1. 使用专业的WSGI服务器（如Gunicorn）
2. 添加身份验证
3. 启用HTTPS
4. 配置CORS策略
5. 添加日志记录
6. 设置监控和告警

## 故障排除

### 端口被占用
```bash
# 修改app.py中的端口号
app.run(debug=True, host='0.0.0.0', port=5001)
```

### CORS错误
已配置Flask-CORS，如仍有问题，检查浏览器控制台。

### LLM配置失败
确保API密钥正确，网络连接正常。

## 贡献

欢迎提交问题和拉取请求！

## 许可证

与主项目相同

## 联系方式

如有问题，请在主项目仓库提交issue。
