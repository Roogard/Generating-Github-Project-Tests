"""Print aggregate SWT-Bench Lite stats from data/featured.db.

Source of the headline numbers quoted in the README. Reuses
`api.store.featured_batch` so this stays in lockstep with what the
website's /database page shows.

Run from the repo root:
    .venv/Scripts/python.exe -m scripts.featured_stats
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.db import FeaturedSessionLocal
from api.store import featured_batch


def main() -> None:
    db = FeaturedSessionLocal()
    try:
        result = featured_batch(db)
    finally:
        db.close()
    s = result["summary"]
    print(f"dataset:        {s['dataset']}")
    print(f"provider/model: {s['provider']} / {s['model']}")
    print(f"preset:         {s['preset']}")
    print(f"date:           {s['date']}")
    print(f"total runs:     {s['total']}")
    print()
    print(f"resolved:       {s['resolved']:>3}  ({s['resolved_rate']}%)")
    print(f"detected (F->P): {s['detected']:>3}  ({s['detection_rate']}%)")
    print()
    print(f"F->P (true positives):  {s['f2p']}")
    print(f"F->F (spurious):        {s['f2f']}")
    print(f"P->F (regressions):     {s['p2f']}")
    print(f"P->P (neutral):         {s['p2p']}")


if __name__ == "__main__":
    main()
