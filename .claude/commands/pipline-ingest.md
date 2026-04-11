将源文档摄入到知识维基中。

使用方法：/pipline-ingest $ARGUMENTS

$ARGUMENTS 应该是 raw/ 目录中的文件路径，例如：`raw/articles/my-article.md`

**使用强大的 Python 脚本来处理：**

1. **首先尝试使用 `tools/pipeline_ingest.py` 执行**：
   - 支持多种文件格式（图片、PDF、DOCX、XLSX、视频等）
   - PDF 默认使用 `balanced` 策略：文本提取 + 多图智能理解
   - 多图 PDF 会执行：图片去重、重要性排序、页内文本上下文融合
   - **视频文件**（.mp4/.avi/.mov/.mkv 等）：关键帧提取 + 多模态 LLM 理解
   - 图片等复杂内容使用多模态增强理解
   - 完整的错误处理和回退机制
   - 专业的元数据提取和处理
   - 与现有维基内容的矛盾检测

**PDF 策略说明**：
- `PIPELINE_PDF_STRATEGY=balanced`（默认）：兼顾速度与准确率。
- `PIPELINE_PDF_STRATEGY=accurate`：偏向准确率，适合图片很多/扫描件较多的 PDF。
- `PIPELINE_PDF_STRATEGY=fast`：只走文本优先解析，速度最快。

**视频处理说明**：
- 使用 OpenCV 进行场景变化检测 + 均匀采样的混合关键帧提取
- 关键帧压缩后分批发送给多模态 LLM 理解画面内容
- 如果有 ffmpeg + whisper，还会提取音频并转写
- 最终由 LLM 综合帧描述和音频生成视频内容总结

2. **如果 Python 脚本失败，则回退到 Claude Code 内置能力**：
   - 直接读取文本
   - 使用 Read 工具处理图片
   - 手动构建页面

**执行命令**：
```bash
# 使用完整的 Python 脚本
python tools/pipeline_ingest.py $ARGUMENTS
```

**详细流程**（由 Python 脚本执行）：
- 读取并处理源文件（支持多模态）
- 分析与现有维基的关系
- 创建源页面和索引
- 更新概览和实体页面
- 记录摄入日志

完成后，提供摘要：添加了什么内容、创建或更新了哪些页面、发现的任何矛盾。
