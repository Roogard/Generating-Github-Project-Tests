"""The agent — single entry point regardless of input source.

`run_agent(task)` takes an `AgentTask` produced by an input adapter and
returns an `AgentResult`. Internally it delegates to `run_harness`.

The agent has no benchmark awareness. It receives an issue + a repo and
writes a test file. The runner's post-hoc grader is what produces F→P
labels (when `task.gold_patch` is set).

This module is also where the SwtBench-specific `set_active_test_file`
call lives — registering the test file with the runtime once per task so
that pytest invocations inside the harness see it at
`/testbed/test_ggpt_agent.py` (where the repo's conftest.py is visible).
"""
from __future__ import annotations

import os
import traceback

from src.harness import run_harness
from src.runtime.swtbench import SwtBenchRuntime
from src.types import AgentResult, AgentTask


def run_agent(task: AgentTask, *, run_id: int | None = None) -> AgentResult:
    """Run the harness loop for one task. Returns an AgentResult.

    `run_id` is passed through so the harness can emit live stage updates
    against the matching Run row. Defaults to None for callers (e.g. direct
    tests) that don't have a DB row.

    Caller (the runner) owns the runtime lifecycle — `runtime.shutdown()`
    is called once after all tasks for a runtime have been processed.
    """
    if not task.issue_text or not task.issue_text.strip():
        raise ValueError("AgentTask requires non-empty issue_text — the agent is issue-driven")

    os.makedirs(task.out_dir, exist_ok=True)
    test_dir = os.path.join(task.out_dir, "tests")
    os.makedirs(test_dir, exist_ok=True)

    # SwtBench: register where the about-to-be-written test file should land
    # inside /testbed. The runtime's per-exec preamble copies it before
    # every pytest run. Other runtimes ignore this (default no-op).
    test_file_path = os.path.join(test_dir, "test_agent.py")
    if isinstance(task.runtime, SwtBenchRuntime):
        task.runtime.set_active_test_file(test_file_path)

    try:
        harness_result = run_harness(
            task.cfg, task.repo_dir, task.out_dir, task.runtime,
            run_id=run_id,
            issue_text=task.issue_text,
            issue_title=task.issue_title,
            hints_text=task.hints_text,
            timeout=task.timeout,
            max_llm_calls=task.max_llm_calls,
            agentic_turn_cap=task.agentic_turn_cap,
            per_test_timeout=task.per_test_timeout,
        )
    except Exception as e:
        print(f"  ERROR in harness: {type(e).__name__}: {e}")
        traceback.print_exc()
        return _empty_result()

    return AgentResult(
        test_file_path=harness_result.get("test_file_path", ""),
        test_code=harness_result.get("test_code", ""),
        turns_used=harness_result.get("turns_used", 0),
        finish_reason=harness_result.get("finish_reason", ""),
        history=harness_result.get("history", []),
        final_run=harness_result.get("final_run", {}),
        tests_passed=harness_result.get("tests_passed", 0),
        tests_failed=harness_result.get("tests_failed", 0),
        tests_errored=harness_result.get("tests_errored", 0),
        tests_run=harness_result.get("tests_run", 0),
        critique=harness_result.get("critique"),
    )


def _empty_result() -> AgentResult:
    return AgentResult(
        test_file_path="", test_code="", turns_used=0, finish_reason="error",
        history=[], final_run={},
        tests_passed=0, tests_failed=0, tests_errored=0, tests_run=0,
    )
