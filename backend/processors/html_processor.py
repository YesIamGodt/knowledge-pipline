"""
HTML 文件处理器 - 提取网页内容
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class HTMLProcessor:
    """HTML 网页处理器"""

    def __init__(self):
        self.use_trafilatura = True  # 是否使用 Trafilatura

    def process(self, file_path: str) -> ProcessedDocument:
        """处理 HTML 文件"""
        path = Path(file_path)
        errors = []

        # 提取基本元数据
        metadata = {
            "source": str(path),
            "type": "html",
        }

        content = ""

        if self.use_trafilatura:
            try:
                content = self._extract_with_trafilatura(str(path))
                metadata["extraction_method"] = "trafilatura"
            except ImportError:
                logger.warning("Trafilatura 未安装，使用 BeautifulSoup")
                content = self._extract_with_beautifulsoup(str(path))
                metadata["extraction_method"] = "beautifulsoup"
            except Exception as e:
                errors.append(f"Trafilatura 提取失败: {str(e)}")
                content = self._extract_with_beautifulsoup(str(path))
                metadata["extraction_method"] = "beautifulsoup"
        else:
            content = self._extract_with_beautifulsoup(str(path))
            metadata["extraction_method"] = "beautifulsoup"

        return ProcessedDocument(
            content=content,
            metadata=metadata,
            errors=errors
        )

    def _extract_with_trafilatura(self, file_path: str) -> str:
        """使用 Trafilatura 提取内容"""
        try:
            import trafilatura
        except ImportError:
            raise ImportError("trafilatura")

        try:
            # 读取 HTML 文件
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 使用 Trafilatura 提取
            content = trafilatura.extract(
                html_content,
                output_format='markdown',
                include_comments=False,
                include_tables=True,
            )

            return content or ""

        except Exception as e:
            logger.error(f"Trafilatura 处理失败: {e}")
            raise

    def _extract_with_beautifulsoup(self, file_path: str) -> str:
        """使用 BeautifulSoup 提取内容"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 提取主要内容
            content_parts = []

            # 提取标题
            title = soup.find('title')
            if title:
                content_parts.append(f"# {title.get_text()}\\n")

            # 提取段落
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    content_parts.append(text)

            # 提取列表
            for ul in soup.find_all(['ul', 'ol']):
                for li in ul.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        content_parts.append(f"- {text}")

            # 提取表格
            for table in soup.find_all('table'):
                markdown_table = self._table_to_markdown(table)
                if markdown_table:
                    content_parts.append(f"\\n{markdown_table}")

            return "\\n\\n".join(content_parts)

        except Exception as e:
            logger.error(f"BeautifulSoup 处理失败: {e}")
            raise

    def _table_to_markdown(self, table) -> str:
        """将 HTML 表格转换为 Markdown"""
        rows = []

        for row in table.find_all('tr'):
            cells = []
            for cell in row.find_all(['td', 'th']):
                text = cell.get_text(strip=True)
                cells.append(text)

            if cells:
                rows.append("| " + " | ".join(cells) + " |")

        if rows:
            # 添加表头分隔线
            max_cols = max(len(row.split('|')) - 2 for row in rows) if rows else 0
            rows.insert(1, "|" + "|".join(["---"] * max_cols) + "|")

        return "\\n".join(rows)
"""
HTML 文件处理器 - 提取网页内容
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from .file_processor import ProcessedDocument

logger = logging.getLogger(__name__)


class HTMLProcessor:
    """HTML 网页处理器"""

    def __init__(self):
        self.use_trafilatura = True  # 是否使用 Trafilatura

    def process(self, file_path: str) -> ProcessedDocument:
        """处理 HTML 文件"""
        path = Path(file_path)
        errors = []

        # 提取基本元数据
        metadata = {
            "source": str(path),
            "type": "html",
        }

        content = ""

        if self.use_trafilatura:
            try:
                content = self._extract_with_trafilatura(str(path))
                metadata["extraction_method"] = "trafilatura"
            except ImportError:
                logger.warning("Trafilatura 未安装，使用 BeautifulSoup")
                content = self._extract_with_beautifulsoup(str(path))
                metadata["extraction_method"] = "beautifulsoup"
            except Exception as e:
                errors.append(f"Trafilatura 提取失败: {str(e)}")
                content = self._extract_with_beautifulsoup(str(path))
                metadata["extraction_method"] = "beautifulsoup"
        else:
            content = self._extract_with_beautifulsoup(str(path))
            metadata["extraction_method"] = "beautifulsoup"

        return ProcessedDocument(
            content=content,
            metadata=metadata,
            errors=errors
        )

    def _extract_with_trafilatura(self, file_path: str) -> str:
        """使用 Trafilatura 提取内容"""
        try:
            import trafilatura
        except ImportError:
            raise ImportError("trafilatura")

        try:
            # 读取 HTML 文件
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()

            # 使用 Trafilatura 提取
            content = trafilatura.extract(
                html_content,
                output_format='markdown',
                include_comments=False,
                include_tables=True,
            )

            return content or ""

        except Exception as e:
            logger.error(f"Trafilatura 处理失败: {e}")
            raise

    def _extract_with_beautifulsoup(self, file_path: str) -> str:
        """使用 BeautifulSoup 提取内容"""
        try:
            from bs4 import BeautifulSoup
        except ImportError:
            raise ImportError("beautifulsoup4")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 提取主要内容
            content_parts = []

            # 提取标题
            title = soup.find('title')
            if title:
                content_parts.append(f"# {title.get_text()}\\n")

            # 提取段落
            for p in soup.find_all('p'):
                text = p.get_text(strip=True)
                if text:
                    content_parts.append(text)

            # 提取列表
            for ul in soup.find_all(['ul', 'ol']):
                for li in ul.find_all('li', recursive=False):
                    text = li.get_text(strip=True)
                    if text:
                        content_parts.append(f"- {text}")

            # 提取表格
            for table in soup.find_all('table'):
                markdown_table = self._table_to_markdown(table)
                if markdown_table:
                    content_parts.append(f"\\n{markdown_table}")

            return "\\n\\n".join(content_parts)

        except Exception as e:
            logger.error(f"BeautifulSoup 处理失败: {e}")
            raise

    def _table_to_markdown(self, table) -> str:
        """将 HTML 表格转换为 Markdown"""
        rows = []

        for row in table.find_all('tr'):
            cells = []
            for cell in row.find_all(['td', 'th']):
                text = cell.get_text(strip=True)
                cells.append(text)

            if cells:
                rows.append("| " + " | ".join(cells) + " |")

        if rows:
            # 添加表头分隔线
            max_cols = max(len(row.split('|')) - 2 for row in rows) if rows else 0
            rows.insert(1, "|" + "|".join(["---"] * max_cols) + "|")

        return "\\n".join(rows)
