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

from api.constants import RunStatus
from api.db import SessionLocal
from api.models import Function, Run


# ── session helper ──────────────────────────────────────────────────────────

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


# ── Run CRUD ────────────────────────────────────────────────────────────────

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


def delete_run(db: Session, run_id: int) -> bool:
    run = db.get(Run, run_id)
    if run is None:
        return False
    db.delete(run)
    return True


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


# ── analytics summary ──────────────────────────────────────────────────────

def _bench_bucket(rows) -> dict:
    """Aggregate a list of Run rows into SWT-bench summary numbers."""
    total = len(rows)
    detected = sum(1 for r in rows if r.detected)
    resolved = sum(1 for r in rows if r.resolved)
    applicable = sum(1 for r in rows if r.patch_applied)
    f2p = sum(r.f2p or 0 for r in rows)
    f2f = sum(r.f2f or 0 for r in rows)
    p2f = sum(r.p2f or 0 for r in rows)
    p2p = sum(r.p2p or 0 for r in rows)
    return {
        "runs": total,
        "detected": detected,
        "resolved": resolved,
        "patch_applied": applicable,
        "f2p": f2p, "f2f": f2f, "p2f": p2f, "p2p": p2p,
        "resolved_rate": round(resolved / total * 100, 1) if total else 0.0,
        "detection_rate": round(detected / total * 100, 1) if total else 0.0,
    }


def summary_stats(db: Session) -> dict:
    """SWT-Bench analytics dashboard. Only benchmark runs are summarized —
    user (`mode='repo'`) runs have no oracle grade and aren't aggregable."""
    bench_runs = (
        db.query(Run)
        .filter(Run.status == RunStatus.DONE, Run.mode == "swtbench")
        .all()
    )

    def _project_name(repo_url: str) -> str:
        if repo_url.startswith("swtbench:"):
            return f"swtbench/{repo_url.split(':', 1)[1]}"
        return repo_url

    by_project: dict[str, list] = {}
    for r in bench_runs:
        by_project.setdefault(_project_name(r.repo_url), []).append(r)

    by_provider: dict[str, list] = {}
    for r in bench_runs:
        by_provider.setdefault(r.provider or "unknown", []).append(r)

    recent = (
        db.query(Run)
        .filter(Run.status == RunStatus.DONE, Run.mode == "swtbench")
        .order_by(Run.created_at.desc())
        .limit(20)
        .all()
    )

    return {
        "overall": _bench_bucket(bench_runs),
        "by_project": [
            {"project": name, **_bench_bucket(rows)}
            for name, rows in sorted(by_project.items())
        ],
        "by_provider": [
            {"provider": name, **_bench_bucket(rows)}
            for name, rows in sorted(by_provider.items())
        ],
        "recent_runs": [
            {
                "id": r.id,
                "repo_url": r.repo_url,
                "mode": r.mode,
                "benchmark_id": r.benchmark_id,
                "provider": r.provider,
                "detected": r.detected,
                "resolved": r.resolved,
                "f2p": r.f2p, "f2f": r.f2f, "p2f": r.p2f, "p2p": r.p2p,
                "tests_run": r.tests_run,
                "elapsed_seconds": r.elapsed_seconds,
                "created_at": r.created_at,
                "finished_at": r.finished_at,
            }
            for r in recent
        ],
    }
