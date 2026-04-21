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
    whitebox_code: str,
    blackbox_code: str,
    passed: int = 0,
    failed: int = 0,
    coverage_pct: float | None = None,
) -> None:
    source = fn["source"]
    fn_name = fn["name"]
    collection = get_collection()

    base_meta = {
        "fn_name": fn_name,
        "fn_file": fn.get("file_path", ""),
        "fn_source": source,
        "repo_url": repo_url,
        "passed": passed,
        "failed": failed,
        "coverage_pct": coverage_pct or -1.0,
    }

    ids, documents, metadatas = [], [], []
    for test_type, test_code in [("whitebox", whitebox_code), ("blackbox", blackbox_code)]:
        if test_code:
            ids.append(f"{fn_name}_{test_type}")
            documents.append(source)
            metadatas.append({**base_meta, "test_type": test_type, "test_code": test_code})

    collection.upsert(ids=ids, documents=documents, metadatas=metadatas)


def retrieve_examples(fn_source: str, test_type: str, n_results: int = 3) -> list[dict]:
    collection = get_collection()
    if collection.count() == 0:
        return []

    matching_ids = collection.get(where={"test_type": test_type}, include=[])["ids"]
    match_count = len(matching_ids)
    if match_count == 0:
        return []

    results = collection.query(
        query_texts=[fn_source],
        n_results=min(n_results, match_count),
        where={"test_type": test_type},
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
