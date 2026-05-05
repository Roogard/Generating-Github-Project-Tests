"""Build data/featured.db — the small, committable SQLite file that backs
the website's /database tab.

Source data:
  - Working DB (./ggpt.db) — copies the 79 SWT-Bench Lite Run rows + their
    Function rows from the FEATURED_BATCH (deepseek-chat, default preset,
    2026-04-30) into the fresh featured DB.
  - HuggingFace dataset princeton-nlp/SWE-bench_Lite — pulls the original
    GitHub issue body (`problem_statement`) for each instance and writes it
    onto the copied Run rows.

Run from the repo root:
    .venv/Scripts/python.exe -m scripts.build_featured_db

Idempotent — drops & recreates the featured DB on every run.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Allow running as `python -m scripts.build_featured_db` OR as a script.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.db import (
    SessionLocal,
    FeaturedSessionLocal,
    reset_featured_db,
    FEATURED_DB_PATH,
)
from api.models import Function, Run
from api.store import FEATURED_BATCH


def copy_featured_rows() -> list[int]:
    """Copy Run + Function rows for the FEATURED_BATCH from the working DB
    into a freshly-recreated featured DB. Returns the list of copied Run IDs.
    """
    reset_featured_db()

    src = SessionLocal()
    dst = FeaturedSessionLocal()
    try:
        from sqlalchemy import func
        rows = (
            src.query(Run)
            .filter(
                Run.status == "done",
                Run.mode == "swtbench",
                Run.dataset == FEATURED_BATCH["dataset"],
                Run.provider == FEATURED_BATCH["provider"],
                Run.model == FEATURED_BATCH["model"],
                Run.preset == FEATURED_BATCH["preset"],
                func.date(Run.created_at) == FEATURED_BATCH["date"],
            )
            .order_by(Run.id)
            .all()
        )
        if not rows:
            raise RuntimeError(
                f"No rows matched FEATURED_BATCH in source DB: {FEATURED_BATCH}"
            )

        copied_ids = []
        for r in rows:
            new_run = Run(
                id=r.id,
                repo_url=r.repo_url,
                mode=r.mode,
                benchmark_id=r.benchmark_id,
                dataset=r.dataset,
                status=r.status,
                error_message=r.error_message,
                # Output dir from the original run no longer exists on disk;
                # null it so the RunDetail download button stays hidden.
                output_dir=None,
                created_at=r.created_at,
                finished_at=r.finished_at,
                elapsed_seconds=r.elapsed_seconds,
                progress_current=r.progress_current,
                progress_total=r.progress_total,
                current_stage=None,
                provider=r.provider,
                model=r.model,
                preset=r.preset,
                tests_run=r.tests_run,
                tests_passed=r.tests_passed,
                tests_failed=r.tests_failed,
                tests_errored=r.tests_errored,
                f2p=r.f2p, f2f=r.f2f, p2f=r.p2f, p2p=r.p2p,
                patch_applied=r.patch_applied,
                detected=r.detected,
                resolved=r.resolved,
            )
            dst.add(new_run)
            for fn in r.functions:
                dst.add(Function(
                    run_id=fn.run_id,
                    name=fn.name,
                    test_code=fn.test_code,
                    tests_passed=fn.tests_passed,
                    tests_failed=fn.tests_failed,
                    history_json=fn.history_json,
                ))
            copied_ids.append(r.id)
        dst.commit()
        return copied_ids
    finally:
        src.close()
        dst.close()


def enrich_with_problem_statements(run_ids: list[int]) -> int:
    """Pull problem_statement from princeton-nlp/SWE-bench_Lite by instance_id
    and write it onto the matching featured Run rows. Returns count enriched.
    """
    from datasets import load_dataset

    print("Loading princeton-nlp/SWE-bench_Lite from HuggingFace...")
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split="test")
    by_instance = {row["instance_id"]: row["problem_statement"] for row in ds}
    print(f"  loaded {len(by_instance)} instances from HF")

    db = FeaturedSessionLocal()
    enriched = 0
    missing = []
    try:
        for rid in run_ids:
            run = db.get(Run, rid)
            if run is None:
                continue
            ps = by_instance.get(run.benchmark_id)
            if ps is None:
                missing.append(run.benchmark_id)
                continue
            run.problem_statement = ps
            enriched += 1
        db.commit()
    finally:
        db.close()

    if missing:
        print(f"  WARN: {len(missing)} instances had no HF match (left null): {missing[:5]}{'...' if len(missing) > 5 else ''}")
    return enriched


def main():
    print(f"Building featured DB at: {FEATURED_DB_PATH}")
    print(f"Filter: {FEATURED_BATCH}")
    ids = copy_featured_rows()
    print(f"Copied {len(ids)} Run rows (id range {min(ids)}–{max(ids)})")
    enriched = enrich_with_problem_statements(ids)
    print(f"Enriched {enriched} rows with HF problem statements")
    print("Done.")


if __name__ == "__main__":
    main()
