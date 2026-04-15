"""
LivePPT Backend Module
"""
__version__ = '2.0.0'

from backend.ppt.pipeline import PPTPipeline
from backend.ppt.exporter import PPTXExporter
from backend.ppt.clone_inducter import TemplateInducter, TemplateSpec
from backend.ppt.clone_generator import CloneGenerator, clone_generate_pptx

__all__ = ['PPTPipeline', 'PPTXExporter', 'TemplateInducter', 'TemplateSpec', 'CloneGenerator', 'clone_generate_pptx']
