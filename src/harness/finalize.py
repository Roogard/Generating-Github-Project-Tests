"""Final accounting — build the persist-ready dict the agent returns.

The harness maintains `ctx.last_feedback` after each pytest invocation;
finalize reads it. The only case it's None is an early exit before any
test code was written.

No benchmark-mode branching — F→P / F→F / P→F / P→P labels are computed
post-hoc by `src/graders/oracle.py` and composed into the Run row by
`src/persist.py`. Finalize only reports what the harness directly observed.
"""
from __future__ import annotations

import os
from pathlib import Path

from src.harness.context import HarnessContext


def finalize(ctx: HarnessContext) -> dict:
    test_exists = os.path.isfile(ctx.test_file_path)
    out: dict = {
        "test_file_path": ctx.test_file_path if test_exists else "",
        "test_code": Path(ctx.test_file_path).read_text(encoding="utf-8") if test_exists else "",
        "turns_used": ctx.llm_calls_used,
        "finish_reason": _derive_finish_reason(ctx),
        "history": list(ctx.attempts),
    }

    fb = ctx.last_feedback
    if fb is None:
        out.update({
            "final_run": {},
            "tests_passed": 0, "tests_failed": 0, "tests_errored": 0, "tests_run": 0,
        })
        return out

    run_result = fb.run_result or {}
    out["final_run"] = run_result
    out["tests_passed"] = len(run_result.get("passed", []))
    out["tests_failed"] = len(run_result.get("failed", []))
    out["tests_errored"] = len([e for e in run_result.get("errors", [])
                                if not e.startswith("__")])
    out["tests_run"] = out["tests_passed"] + out["tests_failed"] + out["tests_errored"]
    return out


def _derive_finish_reason(ctx: HarnessContext) -> str:
    fb = ctx.last_feedback
    if fb is None:
        return "no-feedback"
    if ctx.llm_calls_used >= ctx.llm_budget:
        return "budget-exhausted"
    if fb.has_infrastructure_problems:
        return "infrastructure-problems-remaining"
    return "done"
