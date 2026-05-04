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

GitHub App webhook entrypoint (api/github.py):

  GITHUB_WEBHOOK_SECRET     HMAC-SHA256 secret used to verify incoming
                            webhook payloads. Required for the webhook
                            endpoint to accept anything other than `ping`.
  GITHUB_APP_ID             Numeric App ID (from the GitHub App settings
                            page). Used as the JWT `iss` claim when minting
                            installation tokens. Required for PR-back.
  GITHUB_PRIVATE_KEY_PATH   Path to the App's RS256 private key (PEM).
                            Required for PR-back.
  GITHUB_TRIGGER_LABEL      Label whose addition fires a run (default
                            "ggpt"). Match is case-sensitive.
  GITHUB_DEFAULT_PROVIDER   LLM provider for app-triggered runs
                            (default "deepseek").
  GITHUB_DEFAULT_MODEL      LLM model override; None → provider default.

Per-provider API keys (DEEPSEEK_API_KEY, OPENAI_API_KEY, ANTHROPIC_API_KEY)
are still read directly in src/llm.py — they're scoped to that module and
their names are looked up via the `_PROVIDERS` dict, which is the wrong
shape for a flat constant table.
"""
from __future__ import annotations

import os


RUNTIME: str = (os.getenv("GGPT_RUNTIME") or "auto").strip().lower()
DOCKER_IMAGE: str = os.getenv("GGPT_DOCKER_IMAGE", "ggpt-runtime")
LLM_BASE_URL: str | None = os.getenv("LLM_BASE_URL") or None
LOG_JSON: bool = os.getenv("GGPT_LOG_JSON") == "1"

GITHUB_WEBHOOK_SECRET: str = os.getenv("GITHUB_WEBHOOK_SECRET", "")
GITHUB_APP_ID: str = os.getenv("GITHUB_APP_ID", "")
GITHUB_PRIVATE_KEY_PATH: str = os.getenv("GITHUB_PRIVATE_KEY_PATH", "")
GITHUB_TRIGGER_LABEL: str = os.getenv("GITHUB_TRIGGER_LABEL", "ggpt")
GITHUB_DEFAULT_PROVIDER: str = os.getenv("GITHUB_DEFAULT_PROVIDER", "deepseek")
GITHUB_DEFAULT_MODEL: str | None = os.getenv("GITHUB_DEFAULT_MODEL") or None
