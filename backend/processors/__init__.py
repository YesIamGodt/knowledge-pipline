"""
LLM Wiki Agent - File Processors Package

支持从多种文件格式提取文本内容：
- PDF (pypdf)
- Word DOCX (python-docx)
- Excel XLSX (openpyxl)
- 图片 OCR (PaddleOCR)
- PowerPoint PPTX (python-pptx)
- HTML (BeautifulSoup)
- 视频 (OpenCV 关键帧提取 + 多模态LLM)
- 纯文本文件
"""

from .file_processor import FileProcessor, ProcessedDocument
from .pdf_processor import PDFProcessor
from .docx_processor import DocxProcessor
from .xlsx_processor import XlsxProcessor
from .image_processor import ImageProcessor
from .pptx_processor import PptxProcessor
from .html_processor import HTMLProcessor
from .video_processor import VideoProcessor

__all__ = [
    "FileProcessor",
    "ProcessedDocument",
    "PDFProcessor",
    "DocxProcessor",
    "XlsxProcessor",
    "ImageProcessor",
    "PptxProcessor",
    "HTMLProcessor",
    "VideoProcessor",
]
