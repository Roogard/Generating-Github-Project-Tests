# GHTest

Automated test generation for Python GitHub repositories using LLMs.
Generated tests that fail on the buggy codebase and pass after applying the ground-truth fix indicate a detected bug — this is the SWT-bench evaluation paradigm.

---

## What it does

1. Clones a repo (or a specific buggy commit from BugsInPy)
2. Extracts target Python functions via tree-sitter AST parsing
3. Generates whitebox + blackbox tests concurrently via an LLM
4. Runs tests with pytest and reports failures
5. In batch mode: applies the ground-truth fix patch and measures SWT-bench transitions (F→P, F→F, P→F, P→P)

---

## File structure

```
main.py            CLI entry point — single-function mode + BugsInPy batch mode
pipeline.py        Core orchestration: generate → write → run → parse failures
llm.py             LLM provider config + concurrent test generation (LangChain)
repo_utils.py      Git clone (HEAD or specific commit), tree-sitter function extraction
test_runner.py     pytest runner (JSON report) + coverage measurement (unused, available)
constraints.txt    Pinned versions for test runner + HTTP stack (pip --constraint)

src/prompts/
  whitebox.md      System prompt for structural/whitebox tests
  blackbox.md      System prompt for behavioural/blackbox tests

api/
  app.py           FastAPI app + CORS + lifespan (init_db)
  db.py            SQLite via SQLAlchemy — session factory + Base
  models.py        ORM: Run, Function, GeneratedTest, ProposedFix, BenchmarkRun
  routes.py        REST: POST/GET/DELETE /api/runs, background pipeline execution
  benchmarks.py    REST: POST /api/benchmarks/import, GET /api/benchmarks/stats
  constants.py     StrEnum constants: RunStatus, FixStatus, TestType
```

---

## Running it

**Whole project (primary deliverable):**
```
python main.py --project <repo_url_or_local_path> [--spec spec.md] [--provider deepseek|anthropic|openai|ollama] [--preset fast|default|thorough]
```
Recursively generates `test_<fn>_whitebox.py` + `test_<fn>_blackbox.py` for every function, plus a `conftest.py` and `run_tests.yml` (GitHub Actions).

**Single function:**
```
python main.py <repo_url> <function_name> [--provider deepseek|anthropic|openai|ollama] [--preset fast|default|thorough]
```

**BugsInPy batch (SWT-bench evaluation):**
```
python main.py --batch
# configure BUGSINPY_PROJECTS and BUGS_PER_PROJECT in main.py
```

**Re-analyze an existing results.json:**
```
python main.py --analyze eval_output/bugsinpy_<timestamp>/results.json
```

**API server:**
```
uvicorn api.app:app --reload
# or: ghtest-api  (via pyproject.toml script)
```

---

## SWT-bench metrics (results.json schema)

| Field | Meaning |
|-------|---------|
| `tests_run` | Total tests executed on buggy code |
| `tests_passed` | Tests passing on buggy code (not detecting bug) |
| `tests_failed` | Tests failing on buggy code (potential detections) |
| `tests_errored` | Collection / import errors |
| `patch_applied` | W — ground-truth patch applied cleanly |
| `f2p` | F→P — fail on buggy, pass on fixed (true positives) |
| `f2f` | F→F — fail on both (spurious / false positives) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions introduced) |
| `p2p` | P→P — pass on both (stable neutral tests) |
| `detected` | `tests_failed > 0` |
| `resolved` | S — `f2p > 0 AND f2f == 0 AND p2f == 0` (primary SWT-bench metric) |

---

## Current benchmark performance (BugsInPy, 9 bugs, DeepSeek)

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

- Do not break the existing `main.py` → `pipeline.py` → `llm.py` / `repo_utils.py` / `test_runner.py` call chain
- Keep each module single-purpose; extend rather than rewrite
- `test_runner.py` has `measure_coverage()` implemented but not yet wired into the pipeline — available for future use
