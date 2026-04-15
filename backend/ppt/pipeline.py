"""
PPT generation pipeline orchestrator.

Coordinates the full flow: wiki retrieval → outline planning → slide generation → export.
This is the main entry point for the LivePPT backend.

Uses the project's core.llm_config for LLM configuration.
"""

import json
import traceback
from pathlib import Path
from typing import Dict, List, Optional, Any, Generator

from core.llm_config import LLMConfig, check_llm_config
from backend.ppt.models import Slide, OutlineItem, TemplateStyle, Presentation
from backend.ppt.agents import PlannerAgent, GeneratorAgent, EditorAgent, CommandInterpreterAgent
from backend.ppt.wiki_context import WikiContextProvider
from backend.ppt.template_analyzer import TemplateAnalyzer


class PPTPipeline:
    """
    Orchestrates the full PPT generation pipeline.

    Architecture (inspired by PPTAgent):
      Phase 1 (Planner): knowledge → outline
      Phase 2 (Generator): outline + knowledge → slides (streaming)
      Edit: single slide + instruction → updated slide

    Integration:
      - Config: core.llm_config.LLMConfig (project-wide .llm_config.json)
      - Wiki: wiki/ directory (Markdown knowledge base)
      - Templates: uploaded .pptx files
    """

    def __init__(self, wiki_dir: Path):
        """
        Args:
            wiki_dir: Path to wiki/ directory
        """
        self.wiki_dir = wiki_dir
        self.wiki_ctx = WikiContextProvider(wiki_dir)
        self.template_analyzer = TemplateAnalyzer()

        # Agents are lazily created (they check config on each call)
        self._planner = None
        self._generator = None
        self._editor = None
        self._command_interpreter = None

    @property
    def planner(self) -> PlannerAgent:
        if self._planner is None:
            self._planner = PlannerAgent()
        return self._planner

    @property
    def generator(self) -> GeneratorAgent:
        if self._generator is None:
            self._generator = GeneratorAgent()
        return self._generator

    @property
    def editor(self) -> EditorAgent:
        if self._editor is None:
            self._editor = EditorAgent()
        return self._editor

    @property
    def command_interpreter(self) -> CommandInterpreterAgent:
        if self._command_interpreter is None:
            self._command_interpreter = CommandInterpreterAgent()
        return self._command_interpreter

    # ═══════════════════════════════════════════════════════════════
    #  Wiki Access (for Flask routes)
    # ═══════════════════════════════════════════════════════════════

    def scan_wiki(self) -> Dict[str, List[Dict]]:
        """Scan wiki pages for the frontend picker."""
        return self.wiki_ctx.scan_pages()

    def read_wiki_pages(self, wiki_ids: List[str]) -> Dict[str, str]:
        """Read raw wiki page contents."""
        result = {}
        for page_id in wiki_ids:
            content = self.wiki_ctx.read_page(page_id)
            if content is not None:
                result[page_id] = content
        return result

    # ═══════════════════════════════════════════════════════════════
    #  Template Analysis
    # ═══════════════════════════════════════════════════════════════

    def analyze_template(self, pptx_path: str) -> TemplateStyle:
        """Analyze an uploaded PPTX template."""
        return self.template_analyzer.analyze(pptx_path)

    # ═══════════════════════════════════════════════════════════════
    #  LLM Config Check
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def check_config() -> bool:
        """Check if LLM is configured."""
        return check_llm_config() is not None

    @staticmethod
    def get_config_info() -> Dict[str, str]:
        """Get current config info (for display, hides API key)."""
        cfg = LLMConfig()
        if not cfg.is_configured():
            return {"status": "not_configured"}
        return {
            "status": "configured",
            "model": cfg.config.get("model", "unknown"),
            "base_url": cfg.config.get("base_url", "unknown"),
        }

    # ═══════════════════════════════════════════════════════════════
    #  Core Pipeline: Generate
    # ═══════════════════════════════════════════════════════════════

    def generate(
        self,
        wiki_ids: List[str],
        instruction: str,
        template_style: Optional[TemplateStyle] = None,
        should_stop=None,
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Main generation pipeline. Yields SSE event dicts.

        Events:
          {"type": "outline", "total": N, "slides": [...]}
          {"type": "outline_skip", "message": "..."}
          {"type": "token", "text": "..."}
          {"type": "slide", "index": N, "slide": {...}}
          {"type": "done", "total": N}
          {"type": "error", "message": "..."}

        Args:
            wiki_ids: List of "category/slug" wiki page identifiers
            instruction: User's natural language instruction
            template_style: Optional extracted template style
        """
        try:
            # ── Step 1: Gather wiki content ──
            wiki_contents, wiki_titles = self.wiki_ctx.gather(wiki_ids)
            knowledge_text = self.wiki_ctx.build_knowledge_text(wiki_contents)

            print(f"▶ PPT Pipeline starting")
            print(f"  Wiki: {len(wiki_contents)} articles, Instruction: {instruction[:50]}")

            template_text = template_style.to_prompt_text() if template_style else ""

            # ── Step 2: Outline Planning (sync) ──
            outline = None
            api_overloaded = False
            try:
                outline = self.planner.plan(knowledge_text, instruction)
                yield {
                    "type": "outline",
                    "total": len(outline),
                    "slides": [o.to_dict() for o in outline],
                }
            except Exception as e:
                err_msg = str(e)
                # Detect API overload — no point trying generation immediately
                if "529" in err_msg or "过载" in err_msg or "overload" in err_msg.lower():
                    api_overloaded = True
                print(f"  ⚠ Outline failed: {e}, falling back to direct generation")
                yield {"type": "outline_skip", "message": err_msg}

            # If API is overloaded, don't waste time retrying generation
            if api_overloaded:
                yield {"type": "error", "message": "LLM API 服务过载 (529)，MiniMax 集群负载较高，请等待几分钟后重试，或在设置中更换 API"}
                return

            # ── Step 3: Slide Generation (streaming) ──
            for event in self.generator.generate_streaming(
                outline=outline,
                knowledge_text=knowledge_text,
                instruction=instruction,
                wiki_titles=wiki_titles,
                template_style_text=template_text,
            ):
                if callable(should_stop) and should_stop():
                    yield {"type": "stopped", "message": "用户已停止生成"}
                    return
                yield event

        except Exception as e:
            print(f"✗ Pipeline error: {e}")
            traceback.print_exc()
            yield {"type": "error", "message": str(e)}

    def continue_generation(
        self,
        wiki_ids: List[str],
        original_instruction: str,
        continue_instruction: str,
        existing_slides: List[Dict[str, Any]],
        template_style: Optional[TemplateStyle] = None,
    ) -> Generator[Dict[str, Any], None, None]:
        """Continue an interrupted deck by generating only the missing tail slides."""
        try:
            wiki_contents, wiki_titles = self.wiki_ctx.gather(wiki_ids)
            knowledge_text = self.wiki_ctx.build_knowledge_text(wiki_contents)
            template_text = template_style.to_prompt_text() if template_style else ""

            for event in self.generator.continue_streaming(
                existing_slides=existing_slides,
                knowledge_text=knowledge_text,
                original_instruction=original_instruction,
                continue_instruction=continue_instruction,
                wiki_titles=wiki_titles,
                template_style_text=template_text,
            ):
                yield event
        except Exception as e:
            print(f"✗ Continue error: {e}")
            traceback.print_exc()
            yield {"type": "error", "message": str(e)}

    # ═══════════════════════════════════════════════════════════════
    #  Edit
    # ═══════════════════════════════════════════════════════════════

    def edit_slide(
        self,
        slide_dict: Dict[str, Any],
        instruction: str,
        page_index: int,
        context: str = "",
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Edit a single slide. Yields SSE event dicts.

        Events:
          {"type": "slide", "index": N, "slide": {...}}
          {"type": "error", "message": "..."}
        """
        try:
            new_slide = self.editor.edit(slide_dict, instruction, page_index, context)
            if new_slide:
                yield {
                    "type": "slide",
                    "index": page_index,
                    "slide": new_slide,
                }
            else:
                yield {
                    "type": "error",
                    "message": "编辑失败：无法解析 LLM 输出",
                }
        except Exception as e:
            print(f"✗ Edit error: {e}")
            traceback.print_exc()
            yield {"type": "error", "message": str(e)}

    def interpret_command(
        self,
        instruction: str,
        slides: List[Dict[str, Any]],
        current_slide_index: int,
        can_continue_generation: bool,
        generation_status: str,
        last_generation_instruction: str = "",
    ) -> Dict[str, Any]:
        """Interpret a textbox command with PPT context into a structured action."""
        return self.command_interpreter.interpret(
            instruction=instruction,
            slides=slides,
            current_slide_index=current_slide_index,
            can_continue_generation=can_continue_generation,
            generation_status=generation_status,
            last_generation_instruction=last_generation_instruction,
        )

    # ═══════════════════════════════════════════════════════════════
    #  Test Connection
    # ═══════════════════════════════════════════════════════════════

    @staticmethod
    def test_llm() -> Dict[str, Any]:
        """Quick LLM connectivity test."""
        cfg = LLMConfig()
        if not cfg.is_configured():
            return {"ok": False, "error": "LLM 未配置"}
        try:
            import requests as http_requests
            url = f"{cfg.config['base_url'].rstrip('/')}/chat/completions"
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {cfg.config['api_key']}",
            }
            payload = {
                "model": cfg.config["model"],
                "messages": [{"role": "user", "content": "说'OK'"}],
                "max_tokens": 10,
            }
            resp = http_requests.post(url, json=payload, headers=headers, timeout=30)
            if resp.ok:
                body = resp.json()
                reply = body.get("choices", [{}])[0].get("message", {}).get("content", "")
                return {"ok": True, "model": cfg.config["model"], "reply": reply}
            else:
                return {"ok": False, "status": resp.status_code, "body": resp.text[:500]}
        except Exception as e:
            return {"ok": False, "error": str(e)}
