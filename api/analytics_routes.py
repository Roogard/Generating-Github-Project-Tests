"""Aggregated analytics endpoint — powers the website dashboard."""
from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import Run, Function, GeneratedTest, TestFailure, ProposedFix
from api.constants import RunStatus

router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    # ── Aggregate test counts from generated_tests ────────────────────────────
    test_agg = db.query(
        func.count(GeneratedTest.id).label("total_tests"),
        func.sum(GeneratedTest.passed).label("total_passed"),
        func.sum(GeneratedTest.failed).label("total_failed"),
        func.avg(GeneratedTest.coverage_pct).label("avg_coverage"),
    ).first()

    total_tests = test_agg.total_tests or 0
    total_passed = int(test_agg.total_passed or 0)
    total_failed = int(test_agg.total_failed or 0)
    avg_coverage = round(float(test_agg.avg_coverage or 0), 1)
    total_run_tests = total_passed + total_failed
    pass_rate = round(total_passed / total_run_tests * 100, 1) if total_run_tests > 0 else 0

    # ── Coverage distribution ─────────────────────────────────────────────────
    cov_rows = db.query(GeneratedTest.coverage_pct).filter(GeneratedTest.coverage_pct.isnot(None)).all()
    cov_vals = [r[0] for r in cov_rows]
    cov_dist = {
        "high":   sum(1 for v in cov_vals if v >= 80),
        "medium": sum(1 for v in cov_vals if 50 <= v < 80),
        "low":    sum(1 for v in cov_vals if v < 50),
    }

    # ── Run / function counts ─────────────────────────────────────────────────
    total_runs = db.query(func.count(Run.id)).filter(Run.status == RunStatus.DONE).scalar() or 0
    total_functions = db.query(func.count(Function.id)).scalar() or 0
    total_bug_detections = db.query(func.count(TestFailure.id)).scalar() or 0
    runs_with_fixes = db.query(func.count(func.distinct(ProposedFix.function_id))).scalar() or 0

    # runs that have at least one test failure (bugs detected)
    runs_with_bugs = db.execute(text(
        "SELECT COUNT(DISTINCT r.id) FROM runs r "
        "JOIN functions f ON f.run_id = r.id "
        "JOIN generated_tests gt ON gt.function_id = f.id "
        "JOIN test_failures tf ON tf.generated_test_id = gt.id"
    )).scalar() or 0

    # ── Recent runs with per-run stats ────────────────────────────────────────
    runs = (
        db.query(Run)
        .filter(Run.status == RunStatus.DONE)
        .order_by(Run.created_at.desc())
        .limit(20)
        .all()
    )

    recent_runs = []
    for run in runs:
        fn_count = len(run.functions)
        r_passed = r_failed = 0
        cov_list = []
        bug_count = 0
        has_fix = False

        for fn in run.functions:
            for gt in fn.generated_tests:
                r_passed += gt.passed
                r_failed += gt.failed
                if gt.coverage_pct is not None:
                    cov_list.append(gt.coverage_pct)
                bug_count += len(gt.test_failures)
            if fn.proposed_fixes:
                has_fix = True

        r_total = r_passed + r_failed
        recent_runs.append({
            "id": run.id,
            "repo_url": run.repo_url,
            "function_name": run.function_name,
            "function_count": fn_count,
            "total_passed": r_passed,
            "total_failed": r_failed,
            "pass_rate": round(r_passed / r_total * 100, 1) if r_total > 0 else None,
            "avg_coverage_pct": round(sum(cov_list) / len(cov_list), 1) if cov_list else None,
            "bugs_detected": bug_count,
            "has_fix": has_fix,
            "created_at": run.created_at,
            "finished_at": run.finished_at,
        })

    # ── ChromaDB count (best-effort) ──────────────────────────────────────────
    rag_count = 0
    try:
        from vectordb import get_collection
        rag_count = get_collection().count()
    except Exception:
        pass

    return {
        "total_runs": total_runs,
        "total_functions": total_functions,
        "total_tests": total_tests,
        "total_passed": total_passed,
        "total_failed": total_failed,
        "pass_rate": pass_rate,
        "avg_coverage_pct": avg_coverage,
        "coverage_distribution": cov_dist,
        "total_bug_detections": total_bug_detections,
        "runs_with_bugs": runs_with_bugs,
        "runs_with_fixes": runs_with_fixes,
        "rag_examples": rag_count,
        "recent_runs": recent_runs,
    }
