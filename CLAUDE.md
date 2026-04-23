# GGPT (Generating Github Project Tests)

Automated test generation for Python GitHub repositories using an agentic LLM loop.
Generated tests that fail on the buggy codebase and pass after applying the ground-truth
fix indicate a detected bug — the SWT-bench evaluation paradigm.

---

## What it does

1. Clones a repo (or a buggy/fixed pair from QuixBugs in benchmark mode).
2. Extracts target Python functions via tree-sitter.
3. Hands each function to an agent with tools (`view_function`, `run_tests`,
   `view_coverage`, `check_oracle_stability` in benchmark mode,
   `search_similar_tests`, `view_golden_example`, `write_test_file`, `finish`).
4. The agent iterates — write → run → observe failures/coverage → revise —
   up to a preset-controlled turn budget (default 4).
5. In benchmark mode the agent can directly observe F→P / F→F / P→F labels
   per test and revise spurious ones before calling `finish`.
6. Final metrics are persisted to SQLite and surfaced on the Analytics page.

---

## File structure

```
src/
  pipeline.py        Clone → extract → run_agent per fn → persist
  llm.py             Provider plumbing (build_config, get_llm). No generation logic.
  repo_utils.py      Git clone, tree-sitter function extraction
  test_runner.py     pytest runner (JSON report) + per-function coverage
  vectordb.py        ChromaDB — single bucket, retrieve_examples(query, k)
  benchmarks.py      QuixBugs batch driver (populate / measure phases)
  agent/
    __init__.py      Re-exports TestGenEnv, run_agent
    env.py           TestGenEnv — state, tools, summary (oracle bookkeeping)
    tools.py         LangChain @tool wrappers over env methods
    loop.py          run_agent — hand-rolled tool-calling loop (~50 lines)
    prompts/
      system.md      Single system prompt
    examples/
      golden/        Hand-curated exemplar pairs
      dynamic/       Placeholder — Chroma RAG lives at ./chroma_db/

api/
  app.py             FastAPI app + CORS + lifespan (init_db) + SPA mount
  db.py              SQLite via SQLAlchemy — session factory + Base
  models.py          ORM: Run, Function (single test_code column)
  routes.py          REST: /api/runs/* + /api/runs/benchmark
  browser_routes.py  REST: /api/vectordb/*, /api/analytics/summary
  store.py           Thin DAL + benchmark-interpreter summary_stats
  auth.py            Admin passcode gate (X-Admin-Key header)
  constants.py       StrEnum: RunStatus

webapp/              React + Vite dashboard — the only user-facing entry point
  src/pages/         RunsList, NewRun, RunDetail, BenchmarkRun,
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
FastAPI auto-mounts `webapp/dist/` at `/`. Also available via `ggpt-api`
console script or `docker compose up --build`.

**Benchmarks:** the `/runs/benchmark` page (admin-gated) kicks off a QuixBugs
batch. Each program becomes its own Run in the DB; the Analytics page
aggregates SWT metrics and compares populate vs measure / with-RAG vs baseline.

**First run after pulling this branch:** the schema changed (single `test_code`
column on Function). Reset the DB before starting:
```
python -c "from api.db import reset_db; reset_db()"
```
or delete `ggpt.db`.

---

## SWT-bench metrics (per Run row in DB)

| Field | Meaning |
|-------|---------|
| `tests_passed` | Tests passing on buggy code |
| `tests_failed` | Tests failing on buggy code |
| `patch_applied` | W — ground-truth patch applied cleanly |
| `f2p` | F→P — fail on buggy, pass on fixed (true positives) |
| `f2f` | F→F — fail on both (spurious / false positives) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions introduced) |
| `p2p` | P→P — pass on both (stable neutral tests) |
| `detected` | `f2p > 0` — at least one test transitions fail→pass |
| `resolved` | S — `f2p > 0 AND f2f == 0 AND p2f == 0` (primary SWT-bench metric) |

---

## Historical baseline (pre-agent, BugsInPy 9 bugs, DeepSeek)

| Metric | Result |
|--------|--------|
| S (Resolved) | 0 / 9 (0%) |
| Detected | 8 / 9 (89%) |
| F→P total | 40 |
| F→F total | 98 |
| P→F total | 21 |

**Bottleneck:** F→F dominance. Tests failed on both buggy and fixed code
because the single-shot pipeline never ran them. The agentic loop addresses
this by giving the agent `check_oracle_stability` in benchmark mode —
spurious tests become visible mid-loop and can be revised before `finish`.

---

## Guiding constraints

- All runs go through webapp → API → DB. No CLI entry points.
- Keep modules single-purpose; extend the agent under `src/agent/` rather
  than growing `pipeline.py`.
- Coverage is measured on the agent's final test file (see
  `TestGenEnv.summary`) — it is a wired feature, not a spare.
- Golden examples live at `src/agent/examples/golden/`. Add new ones when a
  pattern proves itself — they're always available via `view_golden_example`.
