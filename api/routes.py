import io
import json
import os
import zipfile
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.db import get_db, SessionLocal
from api.models import Run, Function, GeneratedTest, ProposedFix, TestFailure, FixAttempt
from api.constants import RunStatus

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    repo_url: str
    function_name: str = ""         # empty = whole-project mode
    provider: str = "deepseek"
    model: str | None = None
    preset: str = "default"
    install_deps: bool = True
    api_key: str = ""
    fix_pass: bool = False
    function_limit: int | None = None
    save_to_db: bool = True       # persist full run details to SQLite
    save_to_rag: bool = True      # ingest generated tests into ChromaDB for future RAG
    rag_success_only: bool = True # only ingest into RAG if at least one test passed
    use_rag: bool = True          # retrieve ChromaDB examples during test generation

    def effective_model(self) -> str | None:
        if not self.model or not self.model.strip() or self.model.strip().lower() == "string":
            return None
        return self.model

    def effective_api_key(self) -> str | None:
        if not self.api_key or not self.api_key.strip():
            return None
        return self.api_key.strip()


def _persist_results(
    db: Session,
    run_id: int,
    result: dict,
    repo_url: str = "",
    save_to_db: bool = True,
    save_to_rag: bool = True,
    rag_success_only: bool = True,
) -> None:
    whitebox_code: str = ""
    blackbox_code: str = ""
    total_passed = 0
    total_failed = 0
    fn_source = result.get("fn_source", "")

    if save_to_db:
        fn_record = Function(
            run_id=run_id,
            name=result["fn_name"],
            file_path=result["fn_file"],
            source=fn_source,
        )
        db.add(fn_record)
        db.flush()

        generated_test_by_path: dict[str, GeneratedTest] = {}
        test_dir = result.get("test_dir", "")
        if test_dir and os.path.isdir(test_dir):
            for fname in sorted(os.listdir(test_dir)):
                if not (fname.startswith("test_") and fname.endswith(".py")):
                    continue
                test_type = fname[len("test_"):-len(".py")]
                fpath = os.path.join(test_dir, fname)
                with open(fpath, encoding="utf-8") as fh:
                    code = fh.read()
                outcome = result.get("test_outcomes", {}).get(fpath, {})
                cov = result.get("coverage", {}).get(fpath, {})
                p = len(outcome.get("passed", []))
                f = len(outcome.get("failed", []))
                total_passed += p
                total_failed += f
                gt = GeneratedTest(
                    function_id=fn_record.id,
                    test_type=test_type,
                    code=code,
                    passed=p,
                    failed=f,
                    coverage_pct=cov.get("coverage_pct"),
                )
                db.add(gt)
                db.flush()
                generated_test_by_path[fpath] = gt
                if test_type == "whitebox":
                    whitebox_code = code
                elif test_type == "blackbox":
                    blackbox_code = code

        for failure in result.get("failures", []):
            path = failure.get("test_file_path") or failure.get("path", "")
            gt = generated_test_by_path.get(path)
            if gt is None:
                continue
            db.add(TestFailure(
                generated_test_id=gt.id,
                test_name=failure.get("name", ""),
                kind=failure.get("kind", "failure"),
                longrepr=failure.get("longrepr", ""),
                assertion=failure.get("assertion", ""),
                expected=failure.get("expected", ""),
                actual=failure.get("actual", ""),
            ))

        for attempt in result.get("repair_attempts", []):
            db.add(FixAttempt(
                function_id=fn_record.id,
                attempt_number=attempt["attempt_number"],
                attempt_type=attempt["attempt_type"],
                failures_before=attempt["failures_before"],
                failures_after=attempt["failures_after"],
                converged=attempt["converged"],
            ))

        fix_attempt = result.get("fix_attempt")
        if fix_attempt:
            db.add(FixAttempt(
                function_id=fn_record.id,
                attempt_number=len(result.get("repair_attempts", [])) + 1,
                attempt_type="fix_agent",
                diagnosis=fix_attempt.get("diagnosis"),
                failures_before=fix_attempt.get("failures_before", 0),
                failures_after=fix_attempt.get("failures_after", 0),
                converged=fix_attempt.get("converged", False),
            ))

        fixed_code = result.get("fixed_code", "")
        if fixed_code:
            db.add(ProposedFix(
                function_id=fn_record.id,
                fixed_code=fixed_code,
                diagnosis=result.get("diagnosis"),
            ))
    else:
        # Compute totals for RAG gating without DB writes
        test_dir = result.get("test_dir", "")
        if test_dir and os.path.isdir(test_dir):
            for fname in sorted(os.listdir(test_dir)):
                if not (fname.startswith("test_") and fname.endswith(".py")):
                    continue
                test_type = fname[len("test_"):-len(".py")]
                fpath = os.path.join(test_dir, fname)
                with open(fpath, encoding="utf-8") as fh:
                    code = fh.read()
                outcome = result.get("test_outcomes", {}).get(fpath, {})
                total_passed += len(outcome.get("passed", []))
                total_failed += len(outcome.get("failed", []))
                if test_type == "whitebox":
                    whitebox_code = code
                elif test_type == "blackbox":
                    blackbox_code = code

    rag_eligible = save_to_rag and fn_source and (whitebox_code or blackbox_code)
    if rag_success_only:
        rag_eligible = rag_eligible and total_passed > 0
    if rag_eligible:
        try:
            from src.vectordb import ingest_example
            agg_cov = None
            cov_vals = [v["coverage_pct"] for v in result.get("coverage", {}).values() if v.get("coverage_pct") is not None]
            if cov_vals:
                agg_cov = sum(cov_vals) / len(cov_vals)
            ingest_example(
                fn={"name": result["fn_name"], "source": fn_source, "file_path": result.get("fn_file", "")},
                repo_url=repo_url,
                whitebox_code=whitebox_code,
                blackbox_code=blackbox_code,
                passed=total_passed,
                failed=total_failed,
                coverage_pct=agg_cov,
            )
        except Exception:
            pass


# ── Background task ───────────────────────────────────────────────────────────

def _execute_pipeline(run_id: int, body: RunRequest):
    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        run.status = RunStatus.RUNNING
        db.commit()

        if body.function_name:
            # Single-function mode
            from src.pipeline import run_pipeline
            result = run_pipeline(
                repo_url=body.repo_url,
                fn_name=body.function_name,
                provider=body.provider,
                model=body.effective_model(),
                preset=body.preset,
                install_deps=body.install_deps,
                api_key=body.effective_api_key(),
                fix_pass=body.fix_pass,
                use_rag=body.use_rag,
            )
            run.output_dir = result["output_dir"]
            if result["status"] == "error":
                run.status = RunStatus.ERROR
                run.error_message = result["error"]
            else:
                run.status = RunStatus.DONE
                _persist_results(
                    db, run_id, result,
                    repo_url=run.repo_url,
                    save_to_db=body.save_to_db,
                    save_to_rag=body.save_to_rag,
                    rag_success_only=body.rag_success_only,
                )
        else:
            # Whole-project mode
            from src.pipeline import run_project_for_api

            def progress_cb(current: int, total: int):
                run.progress_current = current
                run.progress_total = total
                db.commit()

            result = run_project_for_api(
                repo_url=body.repo_url,
                provider=body.provider,
                model=body.effective_model(),
                preset=body.preset,
                install_deps=body.install_deps,
                api_key=body.effective_api_key(),
                fix_pass=body.fix_pass,
                limit=body.function_limit,
                progress_callback=progress_cb,
                use_rag=body.use_rag,
            )
            run.output_dir = result["output_dir"]
            if result["status"] == "error":
                run.status = RunStatus.ERROR
                run.error_message = result["error"]
            else:
                run.status = RunStatus.DONE
                for fn_result in result.get("results", []):
                    if fn_result["status"] == "done":
                        _persist_results(
                            db, run_id, fn_result,
                            repo_url=run.repo_url,
                            save_to_db=body.save_to_db,
                            save_to_rag=body.save_to_rag,
                            rag_success_only=body.rag_success_only,
                        )

        run.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        try:
            run = db.get(Run, run_id)
            run.status = RunStatus.ERROR
            run.error_message = str(e)
            run.finished_at = datetime.utcnow()
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_run(body: RunRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = Run(
        repo_url=body.repo_url,
        function_name=body.function_name,
        config_json=json.dumps({
            "provider": body.provider,
            "preset": body.preset,
            "fix_pass": body.fix_pass,
            "function_limit": body.function_limit,
            "use_rag": body.use_rag,
            "save_to_rag": body.save_to_rag,
        }),
        status=RunStatus.PENDING,
        progress_current=0,
        progress_total=0,
    )
    db.add(run)
    db.commit()
    db.refresh(run)
    background_tasks.add_task(_execute_pipeline, run.id, body)
    return {"id": run.id, "status": run.status}


@router.get("/")
def list_runs(status: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Run)
    if status:
        q = q.filter(Run.status == status)
    return [
        {
            "id": r.id,
            "repo_url": r.repo_url,
            "function_name": r.function_name,
            "status": r.status,
            "progress_current": r.progress_current,
            "progress_total": r.progress_total,
            "created_at": r.created_at,
            "finished_at": r.finished_at,
            "function_count": len(r.functions),
        }
        for r in q.order_by(Run.created_at.desc()).all()
    ]


@router.get("/{run_id}/status")
def get_run_status(run_id: int, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
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
    run = db.get(Run, run_id)
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
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {
        "id": run.id,
        "repo_url": run.repo_url,
        "function_name": run.function_name,
        "status": run.status,
        "config": json.loads(run.config_json) if run.config_json else {},
        "output_dir": run.output_dir,
        "error_message": run.error_message,
        "progress_current": run.progress_current,
        "progress_total": run.progress_total,
        "created_at": run.created_at,
        "finished_at": run.finished_at,
        "functions": [
            {
                "id": fn.id,
                "name": fn.name,
                "file_path": fn.file_path,
                "source": fn.source,
                "tests": [
                    {
                        "id": t.id,
                        "type": t.test_type,
                        "passed": t.passed,
                        "failed": t.failed,
                        "coverage_pct": t.coverage_pct,
                        "code": t.code,
                    }
                    for t in fn.generated_tests
                ],
                "fixes": [
                    {"id": fx.id, "status": fx.status, "diagnosis": fx.diagnosis, "fixed_code": fx.fixed_code}
                    for fx in fn.proposed_fixes
                ],
                "failures": [
                    {
                        "test_name": f.test_name,
                        "kind": f.kind,
                        "longrepr": f.longrepr,
                        "assertion": f.assertion,
                        "expected": f.expected,
                        "actual": f.actual,
                    }
                    for t in fn.generated_tests
                    for f in t.test_failures
                ],
            }
            for fn in run.functions
        ],
    }


@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(Run, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    db.delete(run)
    db.commit()
