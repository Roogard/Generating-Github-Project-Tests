"""Runner — the orchestration layer that ties everything together.

`run_batch(adapter)` iterates over the adapter's `RunBatch` stream. Per
batch:
  1. Create a Run row (PENDING/RUNNING).
  2. For each AgentTask in the batch:
     - run_agent(task) → AgentResult
     - grade_with_oracle(task, result) → OracleGrade | None  (only when gold_patch)
     - persist_function_result(run_id, task, result, oracle_grade)
     - tick progress
  3. Finalize the Run row (DONE/ERROR).
  4. Shut down + clean up the runtime.

Adapter-internal metadata can carry hints the runner uses (e.g.
`_skip_reason` for instances we couldn't even set up, `_install_error` for
dep failures, `_host_root` for SwtBench tempdir cleanup). These are
prefixed with `_` and never written to the DB.
"""
from __future__ import annotations

import shutil
import time

from api.constants import RunStatus
from src.agent import run_agent
from src.graders import grade_with_oracle
from src.inputs.base import InputAdapter, force_rmtree
from src.persist import (
    persist_function_result,
    persist_run_end,
    persist_run_start,
    update_run_progress,
)


def run_batch(
    adapter: InputAdapter,
    *,
    run_id: int | None = None,
) -> list[int]:
    """Run every batch the adapter yields. Returns the list of created run_ids.

    `run_id` (optional): when supplied, the FIRST batch reuses this pre-created
    Run row instead of creating a new one. This matches the API pattern where
    the route handler creates a Run row up-front (so it can return the id
    synchronously) and the background task fills it in.
    """
    created_run_ids: list[int] = []
    pre_created_id = run_id

    for batch in adapter.iter_batches():
        # Allocate the Run row.
        if pre_created_id is not None:
            current_run_id = pre_created_id
            pre_created_id = None
            # Pre-created Run already has provider/model/etc; patch in
            # per-batch fields the API didn't know about (dataset, benchmark_id).
            from api.store import session_scope, update_run as _update
            with session_scope() as db:
                _update(db, current_run_id,
                        dataset=batch.run_metadata.get("dataset"),
                        benchmark_id=batch.run_metadata.get("benchmark_id"),
                        mode=batch.run_metadata.get("mode", "repo"),
                        progress_total=len(batch.tasks),
                        status=RunStatus.RUNNING)
        else:
            current_run_id = persist_run_start(batch.run_metadata)
        created_run_ids.append(current_run_id)

        runtime = batch.run_metadata.get("runtime")
        host_root = batch.run_metadata.get("_host_root")
        output_dir = batch.run_metadata.get("output_dir")
        t_start = time.time()

        try:
            # Adapter-side skip / install-failure cases: empty tasks list.
            skip_reason = (
                batch.run_metadata.get("_install_error")
                or batch.run_metadata.get("_skip_reason")
            )
            if not batch.tasks:
                persist_run_end(
                    current_run_id,
                    status=RunStatus.ERROR,
                    error_message=skip_reason or "no tasks emitted by adapter",
                    output_dir=output_dir,
                    elapsed_seconds=time.time() - t_start,
                )
                continue

            total = len(batch.tasks)
            update_run_progress(current_run_id, current=0, total=total)

            for i, task in enumerate(batch.tasks):
                print(f"\n[{i + 1}/{total}] {task.label}")
                result = run_agent(task)
                oracle_grade = grade_with_oracle(task, result)
                persist_function_result(current_run_id, task, result, oracle_grade)
                update_run_progress(current_run_id, current=i + 1, total=total)

            persist_run_end(
                current_run_id,
                status=RunStatus.DONE,
                output_dir=output_dir,
                elapsed_seconds=time.time() - t_start,
            )
        except Exception as e:
            print(f"  RUNNER ERROR: {type(e).__name__}: {e}")
            persist_run_end(
                current_run_id,
                status=RunStatus.ERROR,
                error_message=f"{type(e).__name__}: {e}",
                output_dir=output_dir,
                elapsed_seconds=time.time() - t_start,
            )
        finally:
            if runtime is not None:
                try:
                    runtime.shutdown()
                except Exception:
                    pass
            # SwtBench adapter creates a per-instance tempdir; clean it.
            if host_root:
                shutil.rmtree(host_root, ignore_errors=True)
            # Repo adapter leaves output_dir/_repo + .venv + tmp around;
            # clean transient artifacts but preserve user-visible tests/.
            if output_dir and not host_root:
                import os as _os
                for sub in ("_repo", ".venv", "_runtime_tmp"):
                    force_rmtree(_os.path.join(output_dir, sub))

    return created_run_ids
