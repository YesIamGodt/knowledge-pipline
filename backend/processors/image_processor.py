"""
图片 OCR 处理器 - 使用 PaddleOCR 提取图片中的文本
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图片 OCR 处理器（使用 PaddleOCR）"""

    def __init__(self):
        self.ocr_engine = None
        self.use_ocr = True

    def process(self, file_path: str) -> ProcessedDocument:
        """处理图片文件，提取文本"""
        path = Path(file_path)
        errors = []

        # 提取基本元数据
        metadata = {
            "source": str(path),
            "type": "image",
            "format": path.suffix.lower().replace(".", ""),
        }

        content = ""
        extracted_text = ""

        if self.use_ocr:
            try:
                # 尝试 OCR
                extracted_text = self._ocr_extract_text(str(path))
                if extracted_text:
                    content = extracted_text
                    metadata["extraction_method"] = "ocr"
                    metadata["ocr_engine"] = "paddleocr"
                else:
                    errors.append("OCR 未提取到文本")
            except Exception as e:
                errors.append(f"OCR 提取失败: {str(e)}")

        # 如果 OCR 失败，提供图片描述提示
        if not content:
            content = f"[图片文件: {path.name}]\\n\\n注意：此图片未包含可提取的文本，或 OCR 处理失败。"
            metadata["extraction_method"] = "none"

        return ProcessedDocument(
            content=content,
            metadata=metadata,
            errors=errors
        )

    def _ocr_extract_text(self, image_path: str) -> str:
        """使用 PaddleOCR 提取图片文本"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            logger.error("缺少依赖: paddleocr。请运行: pip install paddleocr")
            raise ImportError("paddleocr 未安装")

        try:
            # 初始化 OCR 引擎（延迟初始化）
            if self.ocr_engine is None:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,  # 使用方向分类器
                    lang='ch',  # 中英文混合
                    show_log=False,
                )

            # 执行 OCR
            result = self.ocr_engine.ocr(image_path, cls=True)

            if not result or not result[0]:
                return ""

            # 提取文本并按行组织
            text_lines = []
            for line in result[0]:
                if line and len(line) > 0:
                    text_line = line[0]  # (text, box)
                    if text_line:
                        text_lines.append(text_line[0])

            return "\\n".join(text_lines)

        except Exception as e:
            logger.error(f"PaddleOCR 处理失败: {e}")
            raise

    def set_ocr_engine(self, engine_name: str):
        """设置 OCR 引擎类型"""
        # 预留接口，支持多种 OCR 引擎
        pass
"""
图片 OCR 处理器 - 使用 PaddleOCR 提取图片中的文本
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class ImageProcessor:
    """图片 OCR 处理器（使用 PaddleOCR）"""

    def __init__(self):
        self.ocr_engine = None
        self.use_ocr = True

    def process(self, file_path: str) -> ProcessedDocument:
        """处理图片文件，提取文本"""
        path = Path(file_path)
        errors = []

        # 提取基本元数据
        metadata = {
            "source": str(path),
            "type": "image",
            "format": path.suffix.lower().replace(".", ""),
        }

        content = ""
        extracted_text = ""

        if self.use_ocr:
            try:
                # 尝试 OCR
                extracted_text = self._ocr_extract_text(str(path))
                if extracted_text:
                    content = extracted_text
                    metadata["extraction_method"] = "ocr"
                    metadata["ocr_engine"] = "paddleocr"
                else:
                    errors.append("OCR 未提取到文本")
            except Exception as e:
                errors.append(f"OCR 提取失败: {str(e)}")

        # 如果 OCR 失败，提供图片描述提示
        if not content:
            content = f"[图片文件: {path.name}]\\n\\n注意：此图片未包含可提取的文本，或 OCR 处理失败。"
            metadata["extraction_method"] = "none"

        return ProcessedDocument(
            content=content,
            metadata=metadata,
            errors=errors
        )

    def _ocr_extract_text(self, image_path: str) -> str:
        """使用 PaddleOCR 提取图片文本"""
        try:
            from paddleocr import PaddleOCR
        except ImportError:
            logger.error("缺少依赖: paddleocr。请运行: pip install paddleocr")
            raise ImportError("paddleocr 未安装")

        try:
            # 初始化 OCR 引擎（延迟初始化）
            if self.ocr_engine is None:
                self.ocr_engine = PaddleOCR(
                    use_angle_cls=True,  # 使用方向分类器
                    lang='ch',  # 中英文混合
                    show_log=False,
                )

            # 执行 OCR
            result = self.ocr_engine.ocr(image_path, cls=True)

            if not result or not result[0]:
                return ""

            # 提取文本并按行组织
            text_lines = []
            for line in result[0]:
                if line and len(line) > 0:
                    text_line = line[0]  # (text, box)
                    if text_line:
                        text_lines.append(text_line[0])

            return "\\n".join(text_lines)

        except Exception as e:
            logger.error(f"PaddleOCR 处理失败: {e}")
            raise

    def set_ocr_engine(self, engine_name: str):
        """设置 OCR 引擎类型"""
        # 预留接口，支持多种 OCR 引擎
        pass
