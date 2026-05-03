"""Shared test fixtures.

`StubRuntime` lets us construct a `HarnessContext` without spawning subprocesses
or pulling Docker images. `HarnessContext.__post_init__` calls
`runtime.translate(...)` and isinstance-checks against `SwtBenchRuntime`; this
stub satisfies both.
"""
from __future__ import annotations

import pytest

from src.harness import HarnessContext


class StubRuntime:
    """Minimal Runtime stand-in for unit tests."""

    def translate(self, p: str) -> str:
        return p


@pytest.fixture
def ctx(tmp_path):
    """A HarnessContext rooted at tmp_path. test_dir is a child of tmp_path/out
    so writes are isolated per-test."""
    repo_dir = tmp_path / "repo"
    repo_dir.mkdir()
    test_dir = tmp_path / "out" / "tests"
    return HarnessContext(
        repo_dir=str(repo_dir),
        test_dir=str(test_dir),
        cfg={"provider": "anthropic", "model": "x"},
        timeout=30,
        per_test_timeout=None,
        runtime=StubRuntime(),
        llm_budget=10,
        issue_text="A bug in the widget.",
    )
