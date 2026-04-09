# GHTest — Architecture & Implementation Plan

## What this project is

An automated bug-detection system that generates unit tests for Python GitHub repositories using LLMs. Generated tests that fail indicate potential bugs. The pipeline also attempts to fix detected bugs via LLM diagnosis and patching.

---

## Guiding constraints

- Do NOT rewrite existing pipeline modules unless strictly necessary — extend them
- `src/extractor.py`, `src/writer.py`, `src/runner.py`, `src/reporter.py` must remain unchanged
- Add new modules/files rather than modifying everything
- Keep file structure clean and each module single-purpose

---

## Target directory structure

```
project/
  src/
    extractor.py              # UNCHANGED — clone repo, AST extract functions
    writer.py                 # UNCHANGED — write tests/artifacts to disk
    runner.py                 # UNCHANGED — run pytest, return structured results
    reporter.py               # UNCHANGED — parse failures, format bug reports
    config.py                 # KEEP — Hydra wraps it, doesn't replace it
    agents.py                 # EXTEND: add generate_with_critique()
    coverage.py               # NEW — run coverage.py, return CoverageInfo per fn
    critic.py                 # NEW — LLM critic that targets uncovered lines
    prompts/
      whitebox.md             # UNCHANGED
      blackbox.md             # UNCHANGED
      critic.md               # NEW — coverage critic system prompt
  api/
    __init__.py
    app.py                    # FastAPI app + BackgroundTasks
    db.py                     # SQLite + SQLAlchemy setup
    models.py                 # ORM models: Run, Function, GeneratedTest, ProposedFix
    vector_db.py              # NEW — ChromaDB connection + embed/query/delete helpers
    routes/
      runs.py                 # POST /api/runs, GET /api/runs, GET /api/runs/{id}, DELETE /api/runs/{id}
      tests.py                # GET/PUT /api/runs/{id}/tests/{test_id}
      fixes.py                # GET/PUT /api/runs/{id}/fixes/{fix_id}
      search.py               # NEW — GET /api/similar, GET /api/patterns, GET /api/stats, GET /api/functions
  conf/
    config.yaml               # Hydra base config
    llm/
      anthropic.yaml
      openai.yaml
      deepseek.yaml
      ollama.yaml
    pipeline/
      default.yaml            # max_iterations=3, threshold=80, convergence_delta=2
      fast.yaml               # max_iterations=1, threshold=70
      thorough.yaml           # max_iterations=5, threshold=90
  run.py                      # Hydra CLI entry point
  pipeline.py                 # MODIFY: add coverage loop, make run_for_functions importable
  Dockerfile
  docker-compose.yml          # local dev only
  .github/
    workflows/
      ci.yml                  # lint + test on PRs
      deploy.yml              # build + deploy on merge to main
```

---

## Implementation phases (do one at a time)

### Phase 1 — Coverage loop

**1. `src/coverage.py`** (no project imports, pure subprocess + stdlib)

```python
def measure_coverage(test_file: str, fn: dict, repo_clone_dir: str, timeout: int = 60) -> dict
```

Returns `CoverageInfo`:
```python
{
    "covered_lines": list[int],
    "uncovered_lines": list[int],
    "coverage_pct": float,          # 0.0–100.0
    "fn_start_line": int,
    "fn_end_line": int,
    "fn_source_lines": dict[int, str],  # uncovered line_num -> source text
    "error": str | None,
}
```

Implementation notes:
- Use `tempfile.mktemp(suffix=".coverage")` for `--data-file` (prevents collisions)
- `python -m coverage run --data-file={tmp} --include={abs_fn_path} --branch -m pytest {test_file} -q`
- `python -m coverage json --data-file={tmp} -o {tmp_json}`
- Normalize paths with `os.path.normcase(os.path.normpath(...))` for Windows compat
- Filter lines to `[fn["start_line"], fn["end_line"]]`
- Cleanup temp files in `finally`
- On any error: return `{"coverage_pct": 0.0, "error": str(e), ...}`

**2. `src/prompts/critic.md`**

System prompt for the coverage critic LLM. Output format (required exactly):
```
## Critique
<3-10 bullets naming specific uncovered branches/lines>

## Improved Whitebox Tests
```python
<complete revised file>
```

## Improved Blackbox Tests
```python
<complete revised file>
```
```
Rules: ADD tests, never remove existing ones. Comment each new test `# covers line(s) N-M`. Apply same Two-Phase Rule from whitebox.md. Output BOTH files even if only one changed.

**3. `src/critic.py`**

```python
def call_critic_agent(fn, test_code, coverage_info, config) -> dict
# Returns: {"critique": str, "improved_code": {"whitebox": str, "blackbox": str}, "error": str | None}
```

Imports `get_llm` from `src/agents.py`. No circular import — `agents.py` imports `critic` deferred inside a function body.

**4. Add to `src/agents.py`** (bottom of file only)

```python
def generate_with_critique(fn, config, coverage_info=None) -> dict
# generate whitebox + blackbox, then if coverage_info: run critic and merge improved results
# Returns: {"whitebox": str, "blackbox": str, "critique": str, "critic_error": str | None}
```

Use `from src.critic import call_critic_agent` as a deferred import inside the function body.

**5. Modify `pipeline.py`**

Add constants:
```python
COVERAGE_THRESHOLD = 80.0
MAX_COVERAGE_ITERATIONS = 3
COVERAGE_CONVERGENCE_DELTA = 2.0
```

Add helper:
```python
def _run_coverage_for_fn(fn, output_dir, repo_dir, index) -> dict | None
# Tries test_whitebox.py and test_blackbox.py, skips files with errors,
# returns CoverageInfo with highest coverage_pct, or None
```

Wrap generation block in `run_for_functions` with coverage loop:
```
initial generation (call_agent whitebox + blackbox) — UNCHANGED
write_generated_tests — UNCHANGED

for iteration in 1..MAX_COVERAGE_ITERATIONS:
    cov = _run_coverage_for_fn(...)
    if cov is None: break                          # collection errors
    if cov["coverage_pct"] >= COVERAGE_THRESHOLD: break
    if iteration > 1 and delta < CONVERGENCE_DELTA: break
    result = generate_with_critique(fn, config, coverage_info=cov)
    write_generated_tests(fn, result, output_dir, index)  # overwrites in-place
```

Everything after (generate_automation, run tests, fix phase, oracle revision) — untouched.

---

### Phase 2 — Hydra config

`conf/config.yaml` (base):
```yaml
defaults:
  - llm: anthropic
  - pipeline: default
output_dir: outputs/${now:%Y-%m-%d_%H-%M-%S}
repo_url: ""
limit: null
```

`conf/llm/anthropic.yaml`:
```yaml
provider: anthropic
model: claude-sonnet-4-6
api_key_env: ANTHROPIC_API_KEY
```

`conf/pipeline/default.yaml`:
```yaml
max_iterations: 3
coverage_threshold: 80.0
convergence_delta: 2.0
test_timeout: 60
```

`run.py` — Hydra entry point:
```python
@hydra.main(config_path="conf", config_name="config")
def main(cfg: DictConfig):
    config = OmegaConf.to_container(cfg, resolve=True)
    # calls run_for_functions from pipeline.py
```

CLI: `python run.py llm=openai pipeline=thorough repo_url=https://...`
Sweep: `python run.py -m llm=anthropic,openai pipeline=default,fast`

Make `pipeline.py` importable: expose `run_for_functions` and `run_pipeline` as top-level functions. Keep `if __name__ == "__main__"` for backwards compat.

---

### Phase 3 — FastAPI backend

**`api/db.py`**: SQLite via SQLAlchemy
```python
DATABASE_URL = "sqlite:///./ghtest.db"
```

**`api/models.py`** — four tables:
- `Run`: id, repo_url, status, config (JSON blob), created_at, finished_at, output_dir
- `Function`: id, run_id (FK), name, file_path, source
- `GeneratedTest`: id, function_id (FK), test_type, code (editable), iteration, coverage_pct
- `ProposedFix`: id, function_id (FK), fixed_code (editable), diagnosis, iteration, status

**`api/app.py`** — BackgroundTasks pattern:
```python
@router.post("/")
def create_run(body, background_tasks, db):
    run = Run(status="pending", ...)
    db.add(run); db.commit()
    background_tasks.add_task(execute_pipeline, run.id, body.config)
    return {"id": run.id}
```

`execute_pipeline` calls `run_for_functions` from `pipeline.py`, writes results to DB alongside existing file output.

**`api/vector_db.py`** — ChromaDB client module:
```python
# Functions:
#   embed_function(fn, test_code, bug_description, run_id) -> None
#     Called after a fix is accepted — embeds function source + diagnosis into ChromaDB
#     Metadata stored: fn_name, repo_url, bug_description, run_id
#
#   query_similar(fn_source, n_results=5) -> list[dict]
#     Semantic similarity search — returns top-N past bug cases similar to the given function
#     Used by the LLM prompt builder and by GET /api/similar
#
#   list_patterns() -> list[dict]
#     Returns all stored embeddings with their metadata (for the Bug Pattern Library UI)
#
#   delete_pattern(pattern_id) -> None
#     Removes a single pattern by ID (for DELETE /api/patterns/{id})
```
Collection name: `"bug_patterns"`. Client: `chromadb.PersistentClient(path="./chroma_db")`.

**Key routes:**
| Method | Path | DB | Purpose |
|--------|------|----|---------|
| POST | /api/runs | SQLite | Start a pipeline run |
| GET | /api/runs | SQLite | List all runs (filter by ?status=, ?repo=) |
| GET | /api/runs/{id} | SQLite | Run status + summary |
| DELETE | /api/runs/{id} | SQLite | Delete run + cascade to child tables (completes CRUD) |
| GET | /api/runs/{id}/tests | SQLite | All generated tests for a run |
| PUT | /api/runs/{id}/tests/{test_id} | SQLite | Edit a test in web UI |
| GET | /api/runs/{id}/fixes | SQLite | All proposed fixes for a run |
| PUT | /api/runs/{id}/fixes/{fix_id} | SQLite | Edit / accept / reject a fix |
| GET | /api/stats | SQLite | Dashboard stats: bugs found, avg coverage, fix success rate |
| GET | /api/functions?coverage_lt=X | SQLite | Filter functions below coverage threshold (embedded query) |
| GET | /api/similar?function_id=X | ChromaDB | Semantic search — similar past functions/bugs |
| GET | /api/patterns | ChromaDB | Browse all stored bug patterns |
| DELETE | /api/patterns/{id} | ChromaDB | Remove a stale pattern from the collection |

---

### Phase 4 — Docker + CI/CD

**`Dockerfile`**:
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml .
RUN pip install uv && uv sync
COPY . .
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

**`docker-compose.yml`** (local dev only — no Redis, no separate worker):
```yaml
services:
  app:
    build: .
    ports: ["8000:8000"]
    volumes:
      - ./data:/app/data
    env_file: .env
```

**`.github/workflows/ci.yml`** — on PR: `uv sync` → `ruff check src/ api/` → `pytest tests/`

**`.github/workflows/deploy.yml`** — on merge to main: build image, push to Railway/Render (Railway/Render auto-deploy from GitHub handles the rest)

---

### Phase 5 — Frontend (React)

**Stack:** Vite + React + TypeScript. All data fetched from FastAPI routes — no direct DB access from browser.

**Page structure:**
```
Dashboard
  ├── Run History — table of all runs, filter by status/repo, delete button
  │     └── [click] → Run Detail
  │           ├── Summary stats cards (bugs found, avg coverage %, fix acceptance rate)
  │           ├── Functions table (sortable by coverage %, filterable by name)
  │           │     └── [click] → Function Detail
  │           │           ├── Generated tests (code editor, saved via PUT)
  │           │           ├── Coverage % per iteration (sparkline chart)
  │           │           ├── Proposed fixes (accept/reject buttons via PUT)
  │           │           └── Similar Past Bugs panel (ChromaDB query result)
  │           └── Link to raw output files
  └── Bug Pattern Library — browse ChromaDB embeddings via GET /api/patterns
        └── [click] → pattern detail + delete button
```

**Key demo moments for class presentation:**
- Submit a repo URL → run created in SQLite → live status polling
- Filter functions by `coverage_lt=50` → demonstrates embedded SQL query
- Click "Similar Past Bugs" on a function → demonstrates ChromaDB semantic search vs SQL limitation
- Edit a test → PUT to SQLite → demonstrates Update
- Delete a run → demonstrates Delete + cascade

---

## Database design (for class project)

This project intentionally uses **two data store paradigms**:

**SQLite (via SQLAlchemy)** — relational structured data
- Stores: runs, functions, generated tests, proposed fixes
- Full CRUD: create runs, read/filter by status/coverage/repo, update tests + fixes, delete runs with cascade
- Embedded queries: `WHERE coverage_pct < 50`, aggregate stats (bug count, avg coverage, fix rate)
- Strength: ACID guarantees, joins across tables, exact-value filtering
- Limitation: can only find things by exact or range-matched values — not by meaning

**ChromaDB** — vector database for semantic memory
- Stores: embeddings of confirmed bug patterns (function source + LLM diagnosis) after a fix is accepted
- Queried by semantic similarity — "find past functions that had similar bugs to this one"
- Cannot be replaced by SQL: a function named `tokenize()` and one named `split_input()` doing similar things won't match on keywords, but will match on vector similarity
- CRUD equivalent: `embed_function` (create), `query_similar` / `list_patterns` (read), metadata update, `delete_pattern` (delete)
- Strength: meaning-based retrieval; also feeds context back into the LLM prompt on the next run

**How they interact:**
1. Pipeline runs → SQLite records created for every function, test, fix
2. User accepts a fix in the UI → `embed_function()` called → ChromaDB stores the pattern
3. Next run on a similar repo → `query_similar()` retrieves past cases → injected into LLM prompt → better tests generated

---

## New dependencies to add to `pyproject.toml`

```
fastapi>=0.115
uvicorn[standard]>=0.30
sqlalchemy>=2.0
hydra-core>=1.3
omegaconf>=2.3
coverage>=7.0      # or rely on pytest-cov's transitive install
chromadb>=0.4
```

---

## Verification checklist

- Phase 1: `python pipeline.py` on a small repo — confirm coverage % printed per iteration, test files overwritten in-place
- Phase 2: `python run.py llm=anthropic pipeline=fast repo_url=...` — confirm Hydra config used
- Phase 3: `uvicorn api.app:app` → POST /api/runs → poll until done → GET /api/runs/{id}/tests
- Phase 4: `docker-compose up` → repeat API checks against container → open PR to verify CI → merge to verify deploy
