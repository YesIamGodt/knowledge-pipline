"""
Data models for LivePPT pipeline.

Defines the core data structures: SlideType, Slide, OutlineItem, TemplateStyle.
Inspired by PPTAgent's Pydantic response models but adapted for our wiki-driven flow.
"""

from enum import Enum
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
from datetime import datetime


class SlideType(str, Enum):
    """Supported slide layout types."""
    TITLE = "title"
    BULLETS = "bullets"
    COMPARISON = "comparison"
    METRIC = "metric"
    QUOTE = "quote"
    TIMELINE = "timeline"
    FLOWCHART = "flowchart"


class GenerationStatus(str, Enum):
    """Generation task status."""
    IDLE = "idle"
    GENERATING = "generating"
    PAUSED = "paused"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class OutlineItem:
    """A single item in the presentation outline (Phase 1 output)."""
    idx: int
    type: str  # SlideType value
    topic: str

    def to_dict(self) -> Dict[str, Any]:
        return {"idx": self.idx, "type": self.type, "topic": self.topic}

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "OutlineItem":
        return OutlineItem(
            idx=data.get("idx", 0),
            type=data.get("type", "bullets"),
            topic=data.get("topic", ""),
        )


@dataclass
class Slide:
    """
    A single slide in a presentation.
    Union type: different fields are used depending on `type`.
    """
    type: str
    badge: str = ""
    title: str = ""
    subtitle: str = ""
    source: str = ""
    # bullets
    items: List[str] = field(default_factory=list)
    # comparison
    left: Optional[Dict[str, str]] = None
    right: Optional[Dict[str, str]] = None
    # metric
    number: str = ""
    label: str = ""
    # quote
    quote: str = ""
    attribution: str = ""
    # timeline
    events: List[Dict[str, str]] = field(default_factory=list)
    # flowchart
    steps: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dict, omitting empty optional fields."""
        result = {"type": self.type}
        if self.badge:
            result["badge"] = self.badge
        if self.source:
            result["source"] = self.source

        if self.type == SlideType.TITLE:
            result["title"] = self.title
            result["subtitle"] = self.subtitle
        elif self.type == SlideType.BULLETS:
            result["title"] = self.title
            result["items"] = self.items
        elif self.type == SlideType.COMPARISON:
            result["title"] = self.title
            result["left"] = self.left or {"label": "", "desc": ""}
            result["right"] = self.right or {"label": "", "desc": ""}
        elif self.type == SlideType.METRIC:
            result["number"] = self.number
            result["label"] = self.label
            result["items"] = self.items
        elif self.type == SlideType.QUOTE:
            result["quote"] = self.quote
            result["attribution"] = self.attribution
        elif self.type == SlideType.TIMELINE:
            result["title"] = self.title
            result["events"] = self.events
        elif self.type == SlideType.FLOWCHART:
            result["title"] = self.title
            result["steps"] = self.steps
        return result

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Slide":
        """Create Slide from raw JSON dict (LLM output)."""
        return Slide(
            type=data.get("type", "bullets"),
            badge=data.get("badge", ""),
            title=data.get("title", ""),
            subtitle=data.get("subtitle", ""),
            source=data.get("source", ""),
            items=data.get("items", []),
            left=data.get("left"),
            right=data.get("right"),
            number=data.get("number", ""),
            label=data.get("label", ""),
            quote=data.get("quote", ""),
            attribution=data.get("attribution", ""),
            events=data.get("events", []),
            steps=data.get("steps", []),
        )

    def validate(self) -> List[str]:
        """Validate slide content, return list of issues."""
        issues = []
        if self.type not in [e.value for e in SlideType]:
            issues.append(f"Unknown slide type: {self.type}")
        if self.type == SlideType.BULLETS and not self.items:
            issues.append("Bullets slide has no items")
        if self.type == SlideType.COMPARISON and (not self.left or not self.right):
            issues.append("Comparison slide missing left or right")
        if self.type == SlideType.TIMELINE and not self.events:
            issues.append("Timeline slide has no events")
        if self.type == SlideType.FLOWCHART and not self.steps:
            issues.append("Flowchart slide has no steps")
        return issues


@dataclass
class TemplateStyle:
    """Style information extracted from a PPTX template."""
    filename: str = ""
    colors: List[str] = field(default_factory=list)
    fonts: List[str] = field(default_factory=list)
    slide_layouts: List[str] = field(default_factory=list)
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def to_prompt_text(self) -> str:
        """Convert to a text description for LLM prompt injection."""
        parts = []
        if self.colors:
            parts.append(f"主题色: {', '.join(self.colors[:6])}")
        if self.fonts:
            parts.append(f"字体: {', '.join(self.fonts[:4])}")
        if self.slide_layouts:
            parts.append(f"布局: {', '.join(self.slide_layouts[:5])}")
        return " | ".join(parts) if parts else ""


@dataclass
class Presentation:
    """A complete presentation with slides and metadata."""
    slides: List[Slide] = field(default_factory=list)
    outline: Optional[List[OutlineItem]] = None
    title: str = ""
    instruction: str = ""
    template_style: Optional[TemplateStyle] = None
    wiki_sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "instruction": self.instruction,
            "slides": [s.to_dict() for s in self.slides],
            "outline": [o.to_dict() for o in self.outline] if self.outline else None,
            "wiki_sources": self.wiki_sources,
        }


# ========== LivePPT v2: Canvas-Based Interactive Models ==========


@dataclass
class LayoutElement:
    """布局元素"""
    type: str  # 'title', 'subtitle', 'text', 'image', 'shape'
    x: float  # 相对位置 (0-1)
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    align: str = 'left'  # 'left', 'center', 'right'

    def __post_init__(self):
        """Validate coordinates are within valid range."""
        if not 0 <= self.x <= 1:
            raise ValueError(f"x must be between 0 and 1, got {self.x}")
        if not 0 <= self.y <= 1:
            raise ValueError(f"y must be between 0 and 1, got {self.y}")


@dataclass
class SlideLayout:
    """幻灯片布局模式（从模板归纳）"""
    name: str
    description: str
    elements: List[LayoutElement]
    sample_slide_index: int  # 来自模板的第几页


@dataclass
class FabricObject:
    """Fabric.js 对象表示"""
    type: str  # 'text', 'image', 'shape', 'group'
    x: float
    y: float
    width: Optional[float] = None
    height: Optional[float] = None
    rotation: float = 0
    # 文字特有
    text: Optional[str] = None
    fontSize: Optional[int] = None
    fontFamily: Optional[str] = None
    fill: Optional[str] = None
    # 图片特有
    src: Optional[str] = None
    # 其他属性
    props: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GenerationState:
    """生成任务状态"""
    job_id: str
    status: GenerationStatus  # 'idle', 'generating', 'paused', 'completed', 'error'
    slides: List[Dict[str, Any]] = field(default_factory=list)  # Fabric JSON 格式的幻灯片列表
    current_index: int = 0
    wiki_ids: List[str] = field(default_factory=list)
    instruction: str = ""
    template_layouts: List[SlideLayout] = field(default_factory=list)
    user_edits: Dict[int, Dict[str, Any]] = field(default_factory=dict)  # slide_index -> fabric_json
    context_stack: List[Dict[str, Any]] = field(default_factory=list)  # LLM 上下文
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    def touch(self):
        """Update the updated_at timestamp"""
        self.updated_at = datetime.now()
