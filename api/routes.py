import json
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from api.db import get_db, SessionLocal
from api.models import Run, Function, GeneratedTest, ProposedFix

router = APIRouter(prefix="/api/runs", tags=["runs"])


class RunRequest(BaseModel):
    repo_url: str
    function_name: str
    description: str = ""
    provider: str = "deepseek"
    model: str | None = None
    preset: str = "default"
    install_deps: bool = True
    api_key: str = ""  # user's LLM API key; overrides .env when provided

    def effective_model(self) -> str | None:
        """Return None if model is blank/placeholder so the pipeline uses its default."""
        if not self.model or not self.model.strip() or self.model.strip().lower() == "string":
            return None
        return self.model

    def effective_api_key(self) -> str | None:
        if not self.api_key or not self.api_key.strip():
            return None
        return self.api_key.strip()


# ── Background task ───────────────────────────────────────────────────────────

def _execute_pipeline(run_id: int, body: RunRequest):
    from src.pipeline import run_pipeline

    db = SessionLocal()
    try:
        run = db.get(Run, run_id)
        run.status = "running"
        db.commit()

        result = run_pipeline(
            repo_url=body.repo_url,
            fn_name=body.function_name,
            description=body.description,
            provider=body.provider,
            model=body.effective_model(),
            preset=body.preset,
            install_deps=body.install_deps,
            api_key=body.effective_api_key(),
        )

        run.output_dir = result["output_dir"]

        if result["status"] == "error":
            run.status = "error"
            run.error_message = result["error"]
        else:
            run.status = "done"

            # Persist function + test results
            fn_record = Function(
                run_id=run_id,
                name=result["fn_name"],
                file_path=result["fn_file"],
            )
            db.add(fn_record)
            db.flush()

            import os
            test_dir = os.path.join(result["output_dir"], "generated_tests", f"{result['fn_name']}_0")
            if os.path.isdir(test_dir):
                for fname in sorted(os.listdir(test_dir)):
                    if not (fname.startswith("test_") and fname.endswith(".py")):
                        continue
                    test_type = fname[len("test_"):-len(".py")]
                    with open(os.path.join(test_dir, fname), encoding="utf-8") as fh:
                        code = fh.read()
                    key = (f"{result['fn_name']}_0", fname)
                    outcome = result["test_outcomes"].get(str(key), {})
                    db.add(GeneratedTest(
                        function_id=fn_record.id,
                        test_type=test_type,
                        code=code,
                        passed=len(outcome.get("passed", [])),
                        failed=len(outcome.get("failed", [])),
                    ))

            # Persist proposed fix if one was written
            fix_dir = os.path.join(result["output_dir"], "fixed_functions", f"{result['fn_name']}_0", "iteration_0")
            fixed_path = os.path.join(fix_dir, "fixed_function.py")
            diag_path  = os.path.join(fix_dir, "diagnosis.md")
            if os.path.isfile(fixed_path):
                fixed_code = open(fixed_path, encoding="utf-8").read()
                diagnosis  = open(diag_path,  encoding="utf-8").read() if os.path.isfile(diag_path) else None
                db.add(ProposedFix(function_id=fn_record.id, fixed_code=fixed_code, diagnosis=diagnosis))

        run.finished_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        run = db.get(Run, run_id)
        run.status = "error"
        run.error_message = str(e)
        run.finished_at = datetime.utcnow()
        db.commit()
    finally:
        db.close()


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/", status_code=201)
def create_run(body: RunRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    run = Run(
        repo_url=body.repo_url,
        function_name=body.function_name,
        config_json=json.dumps({"provider": body.provider, "preset": body.preset}),
        status="pending",
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
            "created_at": r.created_at,
            "finished_at": r.finished_at,
        }
        for r in q.order_by(Run.created_at.desc()).all()
    ]


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
        "created_at": run.created_at,
        "finished_at": run.finished_at,
        "functions": [
            {
                "id": fn.id,
                "name": fn.name,
                "file_path": fn.file_path,
                "tests": [
                    {"id": t.id, "type": t.test_type, "passed": t.passed, "failed": t.failed}
                    for t in fn.generated_tests
                ],
                "fixes": [
                    {"id": fx.id, "status": fx.status, "diagnosis": fx.diagnosis}
                    for fx in fn.proposed_fixes
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
