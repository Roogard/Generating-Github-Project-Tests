"""The Analyze → Generate → maybe Improve(infra) → Critique → maybe Improve(semantic) → Finalize pipeline.

The harness owns side effects (file writes, pytest invocation). Skills are
LLM calls — Analyze and Critique are single-call, Generate and Improve are
agentic (tool-using).

Lazy skill import (inside `run_harness`) is deliberate: skills depend on
`HarnessContext` (defined in `src.harness.state`), and the harness drives
skills. Importing the skills at module top-level here would mean both
modules want each other at import time, which works in CPython today but
is fragile to package-init ordering changes. Keep the imports inside the
function — they're the one-way arrow that makes the dependency safe.
"""
from __future__ import annotations

import os
import traceback
from pathlib import Path

from src.harness.feedback import Feedback, build_feedback
from src.harness.state import (
    BudgetExhausted,
    HarnessContext,
    read_test_file,
    write_test_file,
)
from src.logging import get_logger
from src.test_runner import run_tests as _pytest_run


logger = get_logger(__name__)


def run_harness(
    cfg: dict,
    repo_dir: str,
    out_dir: str,
    runtime,  # src.runtime.base.Runtime — typed loosely to avoid an import cycle
    *,
    run_id: int | None = None,
    issue_text: str,
    issue_title: str = "",
    hints_text: str = "",
    timeout: int = 60,
    max_llm_calls: int = 8,
    agentic_turn_cap: int = 6,
    per_test_timeout: int | None = None,
) -> dict:
    """Run the issue-driven harness for one (repo, issue) task.

    `run_id` (optional): when provided, the harness emits live pipeline-stage
    updates against the matching Run row so the webapp can display
    'Generating' / 'Critiquing' / etc. while polling.

    Returns a persist-ready dict (see `finalize`).
    """
    # Lazy skill import — see module docstring. Skills depend on HarnessContext
    # (state.py); harness drives skills. The arrow goes one way only.
    from src.skills.analyze import AnalyzeSkill
    from src.skills.critique import CritiqueSkill
    from src.skills.generate import GenerateSkill
    from src.skills.improve import ImproveSkill

    def _stage(name: str | None) -> None:
        """Record the live pipeline stage. No-op when run_id is None
        (e.g. direct test invocations without a DB row)."""
        if run_id is None:
            return
        try:
            from src.persist import update_run_stage
            update_run_stage(run_id, name)
        except Exception as e:
            # Stage updates are diagnostic — don't let a DB hiccup
            # break the harness. Log and continue.
            logger.warning("harness.stage_update_failed",
                           err_type=type(e).__name__, err=str(e))

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

    logger.info("harness.start", budget=max_llm_calls, agentic_cap=agentic_turn_cap)

    # 1. Analyze — single LLM call, builds a structured test plan from the issue.
    _stage("analyze")
    try:
        AnalyzeSkill().run(ctx)
    except BudgetExhausted:
        _stage(None)
        return finalize(ctx)
    except Exception as e:
        logger.warning("harness.analyze_error", err_type=type(e).__name__, err=str(e),
                       traceback=traceback.format_exc(), action="proceed_without_plan")

    # 2. Generate — agentic. Agent explores via tools (Glob/Grep/Read) and
    # writes the test file via Write/Edit; the harness auto-runs pytest after
    # any modification to ctx.test_file_path. The skill returns the final
    # candidate so the harness can ensure it's persisted (covers the case
    # where the agent emitted code only in its final message instead of via
    # a tool call).
    _stage("generate")
    try:
        final_code = GenerateSkill().run(ctx)
        write_test_file(ctx, final_code)
    except BudgetExhausted:
        _stage(None)
        return finalize(ctx)
    except ValueError as e:
        logger.warning("harness.generate_empty", err=str(e))
        _stage(None)
        return finalize(ctx)
    except Exception as e:
        logger.error("harness.generate_error", err_type=type(e).__name__, err=str(e),
                     traceback=traceback.format_exc())
        _stage(None)
        return finalize(ctx)

    # 3. Execute → Feedback
    feedback = _execute_and_feedback(ctx)
    ctx.last_feedback = feedback
    logger.info("harness.after_generate",
                next_action=feedback.next_action,
                failures=len(feedback.failures),
                errors=len(feedback.errors),
                collection_problems=len(feedback.collection_problems),
                timeouts=len(feedback.timeouts))

    # 4. Optional Improve fallback. Only fires when the test file's
    # infrastructure is broken (collection / setup error / timeout) AND we
    # still have budget. One pass — if it doesn't fix things, we accept
    # whatever we have.
    if feedback.next_action == "improve" and ctx.llm_calls_used < ctx.llm_budget:
        _stage("improve_infra")
        try:
            improved = ImproveSkill().run(ctx)
            write_test_file(ctx, improved)
            feedback = _execute_and_feedback(ctx)
            ctx.last_feedback = feedback
            logger.info("harness.after_improve_infra",
                        next_action=feedback.next_action,
                        failures=len(feedback.failures),
                        errors=len(feedback.errors),
                        collection_problems=len(feedback.collection_problems),
                        used=ctx.llm_calls_used, budget=ctx.llm_budget)
        except BudgetExhausted:
            pass
        except ValueError as e:
            logger.warning("harness.improve_empty", err=str(e))
        except Exception as e:
            logger.error("harness.improve_error", err_type=type(e).__name__, err=str(e),
                         traceback=traceback.format_exc())

    # 5. Critique — single LLM call. Predicts F→P / F→F / P→F / P→P from the
    # final test + pytest result. Persisted to ctx.last_critique and
    # ctx.attempts. Skipped if there's no test file or no remaining budget.
    if os.path.isfile(ctx.test_file_path) and ctx.llm_calls_used < ctx.llm_budget:
        _stage("critique")
        try:
            CritiqueSkill().run(ctx)
            crit = ctx.last_critique or {}
            logger.info("harness.after_critique",
                        predicted=crit.get("expected_transition"),
                        confidence=crit.get("confidence"),
                        needs_revision=crit.get("needs_revision"),
                        used=ctx.llm_calls_used, budget=ctx.llm_budget)
        except BudgetExhausted:
            pass
        except Exception as e:
            logger.warning("harness.critique_error", err_type=type(e).__name__, err=str(e),
                           traceback=traceback.format_exc(), action="skip_critique")

    # 6. Critique-driven Improve. If Critique predicted a non-F2P outcome
    # and flagged needs_revision, fire Improve in semantic mode — the agent
    # gets the critique's concerns + revision_focus and may re-explore the
    # repo before patching. Gated on remaining budget (need at least a few
    # turns' headroom — skip if budget is too tight).
    crit = ctx.last_critique or {}
    budget_remaining = ctx.llm_budget - ctx.llm_calls_used
    if (crit.get("needs_revision")
            and budget_remaining >= 2  # at minimum: one tool turn + one final
            and os.path.isfile(ctx.test_file_path)):
        # ImproveSkill picks mode from ctx state. Clear last_feedback's
        # infrastructure-problem signal so it routes to semantic mode (the
        # critique-driven path), not infrastructure.
        _stage("improve_semantic")
        prior_feedback = ctx.last_feedback
        ctx.last_feedback = None
        try:
            improved = ImproveSkill().run(ctx)
            write_test_file(ctx, improved)
            # Re-execute pytest so finalize sees the post-improve result.
            ctx.last_feedback = _execute_and_feedback(ctx)
            logger.info("harness.after_improve_semantic",
                        failures=len(ctx.last_feedback.failures),
                        errors=len(ctx.last_feedback.errors),
                        used=ctx.llm_calls_used, budget=ctx.llm_budget)
        except BudgetExhausted:
            ctx.last_feedback = prior_feedback
        except ValueError as e:
            logger.warning("harness.critique_improve_empty", err=str(e))
            ctx.last_feedback = prior_feedback
        except Exception as e:
            logger.error("harness.critique_improve_error",
                         err_type=type(e).__name__, err=str(e),
                         traceback=traceback.format_exc())
            ctx.last_feedback = prior_feedback

    _stage(None)
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
    # Stash the pytest invocation in history so the actual stdout/stderr is
    # recoverable from the DB. Without this, "0 tests run" outcomes can only
    # be diagnosed from API-server scrollback. Tail-truncated to keep
    # history_json from ballooning.
    ctx.attempts.append({
        "skill": "_pytest_run",
        "returncode": run_result.get("returncode"),
        "passed": list(run_result.get("passed") or []),
        "failed": list(run_result.get("failed") or []),
        "errors": list(run_result.get("errors") or []),
        "stdout_tail": (run_result.get("stdout") or "")[-3000:],
        "stderr_tail": (run_result.get("stderr") or "")[-1500:],
    })
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
        "critique": ctx.last_critique,
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


# `read_test_file` re-exported here so callers that previously did
# `ctx.read_test_file()` and now do `read_test_file(ctx)` have a stable
# import path inside the harness package.
__all__ = ["run_harness", "finalize", "read_test_file"]
