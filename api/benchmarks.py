from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
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
    instance_id: str = ""
    status: str = "ok"       # ok | error | no_patch | no_targets
    # Test counts on buggy code
    tests_run: int = 0
    tests_passed: int = 0
    tests_failed: int = 0
    tests_errored: int = 0
    # SWT-bench transitions
    patch_applied: bool = False   # W — applicability
    f2p: int = 0                  # F→P count
    f2f: int = 0                  # F→F count (spurious)
    p2f: int = 0                  # P→F count (regressions)
    p2p: int | None = None        # P→P count
    # Summary
    detected: bool = False
    resolved: bool = False        # S — primary SWT-bench metric
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
    resolved: int
    resolved_rate: float          # S — primary SWT-bench metric
    detected: int
    detection_rate: float
    applicable: int
    applicability_rate: float     # W
    total_f2p: int
    total_f2f: int
    total_p2f: int
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
        total      = len(group)
        n_resolved = sum(1 for r in group if r.resolved)
        n_detected = sum(1 for r in group if r.detected)
        n_applic   = sum(1 for r in group if r.patch_applied)
        tot_f2p    = sum(r.f2p for r in group)
        tot_f2f    = sum(r.f2f for r in group)
        tot_p2f    = sum(r.p2f for r in group)
        avg_elapsed = sum(r.elapsed_seconds for r in group) / total
        stats.append(BenchmarkStats(
            benchmark_name=bname,
            model=mname,
            total=total,
            resolved=n_resolved,
            resolved_rate=round(n_resolved / total, 4),
            detected=n_detected,
            detection_rate=round(n_detected / total, 4),
            applicable=n_applic,
            applicability_rate=round(n_applic / total, 4),
            total_f2p=tot_f2p,
            total_f2f=tot_f2f,
            total_p2f=tot_p2f,
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
