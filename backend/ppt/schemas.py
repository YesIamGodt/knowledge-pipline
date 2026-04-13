"""
API request/response schemas for LivePPT v2.

Pydantic models for validating API endpoints.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class GenerateRequest(BaseModel):
    wiki_ids: List[str]
    instruction: str
    template_path: Optional[str] = None


class GenerateResponse(BaseModel):
    job_id: str
    status: str


class PauseRequest(BaseModel):
    job_id: str


class ResumeRequest(BaseModel):
    job_id: str
    user_edits: Dict[int, Dict[str, Any]] = Field(default_factory=dict)


class ExportRequest(BaseModel):
    slides: List[Dict[str, Any]]
    title: str = "Presentation"


class TemplateAnalyzeRequest(BaseModel):
    file_path: str


class TemplateAnalyzeResponse(BaseModel):
    layouts: List[Dict[str, Any]]
    total_slides: int
