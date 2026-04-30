"""Single persistence path for the issue-driven architecture.

The runner calls these once per (Run, AgentTask, AgentResult, OracleGrade)
tuple. No conditional code paths based on input source — every run goes
through the same write.

Three functions:
  - `persist_run_start(run_metadata)` — creates a Run row.
  - `persist_function_result(run_id, task, result, oracle_grade)` — appends
    one Function row + writes oracle grade to the Run.
  - `persist_run_end(run_id, status, ...)` — finalizes the Run.
"""
from __future__ import annotations

from datetime import datetime

from api.models import RunStatus
from api.store import (
    create_run as _store_create_run,
    finalize_run as _store_finalize_run,
    save_function_result as _store_save_function_result,
    session_scope,
    update_run as _store_update_run,
)
from src.types import AgentResult, AgentTask, OracleGrade


def persist_run_start(run_metadata: dict) -> int:
    """Create a Run row in RUNNING state. Returns the run_id.

    `run_metadata` keys are pulled selectively — extra adapter-internal
    keys (e.g. `runtime`, `_install_error`) are ignored here.
    """
    fields = {
        "repo_url": run_metadata.get("repo_url", ""),
        "mode": run_metadata.get("mode", "repo"),
        "dataset": run_metadata.get("dataset"),
        "benchmark_id": run_metadata.get("benchmark_id"),
        "provider": run_metadata.get("provider"),
        "model": run_metadata.get("model"),
        "preset": run_metadata.get("preset"),
        "status": RunStatus.RUNNING,
    }
    with session_scope() as db:
        run = _store_create_run(db, **fields)
        db.flush()
        return run.id


def persist_function_result(
    run_id: int,
    task: AgentTask,
    result: AgentResult,
    oracle_grade: OracleGrade | None,
) -> None:
    """Append one Function row and write oracle grade onto the Run."""
    with session_scope() as db:
        fn_dict = {
            "fn_name": task.label or task.instance_id or "issue",
            "test_code": result.test_code or None,
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "history": result.history,
        }
        _store_save_function_result(db, run_id, fn_dict)

        update_kwargs = {
            "tests_passed": result.tests_passed,
            "tests_failed": result.tests_failed,
            "tests_run": result.tests_run,
        }

        # Oracle grade — only present when the task carried a gold patch.
        if oracle_grade is not None:
            update_kwargs.update({
                "f2p": oracle_grade.f2p,
                "f2f": oracle_grade.f2f,
                "p2f": oracle_grade.p2f,
                "p2p": oracle_grade.p2p,
                "detected": oracle_grade.detected,
                "resolved": oracle_grade.resolved,
                "patch_applied": True,
            })

        _store_update_run(db, run_id, **update_kwargs)


def persist_run_end(
    run_id: int,
    *,
    status: str = RunStatus.DONE,
    error_message: str | None = None,
    output_dir: str | None = None,
    elapsed_seconds: float | None = None,
) -> None:
    """Mark the Run as finished. Recomputes Run-level totals one final time."""
    with session_scope() as db:
        update_kwargs = {
            "status": status,
            "finished_at": datetime.utcnow(),
            "current_stage": None,  # always clear stage on terminal status
        }
        if error_message is not None:
            update_kwargs["error_message"] = error_message[:2000]
        if output_dir is not None:
            update_kwargs["output_dir"] = output_dir
        if elapsed_seconds is not None:
            update_kwargs["elapsed_seconds"] = round(elapsed_seconds, 1)
        _store_update_run(db, run_id, **update_kwargs)
        _store_finalize_run(db, run_id)


def update_run_progress(run_id: int, *, current: int, total: int) -> None:
    """Tick progress counters during a multi-task batch."""
    with session_scope() as db:
        _store_update_run(db, run_id,
                          progress_current=current, progress_total=total)


def update_run_stage(run_id: int, stage: str | None) -> None:
    """Record the live pipeline stage. Pass `None` when the pipeline finishes
    so the polling client knows the harness is no longer mid-stage. Called
    by the harness at each skill boundary; safe to call frequently — the DB
    write is one short UPDATE.
    """
    with session_scope() as db:
        _store_update_run(db, run_id, current_stage=stage)
