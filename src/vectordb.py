"""ChromaDB vector store for RAG-based test generation.

Embeds function source code so that semantically similar past examples
can be retrieved as few-shot context before LLM test generation calls.
"""
import hashlib

import chromadb

import os as _os
CHROMA_PATH = _os.environ.get("CHROMA_PATH", "./chroma_db")
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
    whitebox_code: str,
    blackbox_code: str,
    passed: int = 0,
    failed: int = 0,
    coverage_pct: float | None = None,
) -> None:
    """Embed fn['source'] and upsert whitebox + blackbox test records.

    Uses the function source as the embedding anchor so future queries
    against a new function's source retrieve structurally similar examples.
    Silent no-op on any exception so the pipeline is never blocked.
    """
    try:
        source = fn.get("source", "")
        if not source or not source.strip():
            return
        collection = get_collection()
        source_hash = hashlib.sha256(source.encode()).hexdigest()[:16]
        fn_name = fn.get("name", "unknown")
        fn_file = fn.get("file_path", "")
        base_meta = {
            "fn_name": fn_name,
            "fn_file": fn_file,
            "fn_source": source,
            "repo_url": repo_url,
            "passed": passed,
            "failed": failed,
            "coverage_pct": coverage_pct if coverage_pct is not None else -1.0,
        }
        records = [
            ("whitebox", whitebox_code),
            ("blackbox", blackbox_code),
        ]
        ids, documents, metadatas = [], [], []
        for test_type, test_code in records:
            if not test_code or not test_code.strip():
                continue
            ids.append(f"fn_{source_hash}_{test_type}")
            documents.append(source)
            metadatas.append({**base_meta, "test_type": test_type, "test_code": test_code})
        if ids:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
    except Exception:
        pass


def retrieve_examples(
    fn_source: str,
    test_type: str,
    n_results: int = 3,
) -> list[dict]:
    """Return up to n_results past examples whose function source is semantically similar.

    Each result: {fn_name, fn_source, test_code, passed, failed, coverage_pct}
    Returns [] on empty collection, wrong test_type filter, or any exception.
    """
    try:
        if not fn_source or not fn_source.strip():
            return []
        collection = get_collection()
        if collection.count() == 0:
            return []
        results = collection.query(
            query_texts=[fn_source],
            n_results=min(n_results, collection.count()),
            where={"test_type": test_type},
        )
        examples = []
        for meta in (results.get("metadatas") or [[]])[0]:
            cov = meta.get("coverage_pct", -1.0)
            examples.append({
                "fn_name": meta.get("fn_name", ""),
                "fn_source": meta.get("fn_source", ""),
                "test_code": meta.get("test_code", ""),
                "passed": meta.get("passed", 0),
                "failed": meta.get("failed", 0),
                "coverage_pct": cov if cov >= 0 else None,
            })
        return examples
    except Exception:
        return []
