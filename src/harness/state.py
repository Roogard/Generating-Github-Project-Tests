"""Per-task state: HarnessContext + the test-file I/O helpers it leans on.

`HarnessContext` is plain data — fields only. The skills mutate `analysis`,
`llm_calls_used`, `attempts`, etc. directly. The pipeline reads them.

The two file-I/O helpers (`write_test_file`, `read_test_file`) used to live
on the dataclass as methods. They moved out so the class stays a record-shaped
data container and the I/O is independently testable. They take `HarnessContext`
as their first arg because they need both `test_file_path` and `read_paths`.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from src.text_utils import strip_code_fence

if TYPE_CHECKING:
    from src.runtime.base import Runtime


_RELATIVE_IMPORT_RE = re.compile(r'^\s*(from\s+\.|\bimport\s+\.)')


def _strip_relative_imports(code: str) -> str:
    return "\n".join(
        line for line in code.splitlines() if not _RELATIVE_IMPORT_RE.match(line)
    )


class BudgetExhausted(RuntimeError):
    """Raised when a skill tries to call the LLM past the configured budget."""


@dataclass
class HarnessContext:
    repo_dir: str
    test_dir: str
    cfg: dict
    timeout: int
    per_test_timeout: int | None
    runtime: "Runtime"  # Local / Docker / SwtBench, built per-run by the adapter
    llm_budget: int

    # The issue — required. Empty issue_text is rejected by run_harness.
    issue_text: str = ""
    issue_title: str = ""
    hints_text: str = ""

    # Cap on tool-use turns inside an agentic skill. Single-call skills ignore.
    agentic_turn_cap: int = 6

    test_file_path: str = ""
    llm_calls_used: int = 0
    analysis: dict | None = None
    last_feedback: "Feedback | None" = None  # noqa: F821 — forward-ref to harness.feedback
    last_critique: dict | None = None
    attempts: list[dict] = field(default_factory=list)

    # Files the agent has Read this session. Edit refuses to operate on files
    # not in this set — mirrors Claude Code's "must Read before Edit" rule.
    read_paths: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        os.makedirs(self.test_dir, exist_ok=True)
        if not self.test_file_path:
            self.test_file_path = os.path.join(self.test_dir, "test_agent.py")

        # SwtBench: the agent (src/agent.py) registers the test file via
        # `runtime.set_active_test_file()` before calling run_harness. The
        # runtime's per-exec preamble copies our host file into
        # `/testbed/test_ggpt_agent.py`. Don't write a local conftest in
        # that case — we want the repo's `/testbed/conftest.py` to be
        # the only one pytest finds.
        from src.runtime.swtbench import SwtBenchRuntime
        if isinstance(self.runtime, SwtBenchRuntime):
            return

        # Generic Local/Docker path: write a conftest that pins sys.path
        # at the repo root. The repo's own conftest still applies — pytest
        # walks up from the test file looking for it.
        conftest = os.path.join(self.test_dir, "conftest.py")
        runtime_repo = self.runtime.translate(os.path.abspath(self.repo_dir))
        with open(conftest, "w", encoding="utf-8") as f:
            f.write(f"import sys; sys.path.insert(0, {repr(runtime_repo)})\n")

        # Also drop a minimal pytest.ini so pytest doesn't walk up from
        # cwd=repo_dir into the repo's setup.cfg / pyproject.toml. Repos
        # commonly set `filterwarnings = error` (turns import-time warnings
        # into errors during collection) or aggressive `addopts`, both of
        # which prevent our test from being collected. test_runner.py
        # passes `-c` pointing at this file so this config wins.
        pytest_ini = os.path.join(self.test_dir, "pytest.ini")
        with open(pytest_ini, "w", encoding="utf-8") as f:
            f.write("[pytest]\n")


def write_test_file(ctx: HarnessContext, code: str) -> int:
    """Write LLM output to `ctx.test_file_path`. Strips markdown fences and
    relative imports. Marks the path as Read so subsequent Edits are allowed
    without an explicit Read call. Returns the number of lines written.
    """
    if not code or not code.strip():
        raise ValueError("code is empty")
    code = strip_code_fence(code)
    code = _strip_relative_imports(code)
    Path(ctx.test_file_path).write_text(code, encoding="utf-8")
    ctx.read_paths.add(str(Path(ctx.test_file_path).resolve()))
    return len(code.splitlines())


def read_test_file(ctx: HarnessContext) -> str:
    """Read the current test file. Returns '' if it doesn't exist yet."""
    if not os.path.isfile(ctx.test_file_path):
        return ""
    return Path(ctx.test_file_path).read_text(encoding="utf-8")
