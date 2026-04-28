"""Data shapes that flow between layers (input adapters → agent → graders
→ persistence). Single source of truth — nothing in here imports any layer.

Layer guide:
  AgentTask    — what the agent receives. One task = one (repo, issue) pair.
                 The agent localizes the relevant code itself via tools.
  RunBatch     — the unit of persistence. One batch = one Run row + N tasks.
  AgentResult  — what the agent produced. No mutation/coverage fields.
  OracleGrade  — post-hoc F→P/F→F/P→F/P→P labels. Only built when the task
                 carries a `gold_patch`.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.runtime.base import Runtime


@dataclass
class AgentTask:
    """Issue-driven. One task = one (repo, issue) pair."""

    # Identity / display
    source: str  # 'repo' | 'swtbench'
    label: str   # human-readable identifier
    instance_id: str | None = None  # benchmarks only
    dataset: str | None = None      # benchmarks only

    # Repo state — already prepared by the adapter
    repo_dir: str = ""
    runtime: "Runtime | None" = None  # adapter chose Local / Docker / SwtBench

    # The issue — REQUIRED. Empty issue_text is rejected at task construction.
    issue_text: str = ""
    issue_title: str = ""
    hints_text: str = ""

    # Optional gold answer — enables the post-hoc oracle grader when present.
    # We deliberately do NOT expose anything derived from this to the agent
    # (e.g. touched_files): the agent must localize from the issue alone, the
    # same as reference SWE-Agent / OpenHands setups.
    gold_patch: str | None = None

    # Per-run config
    cfg: dict = field(default_factory=dict)
    out_dir: str = ""
    timeout: int = 60
    max_llm_calls: int = 8
    agentic_turn_cap: int = 6
    per_test_timeout: int | None = None
    examples_dir: Path | None = None


@dataclass
class RunBatch:
    """A group of tasks that share a single Run row.

    Issue-driven adapters yield exactly one task per batch:
      - SwtBenchAdapter: one batch per HF instance.
      - RepoAdapter:     one batch per (repo_url, issue_text) input.
    """

    run_metadata: dict        # repo_url, mode, dataset, benchmark_id, provider, model, preset
    tasks: list["AgentTask"]


@dataclass
class AgentResult:
    """What the harness produced for one task. No mutation/coverage —
    F→P grading happens post-hoc and is composed in by the runner separately.
    """

    test_file_path: str
    test_code: str
    turns_used: int
    finish_reason: str
    history: list[dict]
    final_run: dict           # last pytest result
    tests_passed: int
    tests_failed: int
    tests_errored: int
    tests_run: int


@dataclass
class OracleGrade:
    """Post-hoc F→P / F→F / P→F / P→P labels. Only built when the task
    carried a `gold_patch`. The runner calls grade_with_oracle(task, result)
    AFTER the agent finishes — never inside the harness loop."""

    f2p: int
    f2f: int
    p2f: int
    p2p: int
    detected: bool
    resolved: bool
    labels: list[tuple[str, str]] = field(default_factory=list)
    buggy_run: dict = field(default_factory=dict)
    fixed_run: dict = field(default_factory=dict)
