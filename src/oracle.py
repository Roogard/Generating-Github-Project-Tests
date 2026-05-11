"""SWT-bench oracle: classify pytest results and run buggy↔fixed transitions.

Called POST-HOC by `grade_with_oracle` (below) after the agent finishes.
Never runs inside the harness loop — F→P / F→F / P→F / P→P labels are pure
reporting and don't drive any decisions.

Protocol (git-patch based):
  1. Assume repo_dir is in the buggy state (base_commit, no patch applied).
  2. Run tests → buggy_result.
  3. `git apply <gold_patch>` → fixed state.
  4. Run tests → fixed_result.
  5. `git apply -R <gold_patch>` → restore buggy state.

For SwtBenchRuntime the patch is applied via `runtime.set_active_patch` so
the runtime's per-exec preamble re-applies it before each pytest. For
LocalRuntime / generic DockerRuntime the patch is host-applied via
subprocess directly.
"""
from __future__ import annotations

import os
import subprocess
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Iterator

from src.logging import get_logger
from src.runtime.base import Runtime
from src.test_runner import run_tests as _pytest_run
from src.types import AgentResult, AgentTask, OracleGrade


logger = get_logger(__name__)


def _name_only(test_nodeid: str) -> str:
    return test_nodeid.split("::")[-1]


def classify_test_result(result: dict) -> tuple[set[str], set[str], set[str], set[str]]:
    """Classify a pytest result for SWT-bench oracle labeling.

    Returns (passed, failed_or_errored, timed_out, real_errors) — all sets of
    bare test names.
    """
    passed = {_name_only(n) for n in result.get("passed", [])}
    failed = {_name_only(n) for n in result.get("failed", [])}
    real_errors = {_name_only(n) for n in result.get("errors", [])
                   if not n.startswith("__")}
    timed_out = {_name_only(n) for n in result.get("timed_out", [])}
    return passed, failed | real_errors, timed_out, real_errors


@dataclass
class OracleResult:
    f2p: int
    f2f: int
    p2f: int
    p2p: int
    labels: list[tuple[str, str]] = field(default_factory=list)
    buggy_run: dict = field(default_factory=dict)
    fixed_run: dict = field(default_factory=dict)

    @property
    def detected(self) -> bool:
        return self.f2p > 0

    @property
    def resolved(self) -> bool:
        return self.f2p > 0 and self.f2f == 0 and self.p2f == 0


@contextmanager
def _apply_via_git_patch(repo_dir: str, runtime: Runtime, gold_patch: str) -> Iterator[bool]:
    """Flip the source from buggy to fixed for the duration of the `with` block.

    Writes the patch to a runtime-visible tempfile and tells the runtime to
    `set_active_patch`. For runtimes whose source lives on a mounted volume
    (Local, generic Docker user-repo path), `set_active_patch` is a no-op
    and we apply directly via host subprocess — the change is visible to
    pytest immediately because the file lives on disk.

    For SwtBenchRuntime, `set_active_patch` stashes the patch path; each
    subsequent `runtime.exec` re-applies it inside the container at /testbed
    BEFORE the actual command. Necessary because every `docker run --rm` is
    stateless; a host-side `git apply` against `repo_dir` (which is the
    parallel host clone, NOT what /testbed sees) has zero effect on what
    the image-side pytest imports.
    """
    # Always write the patch to a runtime-visible tempfile so SwtBench can
    # use it. For host-apply paths we'll convert to a host path below.
    patch_host = runtime.tempfile_path(suffix=".patch")
    try:
        with open(patch_host, "w", encoding="utf-8", newline="") as f:
            f.write(gold_patch)
            if not gold_patch.endswith("\n"):
                f.write("\n")

        # Detect: does this runtime support stateful patching? If yes, use
        # it. If no, fall back to host-side git apply (legacy behavior for
        # LocalRuntime / generic DockerRuntime user-repo path).
        from src.runtime.swtbench import SwtBenchRuntime
        if isinstance(runtime, SwtBenchRuntime):
            runtime.set_active_patch(runtime.translate(patch_host))
            try:
                yield True
            finally:
                runtime.set_active_patch(None)
        else:
            apply = subprocess.run(
                ["git", "-C", repo_dir, "apply", "--whitespace=nowarn", patch_host],
                capture_output=True, text=True,
            )
            if apply.returncode != 0:
                logger.warning("oracle.git_apply_failed",
                               stderr=apply.stderr.strip()[:300])
                yield False
                return
            try:
                yield True
            finally:
                revert = subprocess.run(
                    ["git", "-C", repo_dir, "apply", "-R", "--whitespace=nowarn", patch_host],
                    capture_output=True, text=True,
                )
                if revert.returncode != 0:
                    logger.warning("oracle.git_revert_failed",
                                   stderr=revert.stderr.strip()[:200],
                                   action="hard_reset")
                    subprocess.run(["git", "-C", repo_dir, "checkout", "--", "."],
                                   capture_output=True)
    finally:
        try:
            os.remove(patch_host)
        except OSError:
            pass


def run_oracle(
    benchmark_context: dict,
    test_file_path: str,
    repo_dir: str,
    runtime: Runtime,
    *,
    timeout: int,
    per_test_timeout: int | None,
) -> OracleResult:
    """Run tests against buggy and fixed versions, return labeled transitions.

    `benchmark_context` must contain `gold_patch` (a unified diff string).
    """
    if "gold_patch" not in benchmark_context:
        raise ValueError("benchmark_context must have 'gold_patch'")

    buggy_result = _pytest_run(
        test_file_path, repo_dir, runtime,
        timeout=timeout, per_test_timeout=per_test_timeout,
    )

    apply_cm = _apply_via_git_patch(repo_dir, runtime, benchmark_context["gold_patch"])
    with apply_cm as applied:
        if not applied:
            return OracleResult(
                f2p=0, f2f=0, p2f=0, p2p=0,
                labels=[], buggy_run=buggy_result, fixed_run={},
            )

        fixed_result = _pytest_run(
            test_file_path, repo_dir, runtime,
            timeout=timeout, per_test_timeout=per_test_timeout,
        )

    return _label_transitions(buggy_result, fixed_result)


def _label_transitions(buggy_result: dict, fixed_result: dict) -> OracleResult:
    buggy_passed, buggy_fail_or_err, buggy_timeouts, buggy_errs = classify_test_result(buggy_result)
    fixed_passed, fixed_fail_or_err, _, _ = classify_test_result(fixed_result)

    all_names = buggy_passed | buggy_fail_or_err | fixed_passed | fixed_fail_or_err
    f2p = f2f = p2p = p2f = 0
    labels: list[tuple[str, str]] = []
    for name in sorted(all_names):
        on_buggy_fail = name in buggy_fail_or_err
        on_buggy_pass = name in buggy_passed
        on_fixed_fail = name in fixed_fail_or_err
        on_fixed_pass = name in fixed_passed

        if on_buggy_fail:
            if name in buggy_timeouts:
                why_buggy = "timeout"
            elif name in buggy_errs:
                why_buggy = "error"
            else:
                why_buggy = "fail"
        else:
            why_buggy = ""

        if on_buggy_fail and on_fixed_pass:
            label = f"F→P (DETECTS BUG via {why_buggy} on buggy — KEEP)"
            f2p += 1
        elif on_buggy_fail and on_fixed_fail:
            label = "F→F (SPURIOUS — fails on both; delete or weaken)"
            f2f += 1
        elif on_buggy_pass and on_fixed_pass:
            label = "P→P (stable neutral)"
            p2p += 1
        elif on_buggy_pass and on_fixed_fail:
            label = "P→F (REGRESSION — breaks on fixed; remove)"
            p2f += 1
        else:
            label = "?"
        labels.append((name, label))

    return OracleResult(
        f2p=f2p, f2f=f2f, p2f=p2f, p2p=p2p,
        labels=labels, buggy_run=buggy_result, fixed_run=fixed_result,
    )


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
        logger.error("oracle.grade_failed", err_type=type(e).__name__, err=str(e))
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
