"""REST API for the test-generation pipeline.

Run creation lives in the GitHub Action (src/action_entrypoint.py via
.github/workflows/ggpt.yml). The webapp is read-only and is backed by
data/featured.db — a small committed SQLite file with the showcase batch.
The working DB (./ggpt.db) where the runner actually persists results is
not exposed here.

  GET /api/runs/{id}                — full run + functions (RunDetail page)
  GET /api/runs/{id}/status         — lightweight status poll
  GET /api/runs/{id}/download       — zip of the generated test artifacts
  GET /api/database/featured-batch  — the showcase batch shown on /database
"""
import io
import os
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from api import store
from api.db import get_featured_db


router = APIRouter(prefix="/api/runs", tags=["runs"])
database_router = APIRouter(prefix="/api/database", tags=["database"])


@router.get("/{run_id}/status")
def get_run_status(run_id: int, db: Session = Depends(get_featured_db)):
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
def download_run(run_id: int, db: Session = Depends(get_featured_db)):
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
def get_run(run_id: int, db: Session = Depends(get_featured_db)):
    run = store.get_run(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "repo_url": run.repo_url,
        "mode": run.mode,
        "dataset": run.dataset,
        "benchmark_id": run.benchmark_id,
        "github_url": store.github_issue_url(run.benchmark_id),
        "problem_statement": run.problem_statement,
        "status": run.status,
        "progress_current": run.progress_current,
        "progress_total": run.progress_total,
        "created_at": run.created_at,
        "finished_at": run.finished_at,
        "tests_passed": run.tests_passed,
        "tests_failed": run.tests_failed,
        "tests_run": run.tests_run,
        "provider": run.provider,
        "f2p": run.f2p,
        "f2f": run.f2f,
        "p2f": run.p2f,
        "p2p": run.p2p,
        "detected": run.detected,
        "resolved": run.resolved,
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


@database_router.get("/featured-batch")
def get_featured_batch(db: Session = Depends(get_featured_db)):
    return store.featured_batch(db)
