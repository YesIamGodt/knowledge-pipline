"""
Wiki context provider for LivePPT pipeline.

Handles wiki page scanning, content retrieval, and compression
for LLM context optimization.
"""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Optional, Any, Tuple


class WikiContextProvider:
    """Provides compressed wiki content for LLM context windows."""

    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir

    def scan_pages(self) -> Dict[str, List[Dict[str, str]]]:
        """
        Scan wiki directory and return categorized page list.

        Returns:
            {"sources": [...], "entities": [...], "concepts": [...], "syntheses": [...]}
        """
        result = {}
        categories = ["sources", "entities", "concepts", "syntheses"]

        for cat in categories:
            cat_dir = self.wiki_dir / cat
            if not cat_dir.is_dir():
                continue

            items = []
            for md in sorted(cat_dir.glob("*.md")):
                raw = md.read_text(encoding="utf-8")
                fm, _ = self._parse_frontmatter(raw)
                title = fm.get("title", md.stem)
                tags = fm.get("tags", [])
                desc = f" [{', '.join(tags)}]" if tags else ""
                items.append({
                    "id": f"{cat}/{md.stem}",
                    "title": title,
                    "description": desc,
                    "filename": md.name,
                })
            if items:
                result[cat] = items

        return result

    def gather(
        self, wiki_ids: List[str], max_chars_per_page: int = 1500
    ) -> Tuple[Dict[str, str], List[str]]:
        """
        Gather and compress wiki content for the given page IDs.

        Args:
            wiki_ids: List of "category/slug" identifiers
            max_chars_per_page: Max chars per compressed page

        Returns:
            (contents_dict, titles_list)
        """
        contents = {}
        titles = []

        for page_id in wiki_ids:
            parts = page_id.split("/", 1)
            if len(parts) != 2:
                continue

            cat, slug = parts
            md_path = self.wiki_dir / cat / f"{slug}.md"
            if not md_path.exists():
                continue

            raw = md_path.read_text(encoding="utf-8")
            fm, _ = self._parse_frontmatter(raw)
            title = fm.get("title", slug)
            titles.append(title)
            contents[page_id] = self.compress(raw, max_chars_per_page)

        return contents, titles

    def build_knowledge_text(self, contents: Dict[str, str]) -> str:
        """Build a combined knowledge text from compressed contents."""
        if not contents:
            return ""
        parts = [f"### {pid}\n{content}" for pid, content in contents.items()]
        return "\n\n".join(parts)

    def compress(self, raw_content: str, max_chars: int = 1500) -> str:
        """
        Compress wiki markdown to fit LLM context by extracting key sections.
        Prioritizes: Summary, Key Claims, Key Quotes, Connections.
        """
        _, body = self._parse_frontmatter(raw_content)

        priority_sections = [
            "Summary", "Key Claims", "Key Quotes", "Connections",
            "摘要", "关键声明", "核心观点", "关键引用",
        ]

        result = ""
        current_section = ""

        for line in body.split("\n"):
            if line.startswith("## "):
                current_section = line[3:].strip()
            elif current_section in priority_sections:
                result += line + "\n"

        # If priority sections didn't yield enough content, take raw body
        if len(result) < 200:
            result = body

        if len(result) > max_chars:
            result = result[:max_chars] + "..."

        return result

    def read_page(self, page_id: str) -> Optional[str]:
        """Read raw content of a single wiki page."""
        parts = page_id.split("/", 1)
        if len(parts) != 2:
            return None
        cat, slug = parts
        md_path = self.wiki_dir / cat / f"{slug}.md"
        if md_path.exists():
            return md_path.read_text(encoding="utf-8")
        return None

    @staticmethod
    def _parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str]:
        """Extract YAML frontmatter and body from markdown content."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                try:
                    fm = yaml.safe_load(parts[1]) or {}
                except yaml.YAMLError:
                    fm = {}
                body = parts[2].strip()
                return fm, body
        return {}, content
