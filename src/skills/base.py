"""Skill base class — narrow LLM call wrappers.

Each skill loads its prompt (shared preamble + own task description) and
produces a response. Single-call skills (Analyze, Critique) invoke the LLM
once and return a stripped string. Agentic skills (Generate, Improve) loop
through the tool kit until the model emits a final message with no tool
calls — see src/skills/agentic.py.

Skills don't run subprocesses, don't write files, and don't call the oracle
— the harness owns side effects.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from langchain_core.messages import HumanMessage

from src.harness import BudgetExhausted, HarnessContext
from src.llm import cached_system_message, get_llm


_PROMPTS_DIR = Path(__file__).parent / "prompts"
_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*\n(.*?)```", re.DOTALL)
_PROMPT_CACHE: dict[str, str] = {}


def _load_prompt(filename: str) -> str:
    if filename in _PROMPT_CACHE:
        return _PROMPT_CACHE[filename]
    path = _PROMPTS_DIR / filename
    text = path.read_text(encoding="utf-8")
    _PROMPT_CACHE[filename] = text
    return text


class Skill:
    name: str = ""
    prompt_file: str = ""

    def __init__(self) -> None:
        if not self.name or not self.prompt_file:
            raise ValueError(f"{type(self).__name__} must set name and prompt_file")
        shared = _load_prompt("_shared.md")
        own = _load_prompt(self.prompt_file)
        self._system_prompt = shared + "\n\n---\n\n" + own

    def _call_llm(self, ctx: HarnessContext, user_msg: str) -> str:
        if ctx.llm_calls_used >= ctx.llm_budget:
            raise BudgetExhausted(self.name)
        llm = get_llm(ctx.cfg)
        resp = llm.invoke([cached_system_message(ctx.cfg, self._system_prompt), HumanMessage(user_msg)])
        ctx.llm_calls_used += 1
        content = resp.content
        if isinstance(content, list):  # some providers return a list of parts
            content = "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
        return content or ""

    @staticmethod
    def _parse_json_block(text: str) -> dict:
        """Tolerant JSON extraction. Tries fenced ```json ... ``` first, then
        the first '{...}' span, then the raw text. Returns {} on failure.
        """
        m = _JSON_FENCE_RE.search(text)
        if m:
            blob = m.group(1)
        else:
            start = text.find("{")
            end = text.rfind("}")
            blob = text[start:end + 1] if start != -1 and end > start else text
        try:
            obj = json.loads(blob)
            return obj if isinstance(obj, dict) else {}
        except (json.JSONDecodeError, ValueError):
            return {}

    def run(self, ctx: HarnessContext) -> str | dict:
        raise NotImplementedError


_ISSUE_BODY_CAP = 3000
_HINTS_CAP = 800


def format_intent_section(ctx: HarnessContext) -> str:
    """Render the authoritative-spec block to prepend to skill prompts.

    Returns an empty string in standalone (non-benchmark) mode so skills fall
    back to inferring intent from the function name / docstring.

    Section layout matches Otter (ICML 2025): issue description first, then
    hints. Kept above function source in caller prompts so the LLM reads
    intent before implementation.
    """
    issue = (ctx.issue_text or "").strip()
    if not issue:
        return ""
    title = (ctx.issue_title or "").strip()
    hints = (ctx.hints_text or "").strip()

    parts = ["## Intended behavior (authoritative spec)"]
    if title:
        parts.append(f"### Issue: {title}")
    body = issue[:_ISSUE_BODY_CAP]
    if len(issue) > _ISSUE_BODY_CAP:
        body += "\n...[truncated]"
    parts.append(body)
    if hints:
        capped = hints[:_HINTS_CAP]
        if len(hints) > _HINTS_CAP:
            capped += "\n...[truncated]"
        parts.append("### PR hints")
        parts.append(capped)
    parts.append("")  # trailing blank for spacing when concatenated
    return "\n".join(parts)
