"""
LLM Agent abstractions for LivePPT pipeline.

Wraps the project's core.llm_config system with agent-specific behavior:
- PlannerAgent: outline planning (sync call)
- GeneratorAgent: slide generation (streaming)
- EditorAgent: single-slide editing (streaming)

Uses the project-wide .llm_config.json via core.llm_config.LLMConfig.
"""

import json
import re
import time
import traceback
from typing import Dict, List, Optional, Any, Generator, Tuple

import requests as http_requests

from core.llm_config import LLMConfig, check_llm_config
from backend.ppt.models import Slide, OutlineItem
from backend.ppt.prompts import (
    PLANNER_SYSTEM,
    GENERATOR_SYSTEM,
    EDITOR_SYSTEM,
    COMMAND_INTERPRETER_SYSTEM,
    build_planner_prompt,
    build_continuation_prompt,
    build_generator_prompt,
    build_generator_prompt_no_outline,
    build_editor_prompt,
    build_command_interpreter_prompt,
)


class LLMAgent:
    """
    Base LLM agent wrapping the project's LLMConfig.

    Provides call() for sync requests and call_streaming() for SSE.
    Includes retry logic for 429 and 5xx errors.
    """

    MAX_RETRIES = 3
    TIMEOUT = 60

    def __init__(self, system_prompt: str, role_name: str = "agent"):
        self.system_prompt = system_prompt
        self.role_name = role_name

    @staticmethod
    def _get_config() -> Dict[str, str]:
        """Get raw config dict from project's LLMConfig singleton."""
        llm_cfg = LLMConfig()
        if not llm_cfg.is_configured():
            raise RuntimeError("LLM 未配置，请先运行 /pipeline-config")
        return llm_cfg.config

    def call(
        self,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> str:
        """Synchronous LLM call. Returns response text."""
        config = self._get_config()
        resp = self._call_llm(
            config,
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=False,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        data = resp.json()
        msg = data["choices"][0]["message"]
        # Some reasoning models put content in reasoning_content with empty content
        text = msg.get("content") or ""
        if not text.strip() and msg.get("reasoning_content"):
            text = msg["reasoning_content"]
        return text

    def call_streaming(
        self,
        user_prompt: str,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> http_requests.Response:
        """Streaming LLM call. Returns raw response for iter_lines()."""
        config = self._get_config()
        return self._call_llm(
            config,
            [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            stream=True,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def _call_llm(
        self,
        config: Dict[str, str],
        messages: List[Dict],
        stream: bool = False,
        max_tokens: int = 4096,
        temperature: float = 0.7,
    ) -> http_requests.Response:
        """Low-level LLM call with retry logic for 429/5xx."""
        url = f"{config['base_url'].rstrip('/')}/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config['api_key']}",
        }
        payload = {
            "model": config["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if stream:
            payload["stream"] = True

        resp = None
        for attempt in range(self.MAX_RETRIES):
            try:
                resp = http_requests.post(
                    url, json=payload, headers=headers,
                    stream=stream, timeout=self.TIMEOUT,
                )
                if resp.status_code == 429 or (500 <= resp.status_code < 600):
                    retry_after = resp.headers.get("Retry-After", "")
                    wait = int(retry_after) if retry_after.isdigit() else min(2 ** attempt, 8)
                    print(f"  ⚠ [{self.role_name}] {resp.status_code} (attempt {attempt+1}/{self.MAX_RETRIES}), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                resp.raise_for_status()
                return resp
            except http_requests.exceptions.HTTPError:
                if resp is not None and (resp.status_code == 429 or 500 <= resp.status_code < 600) and attempt < self.MAX_RETRIES - 1:
                    continue
                raise
            except http_requests.exceptions.ReadTimeout:
                if attempt < self.MAX_RETRIES - 1:
                    wait = min(2 ** attempt, 8)
                    print(f"  ⚠ [{self.role_name}] Timeout (attempt {attempt+1}/{self.MAX_RETRIES}), waiting {wait}s...")
                    time.sleep(wait)
                    continue
                raise

        # Extract error details for a more helpful message
        status = resp.status_code if resp else None
        if status == 529:
            raise RuntimeError(
                "LLM API 服务过载 (529)，MiniMax 集群负载较高，请等待几分钟后重试"
            )
        elif status == 429:
            raise RuntimeError(
                "LLM API 速率限制 (429)，请求过于频繁，请稍后重试"
            )
        elif status and 500 <= status < 600:
            raise RuntimeError(
                f"LLM API 服务器错误 ({status})，请稍后重试或更换 API"
            )
        else:
            raise RuntimeError(
                f"LLM API 持续返回 {'超时' if not resp else resp.status_code} 错误，"
                f"请稍后重试或更换 API"
            )


# ═══════════════════════════════════════════════════════════════
#  Specialized Agents
# ═══════════════════════════════════════════════════════════════

class PlannerAgent(LLMAgent):
    """Plans presentation outline structure."""

    MAX_RETRIES = 2   # Fail fast to outline_skip fallback
    TIMEOUT = 30      # 30s max for outline planning

    def __init__(self):
        super().__init__(PLANNER_SYSTEM, role_name="planner")

    def plan(
        self,
        knowledge_text: str,
        instruction: str,
    ) -> List[OutlineItem]:
        """
        Generate presentation outline.

        Returns:
            List of OutlineItem
        Raises:
            RuntimeError if outline parsing fails
        """
        prompt = build_planner_prompt(knowledge_text, instruction)
        print(f"  ▶ [{self.role_name}] Planning outline...")

        raw_text = self.call(prompt, max_tokens=1500, temperature=0.7)
        json_str = self._extract_json_array(raw_text)
        items = json.loads(json_str)

        outline = [OutlineItem.from_dict(item) for item in items]
        print(f"  ✓ [{self.role_name}] Outline: {len(outline)} slides planned")
        return outline

    @staticmethod
    def _extract_json_array(text: str) -> str:
        """Extract JSON array from LLM response, handling markdown blocks."""
        text = text.strip()
        if "```" in text:
            match = re.search(r'```(?:json)?\s*(\[.*?\])\s*```', text, re.DOTALL)
            if match:
                text = match.group(1)
        start = text.find('[')
        end = text.rfind(']')
        if start >= 0 and end > start:
            return text[start:end + 1]
        return text


class GeneratorAgent(LLMAgent):
    """Generates slide content via streaming."""

    def __init__(self):
        super().__init__(GENERATOR_SYSTEM, role_name="generator")

    def generate_streaming(
        self,
        outline: Optional[List[OutlineItem]],
        knowledge_text: str,
        instruction: str,
        wiki_titles: List[str],
        template_style_text: str = "",
    ) -> Generator[Dict[str, Any], None, None]:
        """
        Stream slide generation. Yields SSE events:
          {"type": "token", "text": "..."}
          {"type": "slide", "index": N, "slide": {...}}

        This is the core streaming generator that the pipeline calls.
        """
        # Build prompt based on whether we have an outline
        if outline:
            prompt = build_generator_prompt(
                [o.to_dict() for o in outline],
                knowledge_text,
                instruction,
                wiki_titles,
                template_style_text,
            )
        else:
            prompt = build_generator_prompt_no_outline(
                knowledge_text,
                instruction,
                wiki_titles,
                template_style_text,
            )

        print(f"  ▶ [{self.role_name}] Generating slides (streaming)...")

        resp = self.call_streaming(prompt, max_tokens=4096, temperature=0.7)

        buffer = ""
        slide_count = 0
        token_batch = ""
        last_flush = time.time()

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if not content:
                    continue

                buffer += content
                token_batch += content

                # Strip <think>...</think> blocks from buffer to avoid
                # false SLIDE: matches inside reasoning content
                while "<think>" in buffer and "</think>" in buffer:
                    start = buffer.find("<think>")
                    end = buffer.find("</think>") + len("</think>")
                    buffer = buffer[:start] + buffer[end:]

                # Forward tokens every ~80ms
                now = time.time()
                if now - last_flush >= 0.08 or len(token_batch) > 20:
                    yield {"type": "token", "text": token_batch}
                    token_batch = ""
                    last_flush = now

                # Extract complete SLIDE:{...} blocks
                while "SLIDE:" in buffer:
                    slide = self._extract_slide_json(buffer)
                    if slide is None:
                        # Could not extract a valid slide from the first SLIDE: marker.
                        # Check if JSON is incomplete (still streaming) vs malformed.
                        idx = buffer.find("SLIDE:")
                        # Look for the next SLIDE: or end-of-buffer
                        next_slide = buffer.find("SLIDE:", idx + 6)
                        if next_slide == -1:
                            # Only one SLIDE: marker — might be incomplete, wait for more data
                            break
                        else:
                            # There's another SLIDE: after this one.
                            # The first one is likely malformed — skip past it.
                            print(f"  ⚠ [{self.role_name}] Skipping malformed SLIDE block")
                            buffer = buffer[next_slide:]
                            continue
                    slide_data, end_pos = slide
                    slide_count += 1
                    print(f"  ✓ [{self.role_name}] Slide {slide_count}: "
                          f"{slide_data.get('type','?')} — {slide_data.get('title','')[:30]}")
                    yield {
                        "type": "slide",
                        "index": slide_count - 1,
                        "slide": slide_data,
                    }
                    buffer = buffer[end_pos:]

            except json.JSONDecodeError:
                continue

        # Flush remaining tokens
        if token_batch:
            yield {"type": "token", "text": token_batch}

        yield {"type": "done", "total": slide_count}
        print(f"  ✓ [{self.role_name}] Generation complete: {slide_count} slides")
        if slide_count == 0 and buffer:
            # Log buffer content for debugging
            preview = buffer[:500].replace('\n', '\\n')
            print(f"  ⚠ [{self.role_name}] Buffer had no slides. Preview: {preview}")

    def continue_streaming(
        self,
        existing_slides: List[Dict[str, Any]],
        knowledge_text: str,
        original_instruction: str,
        continue_instruction: str,
        wiki_titles: List[str],
        template_style_text: str = "",
    ) -> Generator[Dict[str, Any], None, None]:
        """Continue generating a deck after an interruption, yielding only new slides."""
        prompt = build_continuation_prompt(
            existing_slides=existing_slides,
            knowledge_text=knowledge_text,
            original_instruction=original_instruction,
            continue_instruction=continue_instruction,
            wiki_titles=wiki_titles,
            template_style_text=template_style_text,
        )

        print(f"  ▶ [{self.role_name}] Continuing deck from {len(existing_slides)} existing slides...")
        resp = self.call_streaming(prompt, max_tokens=2200, temperature=0.6)

        buffer = ""
        token_batch = ""
        last_flush = time.time()
        slide_count = 0
        base_index = len(existing_slides)

        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break

            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                if not content:
                    continue

                buffer += content
                token_batch += content

                while "<think>" in buffer and "</think>" in buffer:
                    start = buffer.find("<think>")
                    end = buffer.find("</think>") + len("</think>")
                    buffer = buffer[:start] + buffer[end:]

                now = time.time()
                if now - last_flush >= 0.08 or len(token_batch) > 20:
                    yield {"type": "token", "text": token_batch}
                    token_batch = ""
                    last_flush = now

                while "SLIDE:" in buffer:
                    slide = self._extract_slide_json(buffer)
                    if slide is None:
                        next_slide = buffer.find("SLIDE:", buffer.find("SLIDE:") + 6)
                        if next_slide == -1:
                            break
                        buffer = buffer[next_slide:]
                        continue
                    slide_data, end_pos = slide
                    slide_count += 1
                    yield {
                        "type": "slide",
                        "index": base_index + slide_count - 1,
                        "slide": slide_data,
                    }
                    buffer = buffer[end_pos:]
            except json.JSONDecodeError:
                continue

        if token_batch:
            yield {"type": "token", "text": token_batch}

        yield {"type": "done", "total": base_index + slide_count}

    @staticmethod
    def _extract_slide_json(buffer: str) -> Optional[Tuple[Dict, int]]:
        """
        Extract the first complete SLIDE:{...} JSON from buffer.
        Returns (parsed_dict, end_position) or None if incomplete.
        """
        idx = buffer.find("SLIDE:")
        if idx < 0:
            return None

        json_start = idx + 6
        # Skip whitespace
        while json_start < len(buffer) and buffer[json_start] in " \t\r\n":
            json_start += 1

        if json_start >= len(buffer) or buffer[json_start] != "{":
            return None

        # Brace-depth counting
        depth, in_str, esc = 0, False, False
        json_end = -1
        for i in range(json_start, len(buffer)):
            c = buffer[i]
            if esc:
                esc = False
                continue
            if c == "\\" and in_str:
                esc = True
                continue
            if c == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if c == "{":
                depth += 1
            elif c == "}":
                depth -= 1
                if depth == 0:
                    json_end = i + 1
                    break

        if json_end == -1:
            return None

        json_str = buffer[json_start:json_end]
        try:
            data = json.loads(json_str)
            return data, json_end
        except json.JSONDecodeError:
            # Try to find the real end by looking for a newline after the first }
            # that brings depth to 0, then try alternative end positions
            # Also try up to the next SLIDE: or newline boundary
            for boundary in ["\nSLIDE:", "\n\n"]:
                bi = buffer.find(boundary, json_start)
                if bi > json_start:
                    candidate = buffer[json_start:bi].rstrip()
                    # Ensure it ends with }
                    if candidate.endswith("}"):
                        try:
                            data = json.loads(candidate)
                            return data, bi
                        except json.JSONDecodeError:
                            pass
            return None


class EditorAgent(LLMAgent):
    """Edits individual slides."""

    def __init__(self):
        super().__init__(EDITOR_SYSTEM, role_name="editor")

    def edit(
        self,
        slide_dict: Dict[str, Any],
        instruction: str,
        page_index: int,
        context: str = "",
    ) -> Optional[Dict[str, Any]]:
        """
        Edit a single slide. Returns new slide dict or None on failure.
        """
        prompt = build_editor_prompt(slide_dict, instruction, page_index, context)
        print(f"  ▶ [{self.role_name}] Editing slide {page_index + 1}: {instruction[:50]}")

        resp = self.call_streaming(prompt, max_tokens=800, temperature=0.5)

        # Parse SLIDE:{...} from streaming response
        full_text = ""
        for raw_line in resp.iter_lines():
            if not raw_line:
                continue
            line = raw_line.decode("utf-8")
            if not line.startswith("data: "):
                continue
            data_str = line[6:].strip()
            if data_str == "[DONE]":
                break
            try:
                chunk = json.loads(data_str)
                delta = chunk.get("choices", [{}])[0].get("delta", {})
                content = delta.get("content", "")
                full_text += content
            except json.JSONDecodeError:
                continue

        full_text = self._strip_thinking(full_text)

        # Extract slide JSON
        result = GeneratorAgent._extract_slide_json(full_text)
        if result:
            new_slide, _ = result
            # Preserve source/badge from original if missing
            new_slide.setdefault("source", slide_dict.get("source", ""))
            new_slide.setdefault("badge", slide_dict.get("badge", ""))
            print(f"  ✓ [{self.role_name}] Slide {page_index + 1} updated")
            return new_slide

        # Fallback: some models omit the SLIDE: prefix and return raw JSON.
        raw_json = self._extract_first_json_object(full_text)
        if raw_json is not None:
            raw_json.setdefault("source", slide_dict.get("source", ""))
            raw_json.setdefault("badge", slide_dict.get("badge", ""))
            print(f"  ✓ [{self.role_name}] Slide {page_index + 1} updated (raw JSON fallback)")
            return raw_json

        # Final fallback: non-streaming call can be more stable on some providers.
        try:
            retry_text = self.call(prompt, max_tokens=900, temperature=0.3)
            retry_text = self._strip_thinking(retry_text)
            retry_result = GeneratorAgent._extract_slide_json(retry_text)
            if retry_result:
                new_slide, _ = retry_result
                new_slide.setdefault("source", slide_dict.get("source", ""))
                new_slide.setdefault("badge", slide_dict.get("badge", ""))
                print(f"  ✓ [{self.role_name}] Slide {page_index + 1} updated (sync fallback)")
                return new_slide
            raw_retry = self._extract_first_json_object(retry_text)
            if raw_retry is not None:
                raw_retry.setdefault("source", slide_dict.get("source", ""))
                raw_retry.setdefault("badge", slide_dict.get("badge", ""))
                print(f"  ✓ [{self.role_name}] Slide {page_index + 1} updated (sync raw JSON fallback)")
                return raw_retry
        except Exception as fallback_error:
            print(f"  ⚠ [{self.role_name}] Sync fallback failed: {fallback_error}")

        print(f"  ✗ [{self.role_name}] Failed to parse edited slide")
        return None

    @staticmethod
    def _strip_thinking(text: str) -> str:
        cleaned = text or ""
        while "<think>" in cleaned and "</think>" in cleaned:
            start = cleaned.find("<think>")
            end = cleaned.find("</think>") + len("</think>")
            cleaned = cleaned[:start] + cleaned[end:]
        return cleaned.strip()

    @staticmethod
    def _extract_first_json_object(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        start = text.find("{")
        end = text.rfind("}")
        if start < 0 or end <= start:
            return None
        candidate = text[start:end + 1]
        try:
            parsed = json.loads(candidate)
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None


class CommandInterpreterAgent(LLMAgent):
    """Interprets free-form textbox commands into structured PPT actions.
    
    Uses short timeout and no retries — frontend has its own 6s abort
    and always falls back to local parser if this is slow.
    """

    MAX_RETRIES = 1   # No retries — speed is critical for interactive use
    TIMEOUT = 8       # 8s max, frontend aborts at 6s anyway

    def __init__(self):
        super().__init__(COMMAND_INTERPRETER_SYSTEM, role_name="command-interpreter")

    def interpret(
        self,
        instruction: str,
        slides: List[Dict[str, Any]],
        current_slide_index: int,
        can_continue_generation: bool,
        generation_status: str,
        last_generation_instruction: str = "",
    ) -> Dict[str, Any]:
        prompt = build_command_interpreter_prompt(
            instruction=instruction,
            slides=slides,
            current_slide_index=current_slide_index,
            can_continue_generation=can_continue_generation,
            generation_status=generation_status,
            last_generation_instruction=last_generation_instruction,
        )
        print(f"  ▶ [{self.role_name}] Interpreting command: {instruction[:60]}")

        raw_text = self.call(prompt, max_tokens=500, temperature=0.1)
        parsed = self._extract_json(raw_text)
        if parsed is None:
            raise RuntimeError("无法解析命令理解结果")

        parsed.setdefault("action", "noop")
        parsed.setdefault("page_index", current_slide_index)
        parsed.setdefault("navigation", None)
        parsed.setdefault("edit_instruction", instruction)
        parsed.setdefault("should_use_local", False)
        parsed.setdefault("confidence", 0.0)
        parsed.setdefault("reason", "")
        return parsed

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        if not text:
            return None
        cleaned = EditorAgent._strip_thinking(text).strip()
        if cleaned.startswith("```"):
            match = re.search(r'```(?:json)?\s*(\{.*\})\s*```', cleaned, re.DOTALL)
            if match:
                cleaned = match.group(1)

        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start < 0 or end <= start:
            return None

        try:
            parsed = json.loads(cleaned[start:end + 1])
            return parsed if isinstance(parsed, dict) else None
        except json.JSONDecodeError:
            return None
