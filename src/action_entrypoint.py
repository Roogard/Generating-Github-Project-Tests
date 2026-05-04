"""GitHub Action entrypoint.

Invoked by the published reusable workflow at
[.github/workflows/ggpt.yml](.github/workflows/ggpt.yml). Reads the
issue/comment that triggered the workflow, dispatches to a mode handler
(`test` today; `fix`/`refactor` later), runs the agent against the
already-checked-out repo, and emits `$GITHUB_OUTPUT` lines that
downstream workflow steps consume to commit + open the PR.

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
import sys
import traceback
from dataclasses import dataclass
from typing import Callable

from src.agent import run_agent
from src.inputs.base import PRESETS
from src.inputs.repo import _setup_runtime
from src.llm import build_config
from src.logging import configure_logging, get_logger
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


# ── output channel ──────────────────────────────────────────────────────────

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


# ── trigger parsing ─────────────────────────────────────────────────────────

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


# ── provider selection ─────────────────────────────────────────────────────

def _pick_provider() -> tuple[str, str] | None:
    """Return (provider_name, api_key) for the first provider with a
    non-empty env var. `None` if no key is set.
    """
    for name, env_var in _PROVIDER_KEYS:
        key = os.environ.get(env_var, "").strip()
        if key:
            return name, key
    return None


# ── mode handlers ──────────────────────────────────────────────────────────

def _run_test_mode(trigger: Trigger, workspace: str) -> str | None:
    """Generate a regression test from the issue. Returns the
    workspace-relative path of the written test on success, `None` on
    any failure.
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

    try:
        result = run_agent(task)
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
    return rel_path


_MODE_HANDLERS: dict[str, Callable[[Trigger, str], str | None]] = {
    "test": _run_test_mode,
    # 'fix', 'refactor', etc. — register handlers here. Adopter workflow
    # already routes the labels and slash-commands; only this dict needs
    # to grow.
}


# ── main ───────────────────────────────────────────────────────────────────

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
        rel_path = handler(trigger, workspace)
    except Exception as e:
        logger.error("entrypoint.handler_crashed",
                     mode=trigger.mode,
                     err_type=type(e).__name__, err=str(e),
                     traceback=traceback.format_exc())
        return 0

    if not rel_path:
        return 0

    _emit("changed_path",   rel_path)
    _emit("branch",         f"ggpt/issue-{trigger.target_number}")
    _emit("commit_message", f"Add regression test for #{trigger.target_number}")
    _emit("pr_title",       f"GGPT: regression test for #{trigger.target_number}")
    _emit("pr_body",
          f"Closes #{trigger.target_number}\n\nAuto-generated by GGPT.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
