"""Shared text helpers — single canonical home for fence-stripping and truncation.

Previously duplicated in src/harness.py (with cap=300, stricter fence regex)
and src/skills/agentic.py (cap=600, no strip) and src/skills/base.py (different
fence regex). The subtly different defaults were a foot-gun; this module is
the one place that owns those rules.
"""
from __future__ import annotations

import re

# Permissive — allows ``` or ```python with optional whitespace before the newline.
_FENCE_RE = re.compile(r"^```(?:python)?\s*\n(.*?)```\s*$", re.DOTALL)


def truncate(text: str, limit: int) -> str:
    """Strip whitespace, cap length, append '...[truncated]' when capped."""
    text = (text or "").strip()
    if len(text) > limit:
        return text[:limit] + "...[truncated]"
    return text


def strip_code_fence(text: str) -> str:
    """If `text` is a single ```python ... ``` (or bare ``` ... ```) block,
    return the inner content. Otherwise return `text` unchanged.
    """
    m = _FENCE_RE.match(text.strip())
    return m.group(1) if m else text
