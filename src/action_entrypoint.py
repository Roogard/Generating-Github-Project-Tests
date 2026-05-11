"""GitHub Action entrypoint.

Invoked by the published reusable workflow at
[.github/workflows/ggpt.yml](.github/workflows/ggpt.yml). Reads the
issue/comment that triggered the workflow, dispatches to a mode handler,
runs the agent against the already-checked-out repo, and emits
`$GITHUB_OUTPUT` lines that downstream workflow steps consume to commit
+ open the PR.

Modes (selected by the label suffix, or `/ggpt <mode>` comment):
  test   — generate a regression test for the issue.            (label: ggpt or ggpt-test)
  fix    — generate the test, then propose a source-code fix    (label: ggpt-fix)
           and ship both in the PR. Fix is verified by re-running
           the test; if the test still fails after the proposed
           edits, the fix is reverted and the PR ships test-only.

Workflow contract
=================

Inputs (env):
  GGPT_RUNTIME=local
  GITHUB_WORKSPACE      caller's repo, already cloned by actions/checkout
  GITHUB_EVENT_PATH     JSON payload from the triggering event
  GITHUB_EVENT_NAME     'issues' | 'issue_comment'
  GITHUB_OUTPUT         file we append k=v pairs to
  RUNNER_TEMP           per-job scratch dir
  GGPT_MODEL            optional LLM model override
  At least one of: DEEPSEEK_API_KEY, ANTHROPIC_API_KEY, OPENAI_API_KEY

Outputs (`$GITHUB_OUTPUT`):
  target_number    issue/PR number — set as soon as known
  changed_path     workspace-relative path of the new file (success only)
  branch           branch name peter-evans should push to
  commit_message   commit subject
  pr_title         PR title
  pr_body          PR body

Exit code is always 0 unless something catastrophic happens. Failure is
signalled by `target_number` being set with `changed_path` empty — the
workflow's failure step reads those outputs to comment on the issue
with a logs link.

Adding new modes
================

Register a handler in `_MODE_HANDLERS`. The dispatcher already routes
labels (`ggpt-<mode>`) and slash-commands (`/ggpt <mode>`) to the
matching key — adopters never need to update their workflow file.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass
from typing import Callable

from src.agent import run_agent
from src.harness import BudgetExhausted, HarnessContext
from src.inputs.base import PRESETS
from src.inputs.repo import _setup_runtime
from src.llm import build_config
from src.logging import configure_logging, get_logger
from src.test_runner import run_tests
from src.types import AgentTask


logger = get_logger(__name__)

# First provider with a non-empty key wins. Order = preference.
_PROVIDER_KEYS: tuple[tuple[str, str], ...] = (
    ("deepseek",  "DEEPSEEK_API_KEY"),
    ("anthropic", "ANTHROPIC_API_KEY"),
    ("openai",    "OPENAI_API_KEY"),
)


@dataclass
class Trigger:
    event_name: str        # 'issues' | 'issue_comment'
    mode: str              # 'test' | 'fix' | ...
    target_number: int     # issue/PR number
    issue_title: str
    issue_body: str


def _emit(key: str, value: str) -> None:
    """Append a `key=value` line to `$GITHUB_OUTPUT`. Multi-line values
    use the heredoc form documented at:
    https://docs.github.com/en/actions/using-workflows/workflow-commands-for-github-actions#multiline-strings
    """
    out_path = os.environ.get("GITHUB_OUTPUT")
    if not out_path:
        # Local smoke test — print to stdout so a developer can see what
        # would have been emitted.
        print(f"::output:: {key}={value!r}")
        return
    if "\n" in value:
        delim = "GGPT_EOF"
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"{key}<<{delim}\n{value}\n{delim}\n")
    else:
        with open(out_path, "a", encoding="utf-8") as f:
            f.write(f"{key}={value}\n")


def _parse_trigger() -> Trigger | None:
    """Read `$GITHUB_EVENT_PATH` and figure out what to do.

    The caller workflow's `if:` filter screens out irrelevant events; we
    re-check here so the entrypoint is independently sane (and so local
    smoke tests don't need a matching wrapper).
    """
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path or not os.path.isfile(event_path):
        logger.error("entrypoint.no_event_path", path=event_path)
        return None

    with open(event_path, "r", encoding="utf-8") as f:
        event = json.load(f)

    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    issue = event.get("issue") or {}
    title = issue.get("title", "") or ""
    body = issue.get("body", "") or ""
    number = issue.get("number")
    if not isinstance(number, int):
        logger.error("entrypoint.no_issue_number", event_name=event_name)
        return None

    if event_name == "issues":
        label_name = ((event.get("label") or {}).get("name") or "").strip()
        if not label_name.startswith("ggpt"):
            return None
        # 'ggpt' or 'ggpt-test' → test (default). 'ggpt-fix' → fix.
        suffix = label_name[len("ggpt"):].lstrip("-")
        mode = (suffix or "test").lower()
        return Trigger(event_name, mode, number, title, body)

    if event_name == "issue_comment":
        comment_body = ((event.get("comment") or {}).get("body") or "").strip()
        if not comment_body.startswith("/ggpt"):
            return None
        # '/ggpt' → test, '/ggpt fix [...]' → fix
        parts = comment_body.split(maxsplit=2)
        mode = (parts[1].strip().lower() if len(parts) >= 2 else "test")
        return Trigger(event_name, mode, number, title, body)

    return None



def _pick_provider() -> tuple[str, str] | None:
    """Return (provider_name, api_key) for the first provider with a
    non-empty env var. `None` if no key is set.
    """
    for name, env_var in _PROVIDER_KEYS:
        key = os.environ.get(env_var, "").strip()
        if key:
            return name, key
    return None


@dataclass
class ModeResult:
    """What a mode handler returns to `main`. The action emits one PR with
    the test plus any source files the (optional) fix step modified.
    """
    test_rel_path: str
    fix_rel_paths: list[str]
    fix_applied: bool



def _propose_and_apply_fix(ctx: HarnessContext, workspace: str) -> tuple[list[str], bool]:
    """Run ProposeFixSkill, verify by re-running pytest, return changed
    source paths + whether the fix was kept.

    Only attempted when:
      - The harness produced a test file that pytest could run.
      - At least one test failed on the buggy code (i.e. the test reproduces
        the bug — F→P signal is real and we have something to fix).
      - There's enough llm_budget headroom for an agentic loop.

    On any failure (skill error, pytest still failing after the edits, or
    no edits at all), reverts source-file changes via `git checkout -- .`
    so the PR ships test-only.
    """
    from src.skills.propose_fix import ProposeFixSkill

    fb = ctx.last_feedback
    if fb is None or not fb.failures:
        logger.info("entrypoint.fix_skipped", reason="no_test_failure_to_fix")
        return [], False

    if ctx.llm_budget - ctx.llm_calls_used < 3:
        logger.info("entrypoint.fix_skipped", reason="budget_exhausted",
                    used=ctx.llm_calls_used, budget=ctx.llm_budget)
        return [], False

    try:
        ProposeFixSkill().run(ctx)
    except BudgetExhausted:
        logger.info("entrypoint.fix_skipped", reason="budget_exhausted_mid_skill")
        _revert_source_edits(workspace)
        return [], False
    except Exception as e:
        logger.error("entrypoint.fix_skill_error",
                     err_type=type(e).__name__, err=str(e),
                     traceback=traceback.format_exc())
        _revert_source_edits(workspace)
        return [], False

    # Verify: re-run the test against the modified source.
    verify = run_tests(
        ctx.test_file_path, ctx.repo_dir, ctx.runtime,
        timeout=ctx.timeout, per_test_timeout=ctx.per_test_timeout,
    )
    passed = len(verify.get("passed") or [])
    failed = len(verify.get("failed") or [])
    real_errors = len([e for e in (verify.get("errors") or []) if not e.startswith("__")])
    fix_works = passed > 0 and failed == 0 and real_errors == 0

    if not fix_works:
        logger.info("entrypoint.fix_verification_failed",
                    passed=passed, failed=failed, errors=real_errors)
        _revert_source_edits(workspace)
        return [], False

    changed = _git_diff_paths(workspace)
    if not changed:
        # The skill said "done" without actually editing anything. Rare but
        # possible. Treat as no fix applied.
        logger.info("entrypoint.fix_skipped", reason="skill_made_no_edits")
        return [], False

    logger.info("entrypoint.fix_applied", changed_count=len(changed))
    return changed, True


def _git_diff_paths(workspace: str) -> list[str]:
    """Workspace-relative paths of files modified vs HEAD. Untracked files
    (e.g. the to-be-copied test file) are intentionally excluded.
    """
    r = subprocess.run(
        ["git", "-C", workspace, "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, timeout=10, check=False,
    )
    return [line.strip() for line in r.stdout.splitlines() if line.strip()]


def _revert_source_edits(workspace: str) -> None:
    """`git checkout -- .` — undo unstaged source edits so a failed fix
    attempt doesn't leak into the PR.
    """
    subprocess.run(
        ["git", "-C", workspace, "checkout", "--", "."],
        capture_output=True, text=True, timeout=10, check=False,
    )


def _run_mode(trigger: Trigger, workspace: str, *, propose_fix: bool) -> ModeResult | None:
    """Run the agent and return its output paths.

    `propose_fix=False` — generate just a regression test (`ggpt-test`).
    `propose_fix=True`  — generate the test AND a proposed source fix
                          (`ggpt-fix`); the fix is gated on verification.

    Returns `ModeResult` on success, `None` on any setup or run failure.
    """
    if not trigger.issue_body.strip():
        logger.error("entrypoint.empty_issue_body", issue=trigger.target_number)
        return None

    picked = _pick_provider()
    if picked is None:
        logger.error("entrypoint.no_provider_key",
                     looked_for=[k for _, k in _PROVIDER_KEYS])
        return None
    provider, api_key = picked
    cfg = build_config(provider, model=os.environ.get("GGPT_MODEL") or None,
                       api_key=api_key)

    # Scratch dir for the agent's tests/, runtime venv, etc. Kept outside
    # the workspace so we don't pollute the cloned tree with intermediates.
    runner_temp = os.environ.get("RUNNER_TEMP") or os.path.dirname(workspace)
    out_dir = os.path.abspath(os.path.join(runner_temp, "ggpt-run"))
    os.makedirs(out_dir, exist_ok=True)

    # Reuse RepoAdapter's helper to set up a runtime and install repo +
    # pytest packages against the already-checked-out workspace.
    runtime, install_result = _setup_runtime(out_dir, workspace, install_deps=True)
    if install_result is not None and install_result.returncode != 0:
        tail = (install_result.stderr or install_result.stdout).strip().splitlines()[-20:]
        logger.error("entrypoint.install_failed",
                     returncode=install_result.returncode,
                     stderr_tail=[line[:200] for line in tail])
        runtime.shutdown()
        return None

    preset = PRESETS["default"]
    task = AgentTask(
        source="repo",
        label=f"action: issue #{trigger.target_number}",
        repo_dir=workspace,
        runtime=runtime,
        issue_text=trigger.issue_body,
        issue_title=trigger.issue_title,
        cfg=cfg,
        out_dir=out_dir,
        timeout=preset["timeout"],
        max_llm_calls=preset["max_llm_calls"],
        agentic_turn_cap=preset["agentic_turn_cap"],
        per_test_timeout=preset.get("per_test_timeout"),
    )

    # In fix mode, ProposeFixSkill runs inside `run_agent` via the
    # post_finalize hook — that's where the live HarnessContext exists.
    # Closure state carries the outcome back here.
    fix_state: dict = {"paths": [], "applied": False}

    if propose_fix:
        def _post_finalize(ctx: HarnessContext) -> None:
            paths, applied = _propose_and_apply_fix(ctx, workspace)
            fix_state["paths"] = paths
            fix_state["applied"] = applied
        post_finalize = _post_finalize
    else:
        post_finalize = None

    try:
        result = run_agent(task, post_finalize=post_finalize)
    finally:
        runtime.shutdown()

    src_test = os.path.join(out_dir, "tests", "test_agent.py")
    if not os.path.isfile(src_test):
        logger.error("entrypoint.no_test_produced", path=src_test,
                     finish_reason=getattr(result, "finish_reason", None))
        return None

    rel_path = f"tests/test_ggpt_issue_{trigger.target_number}.py"
    dst_abs = os.path.join(workspace, rel_path)
    os.makedirs(os.path.dirname(dst_abs), exist_ok=True)
    shutil.copyfile(src_test, dst_abs)
    return ModeResult(
        test_rel_path=rel_path,
        fix_rel_paths=fix_state["paths"],
        fix_applied=fix_state["applied"],
    )


# Thin wrappers so each mode is its own callable in the dispatcher.
def _run_test_mode(trigger: Trigger, workspace: str) -> ModeResult | None:
    return _run_mode(trigger, workspace, propose_fix=False)


def _run_fix_mode(trigger: Trigger, workspace: str) -> ModeResult | None:
    return _run_mode(trigger, workspace, propose_fix=True)


_MODE_HANDLERS: dict[str, Callable[[Trigger, str], ModeResult | None]] = {
    "test": _run_test_mode,
    "fix":  _run_fix_mode,
    # Add more modes here as they're built. The dispatcher already routes
    # labels (`ggpt-<mode>`) and `/ggpt <mode>` comments to the matching
    # key — adopter workflows don't need updating.
}



def main() -> int:
    configure_logging()

    trigger = _parse_trigger()
    if trigger is None:
        logger.info("entrypoint.no_trigger")
        return 0

    # Always emit target_number first so the failure-comment step has
    # somewhere to land even if the handler crashes mid-flight.
    _emit("target_number", str(trigger.target_number))

    handler = _MODE_HANDLERS.get(trigger.mode)
    if handler is None:
        logger.warning("entrypoint.mode_not_implemented", mode=trigger.mode,
                       known=sorted(_MODE_HANDLERS))
        return 0

    workspace = os.environ.get("GITHUB_WORKSPACE")
    if not workspace or not os.path.isdir(workspace):
        logger.error("entrypoint.no_workspace", path=workspace)
        return 0

    try:
        outcome = handler(trigger, workspace)
    except Exception as e:
        logger.error("entrypoint.handler_crashed",
                     mode=trigger.mode,
                     err_type=type(e).__name__, err=str(e),
                     traceback=traceback.format_exc())
        return 0

    if outcome is None:
        return 0

    # peter-evans/create-pull-request@v6 accepts newline-separated paths in
    # `add-paths`. The test always ships; the fix files only ship if the
    # post-finalize step kept them.
    paths = [outcome.test_rel_path, *outcome.fix_rel_paths]
    _emit("changed_path", "\n".join(paths))
    _emit("branch",       f"ggpt/issue-{trigger.target_number}")

    n = trigger.target_number
    if outcome.fix_applied:
        _emit("commit_message", f"Add regression test + proposed fix for #{n}")
        _emit("pr_title",       f"GGPT: regression test + proposed fix for #{n}")
        _emit("pr_body",
              f"Closes #{n}\n\n"
              f"Auto-generated by GGPT. The test reproduces the issue and the "
              f"proposed source change makes it pass.\n\n"
              f"Files changed: {len(outcome.fix_rel_paths)} source file(s) + "
              f"1 test.")
    elif trigger.mode == "fix":
        # User asked for a fix (ggpt-fix label or /ggpt fix), but the
        # propose-and-verify step couldn't make the test pass.
        _emit("commit_message", f"Add regression test for #{n}")
        _emit("pr_title",       f"GGPT: regression test for #{n} (fix attempt failed)")
        _emit("pr_body",
              f"Closes #{n}\n\n"
              f"Auto-generated by GGPT. A code fix was attempted but did not "
              f"make the test pass — shipping test only.")
    else:
        # Test mode (ggpt or ggpt-test) — fix was never attempted.
        _emit("commit_message", f"Add regression test for #{n}")
        _emit("pr_title",       f"GGPT: regression test for #{n}")
        _emit("pr_body",
              f"Closes #{n}\n\n"
              f"Auto-generated by GGPT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
