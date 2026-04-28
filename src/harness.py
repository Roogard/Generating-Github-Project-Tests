"""Issue-driven harness: per-task state + pytest-feedback dataclass + pipeline.

One file because the three pieces are tightly coupled and only used together:

  - HarnessContext: per-task state. Skills mutate it (analysis, llm_calls_used,
    attempts) and the orchestrator reads it.
  - Feedback: pytest result → structured dataclass with the next_action gate.
    Pure conversion; no LLM, no I/O.
  - run_harness: Analyze → Generate → Execute → maybe Improve once → Finalize.
    The harness owns side effects (file writes, pytest invocation). Skills are
    LLM calls — Analyze and Improve are single-call, Generate is agentic.

Signal hierarchy (issue-driven):
  - Collection problems / setup errors / timeouts → "improve"
  - Otherwise → "done"

Pytest assertion failures are NOT improve signals — they may be the F→P
detections we want. The post-hoc oracle grader (`src/oracle.py::grade_with_oracle`)
labels F→P / F→F / P→F / P→P after run_agent returns; the harness has no
benchmark awareness.
"""
from __future__ import annotations

import os
import re
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from src.test_runner import run_tests as _pytest_run

if TYPE_CHECKING:
    from src.runtime.base import Runtime


# ── Helpers ─────────────────────────────────────────────────────────────────

_RELATIVE_IMPORT_RE = re.compile(r'^\s*(from\s+\.|\bimport\s+\.)')
_FENCE_RE = re.compile(r"^```(?:python)?\n(.*?)```\s*$", re.DOTALL)
_LONGREPR_CAP = 300


def _strip_relative_imports(code: str) -> str:
    return "\n".join(
        line for line in code.splitlines() if not _RELATIVE_IMPORT_RE.match(line)
    )


def _strip_markdown_fence(code: str) -> str:
    m = _FENCE_RE.match(code.strip())
    return m.group(1) if m else code


def _truncate(text: str, cap: int = _LONGREPR_CAP) -> str:
    text = (text or "").strip()
    if len(text) > cap:
        return text[:cap] + "...[truncated]"
    return text


class BudgetExhausted(RuntimeError):
    """Raised when a skill tries to call the LLM past the configured budget."""


# ── Feedback ────────────────────────────────────────────────────────────────

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

    fb.next_action = "improve" if fb.has_infrastructure_problems else "done"
    return fb


# ── Per-task state ──────────────────────────────────────────────────────────

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


# ── Pipeline ────────────────────────────────────────────────────────────────

def run_harness(
    cfg: dict,
    repo_dir: str,
    out_dir: str,
    runtime,  # src.runtime.base.Runtime — typed loosely to avoid an import cycle
    *,
    issue_text: str,
    issue_title: str = "",
    hints_text: str = "",
    timeout: int = 60,
    max_llm_calls: int = 8,
    agentic_turn_cap: int = 6,
    per_test_timeout: int | None = None,
) -> dict:
    """Run the issue-driven harness for one (repo, issue) task.

    Returns a persist-ready dict (see `finalize`).
    """
    # Lazy skill import — skills depend on HarnessContext defined above; importing
    # them at module top-level can re-enter on package init.
    from src.skills.analyze import AnalyzeSkill
    from src.skills.generate import GenerateSkill
    from src.skills.improve import ImproveSkill

    if not issue_text or not issue_text.strip():
        raise ValueError("run_harness requires non-empty issue_text")

    test_dir = os.path.join(out_dir, "tests")

    ctx = HarnessContext(
        repo_dir=repo_dir,
        test_dir=test_dir,
        cfg=cfg,
        timeout=timeout,
        per_test_timeout=per_test_timeout,
        runtime=runtime,
        llm_budget=max_llm_calls,
        issue_text=issue_text,
        issue_title=issue_title,
        hints_text=hints_text,
        agentic_turn_cap=agentic_turn_cap,
    )

    print(f"  [harness] budget={max_llm_calls} LLM calls, "
          f"agentic_cap={agentic_turn_cap}")

    # 1. Analyze — single LLM call, builds a structured test plan from the issue.
    try:
        AnalyzeSkill().run(ctx)
    except BudgetExhausted:
        return finalize(ctx)
    except Exception as e:
        print(f"  [harness] analyze error: {type(e).__name__}: {e} — proceeding without plan")
        traceback.print_exc()

    # 2. Generate — agentic. Agent explores via tools, writes test file, exits
    # when it emits a final reply with no tool calls. The skill itself runs
    # write_test_file as part of its loop (via the run_generated_tests tool's
    # pre-commit check); it returns the final candidate so the harness can
    # ensure it's persisted.
    try:
        final_code = GenerateSkill().run(ctx)
        ctx.write_test_file(final_code)
    except BudgetExhausted:
        return finalize(ctx)
    except ValueError as e:
        print(f"  [harness] generate produced empty code: {e}")
        return finalize(ctx)
    except Exception as e:
        print(f"  [harness] generate error: {type(e).__name__}: {e}")
        traceback.print_exc()
        return finalize(ctx)

    # 3. Execute → Feedback
    feedback = _execute_and_feedback(ctx)
    ctx.last_feedback = feedback
    print(f"  [harness] after generate: next_action={feedback.next_action}  "
          f"failures={len(feedback.failures)}  errors={len(feedback.errors)}  "
          f"collection={len(feedback.collection_problems)}  "
          f"timeouts={len(feedback.timeouts)}")

    # 4. Optional Improve fallback. Only fires when the test file's
    # infrastructure is broken (collection / setup error / timeout) AND we
    # still have budget. One pass — if it doesn't fix things, we accept
    # whatever we have.
    if feedback.next_action == "improve" and ctx.llm_calls_used < ctx.llm_budget:
        try:
            improved = ImproveSkill().run(ctx)
            ctx.write_test_file(improved)
            feedback = _execute_and_feedback(ctx)
            ctx.last_feedback = feedback
            print(f"  [harness] after improve: next_action={feedback.next_action}  "
                  f"failures={len(feedback.failures)}  errors={len(feedback.errors)}  "
                  f"collection={len(feedback.collection_problems)}  "
                  f"used={ctx.llm_calls_used}/{ctx.llm_budget}")
        except BudgetExhausted:
            pass
        except ValueError as e:
            print(f"  [harness] improve produced empty code: {e}")
        except Exception as e:
            print(f"  [harness] improve error: {type(e).__name__}: {e}")
            traceback.print_exc()

    return finalize(ctx)


def _execute_and_feedback(ctx: HarnessContext) -> Feedback:
    """Run pytest, build Feedback. No mutation, no in-loop coverage."""
    if not os.path.isfile(ctx.test_file_path):
        return build_feedback(
            {"passed": [], "failed": [], "errors": ["__missing__"],
             "error_details": [{"nodeid": "__missing__", "longrepr": "agent never wrote a test file"}]}
        )

    run_result = _pytest_run(
        ctx.test_file_path, ctx.repo_dir, ctx.runtime,
        timeout=ctx.timeout, per_test_timeout=ctx.per_test_timeout,
    )
    return build_feedback(run_result)


def finalize(ctx: HarnessContext) -> dict:
    """Build the persist-ready dict the agent returns.

    Reads `ctx.last_feedback` set by `_execute_and_feedback`. The only case
    it's None is an early exit before any test code was written. F→P labels
    are computed post-hoc by `src/oracle.py::grade_with_oracle`.
    """
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
