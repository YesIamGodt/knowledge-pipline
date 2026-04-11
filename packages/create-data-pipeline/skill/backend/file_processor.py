"""
统一文件处理器 - 支持多种文件格式的文本提取
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


@dataclass
class ProcessedDocument:
    """处理后的文档数据结构"""
    content: str  # 提取的文本内容
    metadata: Dict[str, Any] = field(default_factory=dict)  # 文件元数据
    tables: List[str] = field(default_factory=list)  # 提取的表格（如果有）
    images: List[Dict[str, str]] = field(default_factory=list)  # 提取的图片信息
    errors: List[str] = field(default_factory=list)  # 处理过程中的错误


class FileProcessor:
    """
    统一文件处理器接口

    根据文件扩展名自动选择合适的处理器
    """

    def __init__(self, use_multimodal: bool = True):
        self.use_multimodal = use_multimodal
        from .pdf_processor import PDFProcessor
        from .docx_processor import DocxProcessor
        from .xlsx_processor import XlsxProcessor
        from .image_processor import ImageProcessor
        from .pptx_processor import PptxProcessor
        from .html_processor import HTMLProcessor
        from .video_processor import VideoProcessor

        self.multimodal_processor = None
        if self.use_multimodal:
            # 尝试导入多模态处理器（如果失败，会回退到传统方法）
            try:
                from .multimodal_processor import MultimodalProcessor
                from core.llm_config import LLMConfig

                llm_config = LLMConfig()
                if llm_config.is_configured():
                    self.multimodal_processor = MultimodalProcessor(
                        config={
                            "base_url": llm_config.config.get("base_url"),
                            "model": llm_config.config.get("model"),
                            "api_key": llm_config.config.get("api_key")
                        }
                    )
                    logger.info("多模态处理器初始化成功")
                else:
                    logger.warning("LLM 未配置，将使用传统处理方法")
            except Exception as e:
                logger.warning(f"多模态处理器初始化失败: {e}")

        self.processors = {
            ".pdf": PDFProcessor(),
            ".docx": DocxProcessor(),
            ".doc": DocxProcessor(),  # 通过转换工具支持
            ".xlsx": XlsxProcessor(),
            ".xls": XlsxProcessor(),
            ".jpg": ImageProcessor(),
            ".jpeg": ImageProcessor(),
            ".png": ImageProcessor(),
            ".webp": ImageProcessor(),
            ".pptx": PptxProcessor(),
            ".html": HTMLProcessor(),
            ".htm": HTMLProcessor(),
            # 视频格式
            ".mp4": VideoProcessor(),
            ".avi": VideoProcessor(),
            ".mov": VideoProcessor(),
            ".mkv": VideoProcessor(),
            ".wmv": VideoProcessor(),
            ".flv": VideoProcessor(),
            ".webm": VideoProcessor(),
            ".m4v": VideoProcessor(),
            ".mpg": VideoProcessor(),
            ".mpeg": VideoProcessor(),
            ".3gp": VideoProcessor(),
            ".ts": VideoProcessor(),
        }

    def process(self, file_path: str) -> ProcessedDocument:
        """
        处理文件，自动选择合适的处理器

        Args:
            file_path: 文件路径

        Returns:
            ProcessedDocument 对象
        """
        path = Path(file_path)

        if not path.exists():
            return ProcessedDocument(
                content="",
                errors=[f"文件不存在: {file_path}"]
            )

        # 获取文件扩展名
        ext = path.suffix.lower()

        # 首先尝试多模态大模型处理（如果可用）
        if self._should_use_multimodal(ext, path):
            try:
                needs_multimodal = self.multimodal_processor._needs_multimodal(ext, path)
                if needs_multimodal:
                    logger.info(f"使用多模态大模型处理: {file_path} (类型: {ext})")
                    result = self.multimodal_processor.process_file(file_path)
                    logger.info(f"成功提取 {len(result.content)} 字符")
                    return result
                else:
                    logger.info(f"文件类型不需要多模态处理: {file_path} (类型: {ext})")
            except Exception as e:
                logger.warning(f"多模态处理失败: {e}，将回退到传统方法")

        # 选择传统处理器
        processor = self.processors.get(ext)

        if processor is None:
            # 尝试作为纯文本处理
            return self._process_as_text(path)

        try:
            logger.info(f"使用传统方法处理: {file_path} (类型: {ext})")
            result = processor.process(str(path))
            logger.info(f"成功提取 {len(result.content)} 字符")
            return result
        except Exception as e:
            logger.error(f"处理文件失败 {file_path}: {e}")
            return ProcessedDocument(
                content="",
                metadata={"source": file_path},
                errors=[f"处理失败: {str(e)}"]
            )

    def _process_as_text(self, path: Path) -> ProcessedDocument:
        """作为纯文本文件处理"""
        try:
            # 尝试不同的编码
            content = None
            for encoding in ["utf-8", "gbk", "gb2312", "latin-1"]:
                try:
                    content = path.read_text(encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue

            if content is None:
                raise ValueError("无法确定文件编码")

            return ProcessedDocument(
                content=content,
                metadata={
                    "source": str(path),
                    "encoding": encoding,
                    "type": "text"
                }
            )
        except Exception as e:
            return ProcessedDocument(
                content="",
                errors=[f"文本读取失败: {str(e)}"]
            )

    def _should_use_multimodal(self, ext: str, path: Path) -> bool:
        """根据文件类型和运行配置决定是否启用多模态。"""
        if not self.use_multimodal:
            return False

        if not self.multimodal_processor or not self.multimodal_processor.is_available():
            return False

        # PDF 使用策略控制：fast 关闭多模态，balanced/accurate 启用。
        if ext == ".pdf":
            pdf_strategy = os.getenv("PIPELINE_PDF_STRATEGY", "balanced").lower()
            if pdf_strategy == "fast":
                return False

        return True

    def get_supported_formats(self) -> List[str]:
        """获取支持的文件格式列表"""
        return list(self.processors.keys())
