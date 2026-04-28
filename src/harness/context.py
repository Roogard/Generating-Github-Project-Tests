"""Per-task harness state (issue-driven).

One HarnessContext per (repo, issue) pair. Skills mutate it (e.g. set
analysis, increment llm_calls_used, append to attempts) and the orchestrator
reads it to decide what to do next.

No `fn` field — the agent localizes to the relevant code itself via tools.
No `import_line` helper — the agent figures out imports by reading the repo.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.harness.feedback import Feedback
    from src.runtime.base import Runtime


_RELATIVE_IMPORT_RE = re.compile(r'^\s*(from\s+\.|\bimport\s+\.)')
_FENCE_RE = re.compile(r"^```(?:python)?\n(.*?)```\s*$", re.DOTALL)


def _strip_relative_imports(code: str) -> str:
    return "\n".join(
        line for line in code.splitlines() if not _RELATIVE_IMPORT_RE.match(line)
    )


def _strip_markdown_fence(code: str) -> str:
    m = _FENCE_RE.match(code.strip())
    return m.group(1) if m else code


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
    examples_dir: Path
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
    last_feedback: "Feedback | None" = None
    attempts: list[dict] = field(default_factory=list)

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

    def write_test_file(self, code: str) -> int:
        """Write LLM output to the test file. Strips relative imports and
        markdown fences. Returns the number of lines written.
        """
        if not code or not code.strip():
            raise ValueError("code is empty")
        code = _strip_markdown_fence(code)
        code = _strip_relative_imports(code)
        with open(self.test_file_path, "w", encoding="utf-8") as f:
            f.write(code)
        return len(code.splitlines())

    def read_test_file(self) -> str:
        if not os.path.isfile(self.test_file_path):
            return ""
        return Path(self.test_file_path).read_text(encoding="utf-8")
