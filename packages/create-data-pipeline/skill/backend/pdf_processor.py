"""
PDF 文件处理器 - 提取 PDF 文档中的文本内容
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class PDFProcessor:
    """PDF 文档处理器"""

    def __init__(self):
        self.extract_images = False  # 是否提取图片

    def process(self, file_path: str) -> ProcessedDocument:
        """
        处理 PDF 文件

        Args:
            file_path: PDF 文件路径

        Returns:
            ProcessedDocument 对象
        """
        try:
            import pypdf
        except ImportError:
            return ProcessedDocument(
                content="",
                errors=["缺少依赖: pypdf。请运行: pip install pypdf"]
            )

        path = Path(file_path)
        errors = []
        content_parts = []
        tables = []
        images = []

        try:
            reader = pypdf.PdfReader(str(path))

            # 提取元数据
            metadata = {
                "source": str(path),
                "type": "pdf",
                "pages": len(reader.pages),
                "encrypted": reader.is_encrypted,
            }

            # 提取基本信息
            if reader.metadata:
                metadata.update({
                    "title": reader.metadata.get("/Title", ""),
                    "author": reader.metadata.get("/Author", ""),
                    "creator": reader.metadata.get("/Creator", ""),
                })

            # 处理加密 PDF
            if reader.is_encrypted:
                try:
                    reader.decrypt("")
                except Exception:
                    errors.append("PDF 文件已加密，无法解密")
                    return ProcessedDocument(
                        content="",
                        metadata=metadata,
                        errors=errors
                    )

            # 提取每一页的文本
            for page_num, page in enumerate(reader.pages):
                try:
                    text = page.extract_text()
                    if text.strip():
                        content_parts.append(f"\\n--- 第 {page_num + 1} 页 ---\\n")
                        content_parts.append(text)
                except Exception as e:
                    errors.append(f"第 {page_num + 1} 页提取失败: {str(e)}")

            # 提取表格（如果有）
            try:
                tables.extend(self._extract_tables(reader))
            except Exception as e:
                errors.append(f"表格提取失败: {str(e)}")

            # 提取图片（如果启用）
            if self.extract_images:
                try:
                    images.extend(self._extract_images(reader, path))
                except Exception as e:
                    errors.append(f"图片提取失败: {str(e)}")

            content = "\\n".join(content_parts)

            return ProcessedDocument(
                content=content,
                metadata=metadata,
                tables=tables,
                images=images,
                errors=errors
            )

        except Exception as e:
            logger.error(f"PDF 处理失败: {e}")
            return ProcessedDocument(
                content="",
                errors=[f"PDF 处理失败: {str(e)}"]
            )

    def _extract_tables(self, reader) -> List[str]:
        """从 PDF 中提取表格（pypdf 不支持表格提取，跳过）"""
        # pypdf 不支持 extract_tables() 方法，表格提取暂不可用
        # 如需表格提取，可使用 PyMuPDF (fitz) 的 page.find_tables() 或 camelot、tabula 库
        return []

    def _extract_images(self, reader, pdf_path: Path) -> List[Dict[str, str]]:
        """从 PDF 中提取图片"""
        images = []

        try:
            for page_num, page in enumerate(reader.pages):
                try:
                    image_list = page.images
                    for img_num, image in enumerate(image_list):
                        try:
                            image_info = page.images[img_num]
                            images.append({
                                "page": page_num + 1,
                                "index": img_num,
                                "name": image_info.name or f"image_{page_num}_{img_num}",
                            })
                        except Exception as e:
                            logger.warning(f"图片 {img_num} 信息获取失败: {e}")
                except Exception as e:
                    logger.warning(f"页面 {page_num + 1} 图片提取失败: {e}")
        except Exception as e:
            logger.warning(f"图片提取失败: {e}")

        return images

    def _table_to_markdown(self, table: List[List[str]]) -> str:
        """将表格数据转换为 Markdown 格式"""
        if not table or not table[0]:
            return ""

        markdown_lines = []

        for row in table:
            if row:
                # 清理单元格内容
                cleaned_row = [cell.strip() if cell else "" for cell in row]
                markdown_lines.append("| " + " | ".join(cleaned_row) + " |")

        if markdown_lines:
            # 添加表头分隔线
            header_cols = len(table[0])
            markdown_lines.insert(1, "|" + "|".join(["---"] * header_cols) + "|")

        return "\\n".join(markdown_lines)
