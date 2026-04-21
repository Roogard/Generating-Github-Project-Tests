"""Thin data-access layer over the SQLite DB.

Callers own the transaction boundary (commit/rollback). `session_scope()` is
provided for script / background-task callers that want one.
"""
from __future__ import annotations

import os
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


# ── persistence of one pipeline result ─────────────────────────────────────

def save_function_result(db: Session, run_id: int, result: dict) -> Function:
    test_dir = result.get("test_dir", "")
    wb_path = os.path.join(test_dir, "test_whitebox.py")
    bb_path = os.path.join(test_dir, "test_blackbox.py")
    wb_code = open(wb_path).read() if os.path.isfile(wb_path) else None
    bb_code = open(bb_path).read() if os.path.isfile(bb_path) else None

    outcomes = result.get("test_outcomes", {})
    wb_pass = len(outcomes.get(wb_path, {}).get("passed", []))
    wb_fail = len(outcomes.get(wb_path, {}).get("failed", []))
    bb_pass = len(outcomes.get(bb_path, {}).get("passed", []))
    bb_fail = len(outcomes.get(bb_path, {}).get("failed", []))

    fn = Function(
        run_id=run_id, name=result["fn_name"], file_path=result.get("fn_file", ""),
        source=result.get("fn_source", ""), whitebox_code=wb_code, blackbox_code=bb_code,
        tests_passed=wb_pass + bb_pass, tests_failed=wb_fail + bb_fail,
    )
    db.add(fn)
    db.flush()
    return fn


def finalize_run(db: Session, run_id: int) -> Run:
    run = db.get(Run, run_id)
    agg = db.query(
        func.sum(Function.tests_passed),
        func.sum(Function.tests_failed),
        func.avg(Function.coverage_pct),
    ).filter(Function.run_id == run_id).first()

    run.tests_passed = int(agg[0] or 0)
    run.tests_failed = int(agg[1] or 0)
    run.tests_run = run.tests_passed + run.tests_failed
    run.avg_coverage_pct = round(float(agg[2]), 2) if agg[2] else None
    return run


# ── quality scoring (for promote-to-memory) ────────────────────────────────

def score_function(
    fn: Function,
    *,
    min_passed: int = 0,
    min_pass_rate: float = 0.0,
    min_coverage: float | None = None,
) -> tuple[int, int, float | None, str | None]:
    """Gate a function's wb+bb pair against quality floors.

    Returns (passed, failed, coverage_pct, skip_reason). skip_reason is None
    when the pair meets every floor.
    """
    if not fn.source or not fn.source.strip():
        return 0, 0, None, "no_source"
    if not (fn.whitebox_code or fn.blackbox_code):
        return 0, 0, None, "no_tests"
    passed = fn.tests_passed or 0
    failed = fn.tests_failed or 0
    if passed < min_passed:
        return passed, failed, fn.coverage_pct, "below_min_passed"
    total = passed + failed
    pass_rate = passed / total if total else 0.0
    if pass_rate < min_pass_rate:
        return passed, failed, fn.coverage_pct, "below_min_pass_rate"
    if min_coverage is not None and (fn.coverage_pct is None or fn.coverage_pct < min_coverage):
        return passed, failed, fn.coverage_pct, "below_min_coverage"
    return passed, failed, fn.coverage_pct, None


# ── analytics summary ──────────────────────────────────────────────────────

BENCH_MODES = ("quixbugs",)
USER_MODES = ("single", "project")


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


def _user_bucket(rows) -> dict:
    total = len(rows)
    return {
        "runs": total,
        "tests_passed": sum(r.tests_passed or 0 for r in rows),
        "tests_failed": sum(r.tests_failed or 0 for r in rows),
        "avg_coverage": round(
            sum(r.avg_coverage_pct or 0 for r in rows) / total, 1
        ) if total else 0.0,
    }


def summary_stats(db: Session, mode_filter: str = "benchmark") -> dict:
    """Analytics dashboard. mode_filter: 'benchmark' | 'user' | 'both'."""

    def _bench_section():
        bench_runs = (
            db.query(Run)
            .filter(Run.status == RunStatus.DONE, Run.mode.in_(BENCH_MODES))
            .all()
        )

        def _project_name(repo_url: str) -> str:
            if repo_url.startswith("quixbugs:"):
                return f"quixbugs/{repo_url.split(':', 1)[1]}"
            return repo_url

        by_project: dict[str, list] = {}
        for r in bench_runs:
            by_project.setdefault(_project_name(r.repo_url), []).append(r)

        by_provider: dict[str, list] = {}
        for r in bench_runs:
            by_provider.setdefault(r.provider or "unknown", []).append(r)

        recent = (
            db.query(Run)
            .filter(Run.status == RunStatus.DONE, Run.mode.in_(BENCH_MODES))
            .order_by(Run.created_at.desc())
            .limit(20)
            .all()
        )

        rag_count = 0
        try:
            from src.vectordb import get_collection
            rag_count = get_collection().count()
        except Exception:
            pass

        return {
            "overall": _bench_bucket(bench_runs),
            "baseline": _bench_bucket([r for r in bench_runs if not r.use_rag]),
            "with_rag": _bench_bucket([r for r in bench_runs if r.use_rag]),
            "by_project": [
                {"project": name, **_bench_bucket(rows)}
                for name, rows in sorted(by_project.items())
            ],
            "by_provider": [
                {"provider": name, **_bench_bucket(rows)}
                for name, rows in sorted(by_provider.items())
            ],
            "rag_examples": rag_count,
            "recent_runs": [
                {
                    "id": r.id,
                    "repo_url": r.repo_url,
                    "mode": r.mode,
                    "benchmark_id": r.benchmark_id,
                    "provider": r.provider,
                    "use_rag": r.use_rag,
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

    def _user_section():
        user_runs = (
            db.query(Run)
            .filter(Run.status == RunStatus.DONE, Run.mode.in_(USER_MODES))
            .all()
        )
        recent = (
            db.query(Run)
            .filter(Run.status == RunStatus.DONE, Run.mode.in_(USER_MODES))
            .order_by(Run.created_at.desc())
            .limit(20)
            .all()
        )
        return {
            "summary": _user_bucket(user_runs),
            "recent_runs": [
                {
                    "id": r.id,
                    "repo_url": r.repo_url,
                    "mode": r.mode,
                    "provider": r.provider,
                    "use_rag": r.use_rag,
                    "tests_passed": r.tests_passed,
                    "tests_failed": r.tests_failed,
                    "avg_coverage_pct": r.avg_coverage_pct,
                    "created_at": r.created_at,
                    "finished_at": r.finished_at,
                }
                for r in recent
            ],
        }

    if mode_filter == "benchmark":
        return {"mode": "benchmark", **_bench_section()}
    if mode_filter == "user":
        return {"mode": "user", **_user_section()}
    # both
    return {
        "mode": "both",
        "benchmark": _bench_section(),
        "user": _user_section(),
    }
