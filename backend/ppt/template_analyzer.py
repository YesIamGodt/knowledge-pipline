"""
PPTX template analyzer for LivePPT pipeline.

Extracts style information (colors, fonts, layouts) from uploaded .pptx files
to use as generation constraints. Inspired by PPTAgent's induction phase.
"""

import re
import zipfile
from pathlib import Path
from typing import Optional
from xml.etree import ElementTree as ET

from backend.ppt.models import TemplateStyle


class TemplateAnalyzer:
    """Analyzes PPTX templates to extract visual style constraints."""

    # XML namespaces used in PPTX
    NS = {
        "a": "http://schemas.openxmlformats.org/drawingml/2006/main",
        "r": "http://schemas.openxmlformats.org/officeDocument/2006/relationships",
        "p": "http://schemas.openxmlformats.org/presentationml/2006/main",
    }

    def analyze(self, pptx_path: str) -> TemplateStyle:
        """
        Analyze a .pptx file and extract style information.

        Args:
            pptx_path: Path to the PPTX file

        Returns:
            TemplateStyle with colors, fonts, layouts, description
        """
        style = TemplateStyle(filename=Path(pptx_path).name)

        try:
            with zipfile.ZipFile(pptx_path, "r") as z:
                # Extract theme colors
                style.colors = self._extract_theme_colors(z)

                # Extract fonts
                style.fonts = self._extract_fonts(z)

                # Extract slide layout names
                style.slide_layouts = self._extract_layouts(z)

        except (zipfile.BadZipFile, KeyError, ET.ParseError) as e:
            style.description = f"模板解析部分失败: {e}"

        # Build description
        style.description = self._build_description(style)

        return style

    def _extract_theme_colors(self, z: zipfile.ZipFile) -> list:
        """Extract theme colors from ppt/theme/theme1.xml."""
        colors = []
        theme_files = [n for n in z.namelist() if "theme" in n and n.endswith(".xml")]

        for tf in theme_files[:1]:
            try:
                root = ET.fromstring(z.read(tf))
                # Look for color scheme elements
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag in (
                        "dk1", "dk2", "lt1", "lt2",
                        "accent1", "accent2", "accent3", "accent4",
                        "accent5", "accent6", "hlink", "folHlink",
                    ):
                        for child in elem:
                            val = child.get("val") or child.get("lastClr")
                            if val and len(val) == 6:
                                color = f"#{val}"
                                if color not in colors:
                                    colors.append(color)
            except (ET.ParseError, KeyError):
                pass

        return colors

    def _extract_fonts(self, z: zipfile.ZipFile) -> list:
        """Extract font names from theme."""
        fonts = []
        theme_files = [n for n in z.namelist() if "theme" in n and n.endswith(".xml")]

        for tf in theme_files[:1]:
            try:
                root = ET.fromstring(z.read(tf))
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1] if "}" in elem.tag else elem.tag
                    if tag in ("latin", "ea", "cs"):
                        typeface = elem.get("typeface")
                        if typeface and typeface not in fonts:
                            fonts.append(typeface)
            except (ET.ParseError, KeyError):
                pass

        return fonts

    def _extract_layouts(self, z: zipfile.ZipFile) -> list:
        """Extract slide layout names."""
        layouts = []
        layout_files = sorted(
            n for n in z.namelist()
            if n.startswith("ppt/slideLayouts/") and n.endswith(".xml")
        )

        for lf in layout_files[:10]:
            try:
                root = ET.fromstring(z.read(lf))
                # Try to get layout name from cSld element
                for csld in root.iter(f"{{{self.NS['p']}}}cSld"):
                    name = csld.get("name")
                    if name:
                        layouts.append(name)
                        break
                else:
                    # Fallback: use filename
                    idx = re.search(r"(\d+)", lf)
                    if idx:
                        layouts.append(f"Layout {idx.group(1)}")
            except (ET.ParseError, KeyError):
                pass

        return layouts

    def _build_description(self, style: TemplateStyle) -> str:
        """Build human-readable style description."""
        parts = []
        if style.colors:
            parts.append(f"主题色 {len(style.colors)} 种: {', '.join(style.colors[:4])}")
        if style.fonts:
            parts.append(f"字体: {', '.join(style.fonts[:3])}")
        if style.slide_layouts:
            parts.append(f"布局: {', '.join(style.slide_layouts[:5])}")
        return " | ".join(parts) if parts else "无法提取样式信息"
