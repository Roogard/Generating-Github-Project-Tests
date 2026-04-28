"""Convert pytest results into a structured Feedback object.

Pure conversion. No LLM, no I/O. The orchestrator's `next_action` decision
lives here so improvement gating is testable and deterministic.

Issue-driven signal hierarchy:
  1. Collection problems / setup errors / timeouts → "improve"
  2. Otherwise → "done"

Critical: pytest assertion failures are NOT improve signals — they may be
the F→P detections we want. The harness never silences them. Only
infrastructure-level problems (test file can't be imported, fixture missing,
test hung) trigger Improve.

The post-hoc oracle grader (src/graders/oracle.py) computes F→P / F→F /
P→F / P→P after the harness finishes. Those labels never enter Feedback.
"""
from __future__ import annotations

from dataclasses import dataclass, field


_LONGREPR_CAP = 300


def _truncate(text: str, cap: int = _LONGREPR_CAP) -> str:
    text = (text or "").strip()
    if len(text) > cap:
        return text[:cap] + "...[truncated]"
    return text


@dataclass
class Feedback:
    failures: list[dict] = field(default_factory=list)
    errors: list[dict] = field(default_factory=list)
    timeouts: list[str] = field(default_factory=list)

    # Pytest-level problems that aren't per-test failures: import errors,
    # collection errors, "no tests collected" (exit code 5), session timeouts.
    # These ARE improve signals — without a working test file we have nothing.
    collection_problems: list[dict] = field(default_factory=list)

    next_action: str = "done"

    run_result: dict = field(default_factory=dict)

    @property
    def has_infrastructure_problems(self) -> bool:
        """Problems that prevent the test file from running at all.

        Includes: collection errors, real errors (AttributeError on construction
        / fixture failures / etc.), and timeouts. Does NOT include pytest
        assertion failures — those are potential F→P detections.
        """
        return bool(self.errors or self.timeouts or self.collection_problems)


def build_feedback(run_result: dict) -> Feedback:
    fb = Feedback(run_result=dict(run_result or {}))

    timed_out_set = {n.split("::")[-1] for n in run_result.get("timed_out", [])}
    fb.timeouts = sorted(timed_out_set)

    failure_details = run_result.get("failure_details") or []
    for i, name in enumerate(run_result.get("failed", [])):
        bare = name.split("::")[-1]
        detail = failure_details[i] if i < len(failure_details) else {}
        kind = "TIMEOUT" if bare in timed_out_set else "FAILED"
        fb.failures.append({
            "name": bare,
            "kind": kind,
            "longrepr": _truncate(detail.get("longrepr", "")),
        })

    error_details = run_result.get("error_details") or []
    raw_errors = run_result.get("errors", [])
    real_errors = [n for n in raw_errors if not n.startswith("__")]
    for i, name in enumerate(real_errors):
        bare = name.split("::")[-1]
        detail = error_details[i] if i < len(error_details) else {}
        fb.errors.append({
            "name": bare,
            "longrepr": _truncate(detail.get("longrepr", "")),
        })

    # Surface synthetic markers (collection errors, session timeouts, missing
    # file) as collection_problems.
    detail_by_index = {i: error_details[i] if i < len(error_details) else {}
                       for i in range(len(raw_errors))}
    for idx, name in enumerate(raw_errors):
        if not name.startswith("__"):
            continue
        detail = detail_by_index[idx]
        fb.collection_problems.append({
            "kind": name.strip("_"),
            "longrepr": _truncate(detail.get("longrepr", ""), cap=600),
        })
    # If pytest ran cleanly but produced zero tests, that's a "no signal" condition.
    if not raw_errors and not run_result.get("passed") and not run_result.get("failed"):
        fb.collection_problems.append({
            "kind": "no_tests_collected",
            "longrepr": "pytest collected zero tests from the file. "
                        "Did you forget to define any `def test_*` functions?",
        })

    fb.next_action = _decide_next_action(fb)
    return fb


def _decide_next_action(fb: Feedback) -> str:
    """Two-state decision. Improve only if the test file's infrastructure is
    broken; otherwise done. Assertion failures are deliberately classified
    as 'done' — they may be the F→P detection we want.
    """
    if fb.has_infrastructure_problems:
        return "improve"
    return "done"
