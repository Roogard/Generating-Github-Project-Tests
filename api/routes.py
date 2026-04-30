"""REST API for the test-generation pipeline.

One endpoint creates runs: POST /api/runs with a `source` discriminator
(`'repo' | 'swtbench'`). The route handler builds an input adapter and
dispatches to the runner as a background task.

The other endpoints (list / get / delete / download / status) are pure
read paths over the unified Run + Function tables — no source-specific
branching needed.
"""
import io
import os
import zipfile
from typing import Literal

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api import store
from api.db import get_db
from api.models import RunStatus


router = APIRouter(prefix="/api/runs", tags=["runs"])
analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("/summary")
def get_analytics_summary(db: Session = Depends(get_db)):
    return store.summary_stats(db)


class RunRequest(BaseModel):
    """Unified body. `source` selects which adapter to build; only the
    fields relevant to that source are read."""

    source: Literal["repo", "swtbench"] = "repo"

    # shared
    provider: str = "deepseek"
    model: str | None = None
    preset: str = "default"
    api_key: str = ""

    # repo (issue-driven)
    repo_url: str | None = None
    issue_text: str | None = None      # REQUIRED for source='repo'
    issue_title: str | None = None     # optional; derived from first line if blank
    hints_text: str | None = None      # optional PR-review-style hints
    install_deps: bool = True

    # swtbench
    dataset: str | None = None         # 'swtbench_lite' | 'swtbench_verified'
    instance_limit: int | None = None
    instance_ids: list[str] | None = None
    use_official_images: bool = True


# ── Background task ──────────────────────────────────────────────────────────

def _execute_run(run_id: int, body: RunRequest):
    """Build the adapter and run it. Errors are caught and persisted as
    Run.status=ERROR by the runner."""
    from src.inputs import build_adapter
    from src.llm import build_config
    from src.runner import run_batch

    cfg = build_config(body.provider, body.model, api_key=body.api_key or None)

    try:
        adapter = build_adapter(body.source, cfg=cfg, request=body)
    except (ValueError, TypeError) as e:
        with store.session_scope() as db:
            store.update_run(db, run_id,
                             status=RunStatus.ERROR,
                             error_message=f"adapter build failed: {e}")
        return

    run_batch(adapter, run_id=run_id)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_run(
    body: RunRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    if body.source == "repo":
        if not body.repo_url:
            raise HTTPException(status_code=400, detail="source='repo' requires repo_url")
        if not body.issue_text or not body.issue_text.strip():
            raise HTTPException(status_code=400,
                                detail="source='repo' requires issue_text — the agent is issue-driven")
    if body.source == "swtbench":
        if body.dataset not in ("swtbench_lite", "swtbench_verified"):
            raise HTTPException(status_code=400,
                                detail="swtbench dataset must be swtbench_lite or swtbench_verified")

    run = store.create_run(db,
        repo_url=body.repo_url or "",
        mode=("swtbench" if body.source == "swtbench" else "repo"),
        dataset=body.dataset if body.source == "swtbench" else None,
        provider=body.provider,
        model=body.model,
        preset=body.preset,
        status=RunStatus.PENDING,
    )
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_execute_run, run.id, body)
    return {"id": run.id, "status": run.status, "source": body.source}


def _run_summary(r) -> dict:
    return {
        "id": r.id,
        "repo_url": r.repo_url,
        "mode": r.mode,
        "dataset": r.dataset,
        "benchmark_id": r.benchmark_id,
        "status": r.status,
        "progress_current": r.progress_current,
        "progress_total": r.progress_total,
        "created_at": r.created_at,
        "finished_at": r.finished_at,
        "tests_passed": r.tests_passed,
        "tests_failed": r.tests_failed,
        "tests_run": r.tests_run,
        "provider": r.provider,
        "f2p": r.f2p,
        "f2f": r.f2f,
        "p2f": r.p2f,
        "p2p": r.p2p,
        "detected": r.detected,
        "resolved": r.resolved,
    }


@router.get("/")
def list_runs(status: str | None = None, db: Session = Depends(get_db)):
    return [_run_summary(r) for r in store.list_runs(db, status=status)]


@router.get("/{run_id}/status")
def get_run_status(run_id: int, db: Session = Depends(get_db)):
    run = store.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "status": run.status,
        "progress_current": run.progress_current,
        "progress_total": run.progress_total,
        "current_stage": run.current_stage,
        "error_message": run.error_message,
    }


@router.get("/{run_id}/download")
def download_run(run_id: int, db: Session = Depends(get_db)):
    run = store.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    if not run.output_dir or not os.path.isdir(run.output_dir):
        raise HTTPException(status_code=404, detail="Output directory not found")

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _dirs, files in os.walk(run.output_dir):
            for fname in files:
                fpath = os.path.join(root, fname)
                arcname = os.path.relpath(fpath, os.path.dirname(run.output_dir))
                zf.write(fpath, arcname)
    buf.seek(0)

    project_name = run.output_dir.replace("\\", "/").rstrip("/").split("/")[-1]
    return StreamingResponse(
        buf,
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{project_name}_tests.zip"'},
    )


@router.get("/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = store.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        **_run_summary(run),
        "model": run.model,
        "preset": run.preset,
        "output_dir": run.output_dir,
        "error_message": run.error_message,
        "elapsed_seconds": run.elapsed_seconds,
        "patch_applied": run.patch_applied,
        "current_stage": run.current_stage,
        "functions": [
            {
                "id": fn.id,
                "name": fn.name,
                "tests_passed": fn.tests_passed,
                "tests_failed": fn.tests_failed,
                "test_code": fn.test_code,
            }
            for fn in run.functions
        ],
    }


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    if not store.delete_run(db, run_id):
        raise HTTPException(status_code=404, detail="Run not found")
    db.commit()
