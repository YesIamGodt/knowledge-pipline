"""
LivePPT Backend Module
"""
__version__ = '2.0.0'

from backend.ppt.pipeline import PPTPipeline
from backend.ppt.exporter import PPTXExporter

__all__ = ['PPTPipeline', 'PPTXExporter']
