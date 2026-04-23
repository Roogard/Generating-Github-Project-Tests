"""ChromaDB RAG memory — one bucket per `(function, test_agent.py)` pair.

The agent calls `retrieve_examples(query, k)` on demand (see `src/agent/tools.py`).
The QuixBugs populate phase calls `ingest_example` for runs that pass the oracle.
"""
from __future__ import annotations
import chromadb
import os

CHROMA_PATH = os.environ.get("CHROMA_PATH", "./chroma_db")
COLLECTION_NAME = "generated_tests"

_client: chromadb.PersistentClient | None = None
_collection: chromadb.Collection | None = None


def get_collection() -> chromadb.Collection:
    global _client, _collection
    if _collection is None:
        _client = chromadb.PersistentClient(path=CHROMA_PATH)
        _collection = _client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},
        )
    return _collection


def ingest_example(
    fn: dict,
    repo_url: str,
    test_code: str,
    passed: int = 0,
    failed: int = 0,
    coverage_pct: float | None = None,
) -> None:
    """Store one `(function, test_agent.py)` pair. Idempotent on fn_name."""
    if not test_code or not test_code.strip():
        return
    source = fn["source"]
    fn_name = fn["name"]
    collection = get_collection()

    meta = {
        "fn_name": fn_name,
        "fn_file": fn.get("file_path", ""),
        "fn_source": source,
        "repo_url": repo_url,
        "passed": passed,
        "failed": failed,
        "coverage_pct": coverage_pct if coverage_pct is not None else -1.0,
        "test_code": test_code,
    }
    collection.upsert(ids=[fn_name], documents=[source], metadatas=[meta])


def retrieve_examples(query: str, n_results: int = 3) -> list[dict]:
    """Return up to n_results similar stored examples. Embeds `query` against fn_source."""
    collection = get_collection()
    if collection.count() == 0:
        return []
    results = collection.query(
        query_texts=[query],
        n_results=min(n_results, collection.count()),
    )
    examples = []
    for meta in results["metadatas"][0]:
        examples.append({
            "fn_name": meta["fn_name"],
            "fn_source": meta["fn_source"],
            "test_code": meta["test_code"],
            "passed": meta["passed"],
            "failed": meta["failed"],
        })
    return examples
