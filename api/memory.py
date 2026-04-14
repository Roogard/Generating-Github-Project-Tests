"""
RAG memory endpoints — backed by ChromaDB.

Current status: stubs that return correctly-shaped responses.
ChromaDB wiring is a TODO once Page 3 is prioritised.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/api/memory", tags=["memory"])

# ── Schemas ───────────────────────────────────────────────────────────────────

class EmbedRequest(BaseModel):
    function_source: str
    fn_name: str
    repo_url: str
    diagnosis: str
    run_id: int | None = None


class PatternOut(BaseModel):
    pattern_id: str
    fn_name: str
    repo_url: str
    diagnosis: str


class SimilarPatternOut(PatternOut):
    similarity: float


# ── Routes ────────────────────────────────────────────────────────────────────

@router.post("/embed", status_code=201)
def embed_pattern(body: EmbedRequest):
    """Store a confirmed bug pattern in ChromaDB.

    Called after a proposed fix is accepted — embeds the function source +
    diagnosis so future similar functions can retrieve this as context.

    TODO: wire up ChromaDB (chromadb.PersistentClient).
    """
    import uuid
    return {"status": "embedded", "pattern_id": str(uuid.uuid4())}


@router.get("/similar", response_model=list[SimilarPatternOut])
def get_similar(function_source: str, k: int = 5):
    """Return the top-k most semantically similar past bug patterns.

    Query ChromaDB by embedding the supplied function_source and finding
    nearest neighbours in the bug-patterns collection.

    TODO: wire up ChromaDB query.
    """
    return []


@router.get("/patterns", response_model=list[PatternOut])
def list_patterns():
    """Return all stored bug patterns (for browsing the pattern library).

    TODO: wire up chromadb collection.get().
    """
    return []


@router.delete("/{pattern_id}", status_code=204)
def delete_pattern(pattern_id: str):
    """Remove a bug pattern from ChromaDB by ID.

    TODO: wire up chromadb collection.delete().
    """
    return
