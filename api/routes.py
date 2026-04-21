import io
import os
import zipfile
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api import store
from api.constants import RunStatus
from api.db import get_db

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    repo_url: str
    function_name: str = ""
    provider: str = "deepseek"
    model: str | None = None
    preset: str = "default"
    install_deps: bool = True
    api_key: str = ""
    function_limit: int | None = None
    use_rag: bool = True


class BenchmarkRequest(BaseModel):
    provider: str = "deepseek"
    model: str | None = None
    preset: str = "default"
    api_key: str = ""
    use_rag: bool = True
    phase: str = "measure"
    seed: int = 42
    populate_count: int = 30


# ── Background tasks ──────────────────────────────────────────────────────────

def _execute_pipeline(run_id: int, body: RunRequest):
    with store.session_scope() as db:
        store.update_run(db, run_id, status=RunStatus.RUNNING)

    if body.function_name:
        from src.pipeline import run_pipeline
        run_pipeline(
            run_id=run_id,
            repo_url=body.repo_url,
            fn_name=body.function_name,
            provider=body.provider,
            model=body.model,
            preset=body.preset,
            install_deps=body.install_deps,
            api_key=body.api_key or None,
            use_rag=body.use_rag,
        )
    else:
        from src.pipeline import run_project_for_api

        def progress_cb(current: int, total: int):
            with store.session_scope() as db:
                store.update_run(db, run_id, progress_current=current, progress_total=total)

        run_project_for_api(
            run_id=run_id,
            repo_url=body.repo_url,
            provider=body.provider,
            model=body.model,
            preset=body.preset,
            install_deps=body.install_deps,
            api_key=body.api_key or None,
            limit=body.function_limit,
            progress_callback=progress_cb,
            use_rag=body.use_rag,
        )


def _execute_benchmark(body: BenchmarkRequest):
    from src.llm import build_config
    from src import benchmarks

    benchmarks.run_quixbugs(
        phase=body.phase,
        cfg=build_config(body.provider, body.model, api_key=body.api_key or None),
        preset=body.preset,
        seed=body.seed,
        populate_count=body.populate_count,
        use_rag=body.use_rag,
    )


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_run(body: RunRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = store.create_run(db,
        repo_url=body.repo_url,
        function_name=body.function_name,
        mode="single" if body.function_name else "project",
        provider=body.provider,
        model=body.model,
        preset=body.preset,
        use_rag=body.use_rag,
        status=RunStatus.PENDING,
    )
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_execute_pipeline, run.id, body)
    return {"id": run.id, "status": run.status}


@router.post("/benchmark", status_code=202)
def create_benchmark(body: BenchmarkRequest, background_tasks: BackgroundTasks):
    if body.phase not in ("populate", "measure"):
        raise HTTPException(status_code=400, detail=f"Unknown phase: {body.phase}")
    background_tasks.add_task(_execute_benchmark, body)
    return {"started": True, "phase": body.phase}


def _run_summary(r) -> dict:
    return {
        "id": r.id,
        "repo_url": r.repo_url,
        "function_name": r.function_name,
        "mode": r.mode,
        "benchmark_id": r.benchmark_id,
        "status": r.status,
        "progress_current": r.progress_current,
        "progress_total": r.progress_total,
        "created_at": r.created_at,
        "finished_at": r.finished_at,
        "promoted_to_memory_at": r.promoted_to_memory_at,
        "function_count": len(r.functions),
        "tests_passed": r.tests_passed,
        "tests_failed": r.tests_failed,
        "tests_run": r.tests_run,
        "avg_coverage_pct": r.avg_coverage_pct,
        "use_rag": r.use_rag,
        "provider": r.provider,
        "f2p": r.f2p,
        "f2f": r.f2f,
        "p2f": r.p2f,
        "p2p": r.p2p,
        "detected": r.detected,
        "resolved": r.resolved,
        "golden": r.golden,
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
        "functions": [
            {
                "id": fn.id,
                "name": fn.name,
                "file_path": fn.file_path,
                "source": fn.source,
                "tests_passed": fn.tests_passed,
                "tests_failed": fn.tests_failed,
                "coverage_pct": fn.coverage_pct,
                "whitebox_code": fn.whitebox_code,
                "blackbox_code": fn.blackbox_code,
            }
            for fn in run.functions
        ],
    }


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    if not store.delete_run(db, run_id):
        raise HTTPException(status_code=404, detail="Run not found")
    db.commit()
