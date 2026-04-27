"""InputAdapter ABC + shared infrastructure for the two concrete adapters.

An adapter's job is the messy bit: turn one input source (HF dataset row,
GitHub URL + issue text) into one or more `AgentTask`s wrapped in a
`RunBatch`. The runner then iterates over batches and runs each task
through `run_agent`.

Each batch corresponds to exactly one Run row in the DB. Both adapters
yield exactly one task per batch:
  - SwtBenchAdapter: one batch per HF instance.
  - RepoAdapter:     one batch per (repo_url, issue_text) input.
"""
from __future__ import annotations

import os
import shutil
import stat
from abc import ABC, abstractmethod
from typing import Iterator

from src.types import RunBatch


PRESETS = {
    "fast":     {"timeout": 60,  "max_llm_calls": 10, "agentic_turn_cap": 4,  "per_test_timeout": 2},
    "default":  {"timeout": 180, "max_llm_calls": 28, "agentic_turn_cap": 10, "per_test_timeout": 5},
    "thorough": {"timeout": 300, "max_llm_calls": 40, "agentic_turn_cap": 14, "per_test_timeout": 10},
}


class InputAdapter(ABC):
    """One adapter per input source. Adapters yield `RunBatch` objects."""

    source: str  # 'repo' | 'swtbench' — set by subclass

    @abstractmethod
    def iter_batches(self) -> Iterator[RunBatch]:
        """Yield one `RunBatch` per Run row that should be created."""


# ── shared helpers used by adapters ────────────────────────────────────────

def force_rmtree(path: str) -> None:
    """rmtree that survives Windows read-only files in `.git/objects/pack/`.

    Git creates pack files with the read-only bit set; on Windows
    `shutil.rmtree` fails on those unless we explicitly chmod first.
    `ignore_errors=True` would silently leave partial dirs, which makes the
    next clone fail with "destination not empty". This handler chmods,
    retries, and only swallows on a second failure.
    """
    if not os.path.exists(path):
        return

    def on_rm_error(func, p, _exc):
        try:
            os.chmod(p, stat.S_IWRITE)
            func(p)
        except Exception:
            pass

    try:
        shutil.rmtree(path, onexc=on_rm_error)  # 3.12+
    except TypeError:
        shutil.rmtree(path, onerror=on_rm_error)  # legacy
