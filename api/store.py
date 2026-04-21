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

def _read_if_exists(path: str) -> str | None:
    if not path or not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def _find_test_code(test_dir: str, fn_name: str) -> tuple[str | None, str | None, str | None, str | None]:
    """Locate whitebox + blackbox test files for a function. Tries named variant first,
    then falls back to the generic single-function filenames. Returns (wb_code, bb_code,
    wb_path, bb_path)."""
    if not test_dir or not os.path.isdir(test_dir):
        return None, None, None, None
    candidates = [
        (os.path.join(test_dir, f"test_{fn_name}_whitebox.py"),
         os.path.join(test_dir, f"test_{fn_name}_blackbox.py")),
        (os.path.join(test_dir, "test_whitebox.py"),
         os.path.join(test_dir, "test_blackbox.py")),
    ]
    for wb_path, bb_path in candidates:
        wb = _read_if_exists(wb_path)
        bb = _read_if_exists(bb_path)
        if wb or bb:
            return wb, bb, wb_path if wb else None, bb_path if bb else None
    return None, None, None, None


def save_function_result(db: Session, run_id: int, result: dict) -> Function:
    """Persist one function result: Function row with denormalized wb/bb code."""
    test_dir = result.get("test_dir", "")
    fn_name = result["fn_name"]
    wb_code, bb_code, wb_path, bb_path = _find_test_code(test_dir, fn_name)

    outcomes = result.get("test_outcomes", {}) or {}
    coverage = result.get("coverage", {}) or {}

    def _counts(path: str | None) -> tuple[int, int]:
        if not path:
            return 0, 0
        o = outcomes.get(path, {})
        return len(o.get("passed", [])), len(o.get("failed", []))

    wb_pass, wb_fail = _counts(wb_path)
    bb_pass, bb_fail = _counts(bb_path)

    cov_vals = [
        coverage.get(p, {}).get("coverage_pct")
        for p in (wb_path, bb_path) if p
    ]
    cov_vals = [v for v in cov_vals if v is not None]
    coverage_pct = round(sum(cov_vals) / len(cov_vals), 2) if cov_vals else None

    fn = Function(
        run_id=run_id,
        name=fn_name,
        file_path=result.get("fn_file", ""),
        source=result.get("fn_source", ""),
        whitebox_code=wb_code,
        blackbox_code=bb_code,
        tests_passed=wb_pass + bb_pass,
        tests_failed=wb_fail + bb_fail,
        coverage_pct=coverage_pct,
    )
    db.add(fn)
    db.flush()
    return fn


def finalize_run(db: Session, run_id: int) -> Run | None:
    """Aggregate child Function outcomes onto the Run row. Call after all
    save_function_result() calls for a given run have been issued."""
    run = db.get(Run, run_id)
    if run is None:
        return None
    agg = db.query(
        func.coalesce(func.sum(Function.tests_passed), 0),
        func.coalesce(func.sum(Function.tests_failed), 0),
        func.avg(Function.coverage_pct),
    ).filter(Function.run_id == run_id).first()
    passed, failed, avg_cov = agg
    run.tests_passed = int(passed or 0)
    run.tests_failed = int(failed or 0)
    # tests_run only from pipeline-level field is set elsewhere (batch modes)
    # for API-triggered single/project runs we approximate as passed + failed
    if run.tests_run == 0:
        run.tests_run = run.tests_passed + run.tests_failed
    run.avg_coverage_pct = round(float(avg_cov), 2) if avg_cov is not None else None
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
    """Benchmark-interpreter dashboard. Aggregates SWT-bench transitions across
    QuixBugs runs, with base-vs-RAG, per-project, and per-provider splits for
    comparison."""
    bench_runs = (
        db.query(Run)
        .filter(Run.status == RunStatus.DONE, Run.mode.in_(BENCH_MODES))
        .all()
    )

    overall = _bench_bucket(bench_runs)

    baseline = _bench_bucket([r for r in bench_runs if not r.use_rag])
    with_rag = _bench_bucket([r for r in bench_runs if r.use_rag])

    def _project_name(repo_url: str) -> str:
        # "quixbugs:foo" → "quixbugs/foo"
        if repo_url.startswith("quixbugs:"):
            return f"quixbugs/{repo_url.split(':', 1)[1]}"
        return repo_url

    by_project: dict[str, list] = {}
    for r in bench_runs:
        by_project.setdefault(_project_name(r.repo_url), []).append(r)
    projects = [
        {"project": name, **_bench_bucket(rows)}
        for name, rows in sorted(by_project.items())
    ]

    by_provider: dict[str, list] = {}
    for r in bench_runs:
        by_provider.setdefault(r.provider or "unknown", []).append(r)
    providers = [
        {"provider": name, **_bench_bucket(rows)}
        for name, rows in sorted(by_provider.items())
    ]

    recent = (
        db.query(Run)
        .filter(Run.status == RunStatus.DONE, Run.mode.in_(BENCH_MODES))
        .order_by(Run.created_at.desc())
        .limit(20)
        .all()
    )
    recent_runs = [
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
    ]

    rag_count = 0
    try:
        from src.vectordb import get_collection
        rag_count = get_collection().count()
    except Exception:
        pass

    return {
        "overall": overall,
        "baseline": baseline,
        "with_rag": with_rag,
        "by_project": projects,
        "by_provider": providers,
        "rag_examples": rag_count,
        "recent_runs": recent_runs,
    }
