"""Thin data-access layer over the SQLite DB.

Callers own the transaction boundary (commit/rollback). `session_scope()` is
provided for script / background-task callers that want one.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import func
from sqlalchemy.orm import Session

from api.db import SessionLocal
from api.models import Function, Run, RunStatus


# Identifies the SWT-Bench batch baked into data/featured.db. Used by
# scripts/build_featured_db.py to filter from the working DB; the website
# itself just reads everything in the featured DB.
FEATURED_BATCH = {
    "dataset": "swtbench_lite",
    "provider": "deepseek",
    "model": "deepseek-chat",
    "preset": "default",
    "date": "2026-04-30",
}


def github_issue_url(benchmark_id: str | None) -> str | None:
    """`astropy__astropy-14182` → https://github.com/astropy/astropy/issues/14182.

    Splits on the last hyphen for the issue number and the first `__` for
    owner/repo. Handles repos with hyphens in the name (scikit-learn etc.)
    because the issue number is always at the very end. GitHub auto-redirects
    /issues/N → /pull/N when N is a PR.
    """
    if not benchmark_id or "__" not in benchmark_id or "-" not in benchmark_id:
        return None
    base, _, issue_no = benchmark_id.rpartition("-")
    if not issue_no.isdigit():
        return None
    owner, _, repo = base.partition("__")
    if not owner or not repo:
        return None
    return f"https://github.com/{owner}/{repo}/issues/{issue_no}"


@contextmanager
def session_scope() -> Iterator[Session]:
    """Commit on success, rollback on error, always close."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def create_run(db: Session, **fields) -> Run:
    run = Run(**fields)
    db.add(run)
    db.flush()
    return run


def get_run(db: Session, run_id: int) -> Run | None:
    return db.get(Run, run_id)


def list_runs(db: Session, status: str | None = None) -> list[Run]:
    q = db.query(Run)
    if status:
        q = q.filter(Run.status == status)
    return q.order_by(Run.created_at.desc()).all()


def update_run(db: Session, run_id: int, **fields) -> Run | None:
    run = db.get(Run, run_id)
    if run is None:
        return None
    for k, v in fields.items():
        setattr(run, k, v)
    return run


def save_function_result(db: Session, run_id: int, result: dict) -> Function:
    """Persist one harness run's output: test file + pass/fail counts + per-skill history."""
    history = result.get("history") or []
    try:
        history_json = json.dumps(history, default=str) if history else None
    except (TypeError, ValueError):
        history_json = None
    fn = Function(
        run_id=run_id,
        name=result["fn_name"],
        test_code=result.get("test_code") or None,
        tests_passed=result.get("tests_passed", 0),
        tests_failed=result.get("tests_failed", 0),
        history_json=history_json,
    )
    db.add(fn)
    db.flush()
    return fn


def finalize_run(db: Session, run_id: int) -> Run:
    run = db.get(Run, run_id)
    agg = db.query(
        func.sum(Function.tests_passed),
        func.sum(Function.tests_failed),
    ).filter(Function.run_id == run_id).first()

    run.tests_passed = int(agg[0] or 0)
    run.tests_failed = int(agg[1] or 0)
    run.tests_run = run.tests_passed + run.tests_failed
    return run


def featured_batch(db: Session) -> dict:
    """The featured SWT-Bench Lite batch shown on /database.

    Reads everything in the featured DB (which is built to contain exactly
    the FEATURED_BATCH rows by scripts/build_featured_db.py). Returns one
    summary block plus the per-instance rows in id order.
    """
    rows = db.query(Run).order_by(Run.id).all()

    total = len(rows)
    resolved = sum(1 for r in rows if r.resolved)
    detected = sum(1 for r in rows if r.detected)
    summary = {
        **FEATURED_BATCH,
        "total": total,
        "resolved": resolved,
        "detected": detected,
        "resolved_rate": round(resolved / total * 100, 1) if total else 0.0,
        "detection_rate": round(detected / total * 100, 1) if total else 0.0,
        "f2p": sum(r.f2p or 0 for r in rows),
        "f2f": sum(r.f2f or 0 for r in rows),
        "p2f": sum(r.p2f or 0 for r in rows),
        "p2p": sum(r.p2p or 0 for r in rows),
    }
    instances = [
        {
            "id": r.id,
            "benchmark_id": r.benchmark_id,
            "repo_url": r.repo_url,
            "github_url": github_issue_url(r.benchmark_id),
            "resolved": r.resolved,
            "detected": r.detected,
            "f2p": r.f2p, "f2f": r.f2f, "p2f": r.p2f, "p2p": r.p2p,
            "tests_passed": r.tests_passed,
            "tests_failed": r.tests_failed,
            "elapsed_seconds": r.elapsed_seconds,
            "finished_at": r.finished_at,
        }
        for r in rows
    ]
    return {"summary": summary, "instances": instances}
