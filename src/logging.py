"""Structured logging setup.

One-time `configure_logging()` wires structlog with two output formats:

  - Console-pretty (default; for dev / interactive Docker logs)
  - JSON-per-line (when `GGPT_LOG_JSON=1`; for prod ingestion)

Per-module loggers are obtained via `structlog.get_logger(__name__)`. Bind
the run_id at the top of `run_harness` (via `structlog.contextvars.bind_contextvars`)
so every nested log line in skills / agentic loop carries it automatically.

The agentic loop is the most complex part of the system and was previously
invisible at runtime — every print() has been replaced with a structured
log call so the agent's tool calls, pytest invocations, and budget burn
are all greppable / parseable.
"""
from __future__ import annotations

import logging
import sys

import structlog

from src import config


_configured = False


def configure_logging(level: int = logging.INFO) -> None:
    """Configure structlog once per process. Subsequent calls are no-ops."""
    global _configured
    if _configured:
        return
    _configured = True

    timestamper = structlog.processors.TimeStamper(fmt="iso", utc=True)

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        timestamper,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if config.LOG_JSON:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=False))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str = "ggpt"):
    """Convenience wrapper for `structlog.get_logger(name)`."""
    return structlog.get_logger(name)
