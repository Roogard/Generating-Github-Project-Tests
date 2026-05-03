"""Pytest result → structured Feedback.

Pure conversion: takes the dict returned by `src.test_runner.run_tests` and
classifies each entry. The `next_action` gate decides whether the harness
fires the Improve fallback:

  - Collection problems / setup errors / timeouts → "improve" (infrastructure)
  - Otherwise (including assertion failures only) → "done"

Pytest assertion failures are deliberately NOT improve signals — they may be
the F→P detection we want.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.text_utils import truncate


_LONGREPR_CAP = 300


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
            "longrepr": truncate(detail.get("longrepr", ""), _LONGREPR_CAP),
        })

    error_details = run_result.get("error_details") or []
    raw_errors = run_result.get("errors", [])
    real_errors = [n for n in raw_errors if not n.startswith("__")]
    for i, name in enumerate(real_errors):
        bare = name.split("::")[-1]
        detail = error_details[i] if i < len(error_details) else {}
        fb.errors.append({
            "name": bare,
            "longrepr": truncate(detail.get("longrepr", ""), _LONGREPR_CAP),
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
            "longrepr": truncate(detail.get("longrepr", ""), 600),
        })
    # If pytest ran cleanly but produced zero tests, that's a "no signal" condition.
    if not raw_errors and not run_result.get("passed") and not run_result.get("failed"):
        fb.collection_problems.append({
            "kind": "no_tests_collected",
            "longrepr": "pytest collected zero tests from the file. "
                        "Did you forget to define any `def test_*` functions?",
        })

    fb.next_action = "improve" if fb.has_infrastructure_problems else "done"
    return fb
