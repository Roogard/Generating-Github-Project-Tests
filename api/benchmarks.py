from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from api.db import get_db
from api.models import BenchmarkRun

router = APIRouter(prefix="/api/benchmarks", tags=["benchmarks"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class BenchmarkRunIn(BaseModel):
    benchmark_name: str
    model: str
    provider: str
    project: str
    bug_id: str
    status: str           # detected | missed | error
    tests_passed: int = 0
    tests_failed: int = 0
    fix_attempted: bool = False
    fix_converged: bool = False
    elapsed_seconds: float = 0.0


class BenchmarkRunOut(BenchmarkRunIn):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class BenchmarkStats(BaseModel):
    benchmark_name: str
    model: str
    total: int
    detected: int
    detection_rate: float
    fix_attempted: int
    fix_converged: int
    convergence_rate: float
    avg_elapsed_seconds: float


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/import", status_code=201)
def import_benchmarks(records: list[BenchmarkRunIn], db: Session = Depends(get_db)):
    """Bulk-import benchmark run results."""
    rows = [BenchmarkRun(**r.model_dump()) for r in records]
    db.add_all(rows)
    db.commit()
    return {"imported": len(rows)}


@router.get("/stats", response_model=list[BenchmarkStats])
def get_stats(
    benchmark_name: str | None = None,
    model: str | None = None,
    db: Session = Depends(get_db),
):
    """Aggregate detection/fix stats grouped by benchmark_name + model."""
    q = db.query(BenchmarkRun)
    if benchmark_name:
        q = q.filter(BenchmarkRun.benchmark_name == benchmark_name)
    if model:
        q = q.filter(BenchmarkRun.model == model)

    rows = q.all()
    if not rows:
        return []

    # Group in Python (simpler than SQLAlchemy group_by for this shape)
    groups: dict[tuple, list] = {}
    for r in rows:
        key = (r.benchmark_name, r.model)
        groups.setdefault(key, []).append(r)

    stats = []
    for (bname, mname), group in sorted(groups.items()):
        total = len(group)
        detected = sum(1 for r in group if r.status == "detected")
        fix_att  = sum(1 for r in group if r.fix_attempted)
        fix_conv = sum(1 for r in group if r.fix_converged)
        avg_elapsed = sum(r.elapsed_seconds for r in group) / total
        stats.append(BenchmarkStats(
            benchmark_name=bname,
            model=mname,
            total=total,
            detected=detected,
            detection_rate=round(detected / total, 4),
            fix_attempted=fix_att,
            fix_converged=fix_conv,
            convergence_rate=round(fix_conv / fix_att, 4) if fix_att else 0.0,
            avg_elapsed_seconds=round(avg_elapsed, 2),
        ))
    return stats


@router.get("/", response_model=list[BenchmarkRunOut])
def list_benchmarks(
    benchmark_name: str | None = None,
    model: str | None = None,
    db: Session = Depends(get_db),
):
    """List benchmark runs, optionally filtered by benchmark_name and/or model."""
    q = db.query(BenchmarkRun)
    if benchmark_name:
        q = q.filter(BenchmarkRun.benchmark_name == benchmark_name)
    if model:
        q = q.filter(BenchmarkRun.model == model)
    return q.order_by(BenchmarkRun.created_at.desc()).all()
