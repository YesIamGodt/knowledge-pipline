"""
Wikilink 解析器 - 跨页面链接的统一规范化解析

解决原有实现的问题：
1. 大小写敏感导致 [[RAG]] ≠ [[Rag]] ≠ [[rag]]
2. 空格/连字符不兼容: [[Transformer Model]] vs TransformerModel.md
3. 中文标题匹配不稳定

提供统一的 normalize → resolve → validate 流程。
"""

import re
from pathlib import Path
from typing import List, Dict, Optional, Set


def normalize_link_name(name: str) -> str:
    """
    将 wikilink 名称规范化为统一的比较键

    规则：
    - 全部转小写
    - 移除空格、连字符、下划线
    - 去掉 .md 后缀（如果有）
    """
    name = name.strip()
    if name.lower().endswith(".md"):
        name = name[:-3]
    return re.sub(r'[\s\-_]+', '', name).lower()


class WikilinkResolver:
    """
    Wikilink 解析器

    缓存 wiki 目录中所有页面的规范化名称，提供快速解析。
    """

    def __init__(self, wiki_dir: Path):
        self.wiki_dir = wiki_dir
        self._pages: Dict[str, Path] = {}          # normalized_name → Path
        self._stem_map: Dict[str, Path] = {}        # stem.lower() → Path
        self._all_pages: List[Path] = []
        self._build_index()

    def _build_index(self):
        """扫描 wiki 目录，构建索引"""
        self._pages.clear()
        self._stem_map.clear()
        self._all_pages.clear()

        skip_names = {"index.md", "log.md", "lint-report.md"}
        for p in self.wiki_dir.rglob("*.md"):
            if p.name in skip_names:
                continue
            self._all_pages.append(p)

            # 精确 stem 映射
            self._stem_map[p.stem.lower()] = p

            # 规范化映射（去空格/连字符）
            norm = normalize_link_name(p.stem)
            self._pages[norm] = p

            # 如果 frontmatter 有 title，也加入映射
            try:
                content = p.read_text(encoding="utf-8")[:500]
                m = re.search(r'^title:\s*"?([^"\n]+)"?', content, re.MULTILINE)
                if m:
                    title_norm = normalize_link_name(m.group(1))
                    if title_norm not in self._pages:
                        self._pages[title_norm] = p
            except Exception:
                pass

    def resolve(self, link_name: str) -> Optional[Path]:
        """
        解析 [[wikilink]] 到文件路径

        尝试顺序：
        1. 精确 stem 匹配（大小写无关）
        2. 规范化名称匹配（去空格/连字符）
        3. 包含匹配（link_name 是某页面名的子串或反之）
        """
        name_lower = link_name.strip().lower()

        # 去 .md 后缀
        if name_lower.endswith(".md"):
            name_lower = name_lower[:-3]

        # 1. 精确 stem 匹配
        if name_lower in self._stem_map:
            return self._stem_map[name_lower]

        # 2. 规范化匹配
        norm = normalize_link_name(link_name)
        if norm in self._pages:
            return self._pages[norm]

        # 3. 包含匹配（双向）
        for key, path in self._pages.items():
            if norm in key or key in norm:
                return path

        return None

    def resolve_all(self, link_name: str) -> List[Path]:
        """解析所有可能的匹配（用于歧义检测）"""
        result = self.resolve(link_name)
        return [result] if result else []

    def exists(self, link_name: str) -> bool:
        """检查 wikilink 是否能解析到存在的页面"""
        return self.resolve(link_name) is not None

    def all_pages(self) -> List[Path]:
        """所有 wiki 页面"""
        return list(self._all_pages)

    def page_id(self, path: Path) -> str:
        """获取页面 ID（相对路径，无 .md 后缀）"""
        return path.relative_to(self.wiki_dir).as_posix().replace(".md", "")

    def find_inbound_links(self, target: Path) -> List[Path]:
        """查找所有指向 target 的入站链接页面"""
        target_stem = target.stem.lower()
        target_norm = normalize_link_name(target.stem)
        inbound = []

        for p in self._all_pages:
            if p == target:
                continue
            try:
                content = p.read_text(encoding="utf-8")
                links = re.findall(r'\[\[([^\]]+)\]\]', content)
                for link in links:
                    if (link.lower().strip() == target_stem or
                            normalize_link_name(link) == target_norm):
                        inbound.append(p)
                        break
            except Exception:
                pass

        return inbound

    def find_orphans(self) -> List[Path]:
        """查找孤立页面（无入站链接）"""
        has_inbound: Set[str] = set()
        overview = self.wiki_dir / "overview.md"

        for p in self._all_pages:
            try:
                content = p.read_text(encoding="utf-8")
                links = re.findall(r'\[\[([^\]]+)\]\]', content)
                for link in links:
                    resolved = self.resolve(link)
                    if resolved:
                        has_inbound.add(str(resolved))
            except Exception:
                pass

        orphans = []
        for p in self._all_pages:
            if str(p) not in has_inbound and p != overview:
                orphans.append(p)
        return orphans

    def find_broken_links(self) -> List[tuple]:
        """查找所有损坏的 wikilink: [(页面路径, link名称), ...]"""
        broken = []
        for p in self._all_pages:
            try:
                content = p.read_text(encoding="utf-8")
                links = re.findall(r'\[\[([^\]]+)\]\]', content)
                for link in links:
                    if not self.exists(link):
                        broken.append((p, link))
            except Exception:
                pass
        return broken

    def refresh(self):
        """重建索引（在页面增删后调用）"""
        self._build_index()
