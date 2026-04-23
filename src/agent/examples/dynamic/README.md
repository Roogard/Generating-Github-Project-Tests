# Dynamic examples (Chroma RAG)

This folder is intentionally empty. The dynamic example store lives outside
the repo at `./chroma_db/` (configurable via `CHROMA_PATH`).

## How it's populated

During the QuixBugs benchmark's `populate` phase, any run where the agent
produces a test suite with `f2p > 0` and `f2f == 0` (i.e. `resolved=True`)
is ingested via [src/vectordb.py](../../../vectordb.py) `ingest_example`.
Each entry stores the function source + the agent's final `test_agent.py`.

## How it's retrieved

The agent can query this store mid-loop via `search_similar_tests(query, k)`.
The query embeds against function source; the top-k similar entries are
returned with their generated test code.

## Why this folder exists

To make the distinction explicit: golden examples ship in-repo and are
reviewed by hand; dynamic examples are grown from benchmark runs and live
on disk at `./chroma_db/`. Both are discoverable by the agent but through
different tools.
