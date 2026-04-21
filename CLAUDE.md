# GGPT (Generating Github Project Tests)

Automated test generation for Python GitHub repositories using LLMs.
Generated tests that fail on the buggy codebase and pass after applying the ground-truth fix indicate a detected bug — this is the SWT-bench evaluation paradigm.

---

## What it does

1. Clones a repo (or a buggy/fixed pair from QuixBugs for benchmark mode)
2. Extracts target Python functions via tree-sitter AST parsing
3. Generates whitebox + blackbox tests concurrently via an LLM
4. Runs tests with pytest and reports failures + coverage
5. In benchmark mode: applies the ground-truth fix patch and measures SWT-bench transitions (F→P, F→F, P→F, P→P)

---

## File structure

```
src/
  pipeline.py      Core orchestration: generate → write → run → parse failures → measure coverage
  llm.py           LLM provider config + concurrent test generation (LangChain)
  repo_utils.py    Git clone (HEAD or specific commit), tree-sitter function extraction
  test_runner.py   pytest runner (JSON report) + per-file coverage measurement
  vectordb.py      ChromaDB wrapper — RAG few-shot retrieval for test generation
  benchmarks.py    QuixBugs batch driver, invoked by the API
  prompts/
    whitebox.md    System prompt for structural/whitebox tests
    blackbox.md    System prompt for behavioural/blackbox tests

api/
  app.py           FastAPI app + CORS + lifespan (init_db) + SPA mount
  db.py            SQLite via SQLAlchemy — session factory + Base
  models.py        ORM: Run, Function (cascade delete)
  routes.py        REST: /api/runs/* + /api/runs/benchmark (admin)
  browser_routes.py REST: /api/vectordb/*, /api/analytics/summary
  store.py         Thin DAL + benchmark-interpreter summary_stats
  auth.py          Admin passcode gate (X-Admin-Key header)
  constants.py     StrEnum constants: RunStatus, TestType

webapp/            React + Vite dashboard — the only user-facing entry point
  src/pages/       RunsList, NewRun, RunDetail, BenchmarkRun (admin),
                   VectorDB, Analytics
```

---

## Running it

The web dashboard is the only entry point — there is no CLI.

**Dev (two terminals):**
```
uvicorn api.app:app --reload
cd webapp && npm install && npm run dev
```
Open http://localhost:5173.

**Production bundle (one terminal):**
```
cd webapp && npm run build
cd .. && uvicorn api.app:app
```
FastAPI auto-mounts `webapp/dist/` at `/`. Also available via `ggpt-api` console script or `docker compose up --build`.

**Benchmarks:** the `/runs/benchmark` page (admin-gated) kicks off a QuixBugs batch. Each program becomes its own Run in the DB; the Analytics page aggregates the SWT metrics and compares base vs RAG.

---

## SWT-bench metrics (per Run row in DB)

| Field | Meaning |
|-------|---------|
| `tests_passed` | Tests passing on buggy code (not detecting bug) |
| `tests_failed` | Tests failing on buggy code (potential detections) |
| `patch_applied` | W — ground-truth patch applied cleanly |
| `f2p` | F→P — fail on buggy, pass on fixed (true positives) |
| `f2f` | F→F — fail on both (spurious / false positives) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions introduced) |
| `p2p` | P→P — pass on both (stable neutral tests) |
| `detected` | `f2p > 0` — at least one test transitions fail→pass under the oracle |
| `resolved` | S — `f2p > 0 AND f2f == 0 AND p2f == 0` (primary SWT-bench metric) |

---

## Historical benchmark performance (BugsInPy, 9 bugs, DeepSeek — prior evaluation)

| Metric | Result |
|--------|--------|
| S (Resolved) | 0 / 9 (0%) |
| Detected | 8 / 9 (89%) |
| W (Applicability) | 8 / 9 (89%) |
| F→P total | 40 |
| F→F total | 98 |
| P→F total | 21 |

**Primary bottleneck:** F→F dominance — generated tests fail on both buggy and fixed code, preventing any instance from reaching S=1 even when F→P > 0.

---

## Guiding constraints

- All runs go through the webapp → API → DB. Do not add CLI entry points.
- Keep each module single-purpose; extend rather than rewrite.
- `src/pipeline.py` calls `test_runner.measure_coverage()` per generated test file — coverage is a wired feature, not a spare.
