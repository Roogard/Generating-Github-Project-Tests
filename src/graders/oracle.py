"""F→P oracle grader (post-hoc).

Wraps `src/oracle.py::run_oracle`. Returns `None` when the task carries no
`gold_patch` — non-benchmark runs skip oracle grading entirely.

Called from the runner AFTER `run_agent` finishes. The grader runs the
test file twice (once on buggy, once on fixed) and labels each test's
transition. None of this feeds back into the agent loop — it's pure
reporting that gets persisted alongside the AgentResult.
"""
from __future__ import annotations

from src.oracle import run_oracle
from src.types import AgentResult, AgentTask, OracleGrade


def grade_with_oracle(task: AgentTask, result: AgentResult) -> OracleGrade | None:
    """Run the SWT-Bench F→P oracle. Returns None if no gold patch is set
    on the task, or if the test file the agent produced is missing/empty.
    """
    if not task.gold_patch:
        return None
    if not result.test_file_path or not result.test_code:
        return None

    benchmark_context = {
        "instance_id": task.instance_id or task.label,
        "gold_patch": task.gold_patch,
    }
    try:
        oracle_result = run_oracle(
            benchmark_context, result.test_file_path, task.repo_dir, task.runtime,
            timeout=task.timeout, per_test_timeout=task.per_test_timeout,
        )
    except Exception as e:
        print(f"  [grader] oracle failed: {type(e).__name__}: {e}")
        return None

    return OracleGrade(
        f2p=oracle_result.f2p,
        f2f=oracle_result.f2f,
        p2f=oracle_result.p2f,
        p2p=oracle_result.p2p,
        detected=oracle_result.detected,
        resolved=oracle_result.resolved,
        labels=oracle_result.labels,
        buggy_run=oracle_result.buggy_run,
        fixed_run=oracle_result.fixed_run,
    )
