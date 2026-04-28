"""Top-level harness pipeline (issue-driven).

Loop:
  Analyze → Generate (agentic) → Execute → maybe Improve once → Finalize

The harness owns side effects (file writes, pytest invocation). Skills are
LLM calls — Analyze and Improve are single-call, Generate is agentic with
tool use.

Signal: pytest only.
  - Collection / setup / timeout problems → Improve once (fallback only)
  - Otherwise → done

Pytest assertion failures are NOT improve signals — they may be the F→P
detections we want. The post-hoc oracle grader (`src/graders/oracle.py`)
labels F→P / F→F / P→F / P→P after run_agent returns; the harness has no
benchmark awareness.
"""
from __future__ import annotations

import os
import traceback
from pathlib import Path

from src.harness.context import BudgetExhausted, HarnessContext
from src.harness.feedback import Feedback, build_feedback
from src.harness.finalize import finalize
from src.test_runner import run_tests as _pytest_run


_DEFAULT_EXAMPLES_DIR = Path(__file__).resolve().parent.parent / "examples" / "golden"


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
    examples_dir: Path | None = None,
) -> dict:
    """Run the issue-driven harness for one (repo, issue) task.

    Returns a persist-ready dict (see `finalize`).
    """
    # Lazy skill import — skills depend on HarnessContext, which is defined
    # next to this module; importing them at top-level can re-enter on package init.
    from src.skills import AnalyzeSkill, GenerateSkill, ImproveSkill

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
        examples_dir=examples_dir or _DEFAULT_EXAMPLES_DIR,
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
