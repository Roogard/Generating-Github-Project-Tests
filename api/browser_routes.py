"""Read-only browse endpoints — vector DB browser + analytics summary.

  /api/vectordb/*   — read-only ChromaDB browser (Vector DB page)
  /api/analytics/*  — benchmark-interpreter dashboard (Analytics page)
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api import store
from api.db import get_db

router = APIRouter()


# ═════════════════════════════════════════════════════════════════════════════
#   Read-only Vector DB browser   (/api/vectordb/*)
# ═════════════════════════════════════════════════════════════════════════════

vector_router = APIRouter(prefix="/api/vectordb", tags=["vectordb"])


@vector_router.get("/stats")
def vector_stats():
    try:
        from src.vectordb import get_collection
        col = get_collection()
        return {"count": col.count(), "collection_name": col.name}
    except Exception as e:
        return {"count": 0, "collection_name": "generated_tests", "error": str(e)}


@vector_router.post("/search")
def vector_search(body: dict):
    query = (body.get("query") or "").strip()
    test_type = body.get("test_type", "whitebox")
    n = min(int(body.get("n", 3)), 20)
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    try:
        from src.vectordb import retrieve_examples
        return {"results": retrieve_examples(query, test_type, n_results=n)}
    except Exception as e:
        return {"results": [], "error": str(e)}


@vector_router.get("/examples")
def list_examples(page: int = 1, limit: int = 20, test_type: str = ""):
    try:
        from src.vectordb import get_collection
        col = get_collection()
        count = col.count()
        if count == 0:
            return {"total": 0, "page": page, "limit": limit, "examples": []}

        where = {"test_type": test_type} if test_type else None
        offset = (page - 1) * limit

        kwargs: dict = {"include": ["metadatas", "documents"], "limit": limit, "offset": offset}
        if where:
            kwargs["where"] = where
        results = col.get(**kwargs)

        examples = []
        ids = results.get("ids", [])
        metas = results.get("metadatas") or []
        for i, meta in enumerate(metas):
            cov = meta.get("coverage_pct", -1)
            examples.append({
                "id": ids[i] if i < len(ids) else "",
                "fn_name": meta.get("fn_name", ""),
                "fn_file": meta.get("fn_file", ""),
                "repo_url": meta.get("repo_url", ""),
                "test_type": meta.get("test_type", ""),
                "passed": meta.get("passed", 0),
                "failed": meta.get("failed", 0),
                "coverage_pct": cov if cov >= 0 else None,
                "test_code": meta.get("test_code", ""),
            })
        return {"total": count, "page": page, "limit": limit, "examples": examples}
    except Exception as e:
        return {"total": 0, "page": page, "limit": limit, "examples": [], "error": str(e)}


# ═════════════════════════════════════════════════════════════════════════════
#   Analytics summary   (/api/analytics/*)
# ═════════════════════════════════════════════════════════════════════════════

analytics_router = APIRouter(prefix="/api/analytics", tags=["analytics"])


@analytics_router.get("/summary")
def get_summary(db: Session = Depends(get_db)):
    return store.summary_stats(db)


router.include_router(vector_router)
router.include_router(analytics_router)
