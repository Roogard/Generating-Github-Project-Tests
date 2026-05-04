"""Centralised env-var configuration.

Single grep target for "what configures this system?". Each constant is read
once at import time from os.getenv with a documented default. Add new vars
here, not inline in random modules.

  GGPT_RUNTIME         "auto" | "local" | "docker"
                       Forces the runtime selection. "auto" → detect Docker;
                       fall back to local if image / daemon unreachable.
  GGPT_DOCKER_IMAGE    Docker image name for the generic runtime
                       (default: "ggpt-runtime").
  GGPT_LOG_JSON        "1" → emit logs as one-JSON-per-line. Anything else
                       → console-pretty rendering. Used by src.logging.
  LLM_BASE_URL         Override the per-provider base_url (e.g. routing
                       traffic through a proxy). None → use the provider's
                       hardcoded default in src.llm._PROVIDERS.

Per-provider API keys (DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
are still read directly in src/llm.py — they're scoped to that module and
their names are looked up via the `_PROVIDERS` dict, which is the wrong
shape for a flat constant table.
"""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()


RUNTIME: str = (os.getenv("GGPT_RUNTIME") or "auto").strip().lower()
DOCKER_IMAGE: str = os.getenv("GGPT_DOCKER_IMAGE", "ggpt-runtime")
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL") or None
LOG_JSON: bool = os.getenv("GGPT_LOG_JSON") == "1"
