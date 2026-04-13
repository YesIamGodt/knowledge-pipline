# tests/unit/test_inductor.py
import pytest
import os
from pptx import Presentation
from pptx.util import Inches, Pt
from backend.ppt.inductor import SlideInducter

@pytest.fixture
def sample_template(tmp_path):
    """创建测试用 PPT 模板"""
    prs = Presentation()

    # 幻灯片 1: 标题页
    slide1 = prs.slides.add_slide(prs.slide_layouts[0])
    title = slide1.shapes.title
    title.text = "Title Slide"

    # 幻灯片 2: 双栏文本
    slide2 = prs.slides.add_slide(prs.slide_layouts[5])
    left_box = slide2.shapes.add_textbox(Inches(1), Inches(2), Inches(3), Inches(4))
    left_box.text = "Left Column"
    right_box = slide2.shapes.add_textbox(Inches(5), Inches(2), Inches(3), Inches(4))
    right_box.text = "Right Column"

    # 保存
    template_path = tmp_path / "test_template.pptx"
    prs.save(str(template_path))
    return str(template_path)

def test_analyze_template(sample_template):
    """测试模板分析"""
    inductor = SlideInducter()
    layouts = inductor.analyze(sample_template)

    # 应该提取出至少 1 种布局
    assert len(layouts) >= 1

    # 检查布局属性
    for layout in layouts:
        assert layout.name is not None
        assert layout.description is not None
        assert isinstance(layout.elements, list)

def test_nonexistent_file():
    """测试不存在的文件"""
    inductor = SlideInducter()

    with pytest.raises(FileNotFoundError):
        inductor.analyze('/nonexistent/file.pptx')
