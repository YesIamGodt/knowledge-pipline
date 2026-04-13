"""
Unit tests for LivePPT v2 data models.
"""

import pytest
from backend.ppt.models import SlideLayout, LayoutElement, FabricObject, GenerationState


def test_slide_layout_creation():
    layout = SlideLayout(
        name='title-center',
        description='标题居中',
        elements=[],
        sample_slide_index=0
    )
    assert layout.name == 'title-center'
    assert len(layout.elements) == 0


def test_layout_element():
    element = LayoutElement(
        type='title',
        x=0.5,
        y=0.3,
        align='center'
    )
    assert element.type == 'title'
    assert element.x == 0.5


def test_fabric_object():
    obj = FabricObject(
        type='text',
        x=100,
        y=200,
        text='Hello',
        fontSize=48
    )
    assert obj.type == 'text'
    assert obj.text == 'Hello'


def test_generation_state():
    state = GenerationState(
        job_id='test-job',
        status='idle',
        slides=[],
        current_index=0,
        wiki_ids=['test'],
        instruction='Test',
        template_layouts=[],
        user_edits={},
        context_stack=[]
    )
    assert state.job_id == 'test-job'
    assert state.status == 'idle'
