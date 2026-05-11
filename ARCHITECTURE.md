# Architecture

GGPT is an issue-driven agent that reads a GitHub bug report and writes a regression test that reproduces it. It ships as a reusable GitHub Action *and* as a local web dashboard for batch evaluation against [SWT-Bench Lite](https://swtbench.com/).

This document covers the internals. For setup and adopter-facing usage, see [README.md](README.md).

---

## Pipeline

```
       SwtBenchAdapter           RepoAdapter (issue_text REQUIRED)
       (HF dataset row)          (user-supplied repo + issue)
              │                          │
              └────────────┬─────────────┘
                           │  yields RunBatch — one IssueTask per row
                           ▼
                       Runner
                           │
                           ▼
                   run_agent(task)
                           │
                           ▼
                   run_harness(task)
                           │
                           ▼
              Analyze → Generate (agentic) → maybe Improve(infra) → Critique → maybe Improve(semantic)
                           │
                           ▼
                  ctx.read_test_file()  → AgentResult
                           │
                           ▼
              grade_with_oracle(task, result)   (post-hoc; only if gold_patch)
                           │
                           ▼
              persist_function_result
```

Real iteration happens **inside Generate's agentic loop** — explore → write → run pytest → reflect → revise. The outer harness only invokes Improve once, and only if the test file has *infrastructure* problems (collection error, fixture failure, AttributeError on construction). Pytest assertion failures do NOT trigger Improve — they may be the F→P detection we want.

When the task carries a `gold_patch` (SWT-Bench rows), the runner grades post-hoc: run tests on buggy → apply patch → run on fixed → label each test's transition. **Grading never feeds back into the agent loop** — the agent must reproduce the bug from the issue alone.

---

## File structure

```
src/
  agent.py           run_agent(task) — single entrypoint, dispatches to harness
  runner.py          Runs adapters; persists Run rows; grades post-hoc
  llm.py             Provider plumbing (build_config, get_llm)
  test_runner.py     pytest runner (JSON report + per-test isolation)
  oracle.py          SWT-bench classifier + buggy↔fixed transitions + grade_with_oracle
  persist.py         Single persistence path (Run + Function rows)
  types.py           AgentTask, AgentResult, OracleGrade, RunBatch
  config.py          Centralized env-var configuration
  logging.py         Structured logging via structlog (console-pretty or JSON)
  text_utils.py      Code-fence stripping + truncation
  harness/
    state.py         HarnessContext + BudgetExhausted + read/write_test_file
    feedback.py      Feedback + build_feedback (pytest result → next_action gate)
    pipeline.py      run_harness (Analyze → Generate → Improve(infra) → Critique → Improve(semantic))
  inputs/
    base.py          InputAdapter ABC + PRESETS
    repo.py          RepoAdapter — (URL, issue_text) → AgentTask
    swtbench.py      SwtBenchAdapter — HF row → AgentTask
  runtime/
    base.py          Runtime ABC + RuntimeResult
    local.py         Host subprocess + optional uv venv
    docker.py        `docker run --rm` against ggpt-runtime image
    swtbench.py      Per-instance official sweb image with /testbed preamble
    factory.py       Auto-selects via GGPT_RUNTIME env var
  skills/
    base.py          Skill base class — prompt loading, single LLM call
    agentic.py       Reusable tool-using LLM loop (Generate + Improve)
    tools.py         Glob, Grep, Read, Edit, Write — Claude Code-shaped tool kit
    analyze.py       AnalyzeSkill — issue → JSON test plan
    generate.py      GenerateSkill — agentic; explores repo, writes tests
    improve.py       ImproveSkill — dual-mode: infrastructure + semantic
    critique.py      CritiqueSkill — predicts F→P / F→F / P→F / P→P
    prompts/         _shared.md + per-skill prompt files

api/
  app.py             FastAPI app + lifespan + SPA mount
  db.py              SQLite via SQLAlchemy
  models.py          ORM: Run, Function + RunStatus StrEnum
  routes.py          REST: /api/runs/* + /api/analytics/summary
  store.py           Thin DAL + featured_batch aggregation

webapp/              React + Vite dashboard — local entry point
  src/pages/         Runs, Benchmark, Database, Analytics
```

---

## Running locally

The web dashboard is the local entry point for SWT-Bench batches and manual runs against arbitrary repos.

**Prereqs:**
- Python 3.12 (managed by your `.venv`)
- Node 20+ for the webapp
- **Docker Desktop** (recommended) for per-run pytest isolation:
  - Generic image: `docker build -f Dockerfile.runtime -t ggpt-runtime .`
  - For SWT-Bench: per-instance official sweb images (`swebench/sweb.eval.x86_64.<instance>:latest`) pulled on demand.

If Docker isn't available, the harness falls back to `LocalRuntime` (host subprocess + uv venv if `uv` is on PATH). Set `GGPT_RUNTIME=local` to force-skip Docker.

### Dev (two terminals)

```bash
# Terminal 1 — backend on :8000
uv sync --all-extras
cp .env.example .env   # then fill in your LLM key
python -m uvicorn api.app:app --reload

# Terminal 2 — frontend dev server on :5173 (proxies /api to :8000)
cd webapp && npm install && npm run dev
```

Open http://localhost:5173.

### Production bundle (one terminal)

```bash
cd webapp && npm run build   # emits webapp/dist
cd .. && uvicorn api.app:app # serves API + built frontend on :8000
```

FastAPI auto-mounts `webapp/dist/` at `/` when it exists. Also via the `ggpt-api` console script or `docker compose up --build`.

### Provider configuration

`.env` supports four providers — set `LLM_PROVIDER` and the matching key:

```
LLM_PROVIDER=deepseek   # deepseek | anthropic | openai | ollama
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=...
```

---

## Web dashboard pages

- **Runs** — start a run from a repo URL + issue text, watch live progress, inspect generated test code.
- **Benchmark** — kick off an SWT-Bench Lite or Verified batch. Each instance becomes its own run.
- **Database** — the 79-run SWT-Bench Lite batch shipped with `data/featured.db`. Per-instance results, sortable, linked back to the original GitHub issues.
- **Analytics** — F→P / F→F / P→F / P→P aggregates per project and per provider.

---

## REST API

| Prefix | File | Purpose |
|---|---|---|
| `/api/runs` | [api/routes.py](api/routes.py) | Create / list / inspect / download / delete runs (dispatched by `source: 'repo' \| 'swtbench'`) |
| `/api/analytics` | [api/routes.py](api/routes.py) | Read-only summary for the Analytics page |

`POST /api/runs/` body:

- `source: 'repo'` — requires `repo_url` + `issue_text`. Optional `hints_text`, `install_deps`.
- `source: 'swtbench'` — requires `dataset` (`swtbench_lite` | `swtbench_verified`). Optional `instance_limit`, `instance_ids`, `use_official_images`.
- Shared: `provider`, `model`, `preset` (`fast` | `default` | `thorough`), `api_key`.

---

## Metrics

Each Run row in the DB carries these fields:

| Field | Meaning |
|---|---|
| `tests_passed` / `tests_failed` | Pytest outcomes on the buggy code |
| `tests_errored` | Collection / setup errors on the buggy code |
| `patch_applied` | The gold patch applied cleanly (benchmark only) |
| `f2p` | **F→P — fail on buggy, pass on fixed (true positives)** |
| `f2f` | F→F — fail on both (spurious / false positives — the killer) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions) |
| `p2p` | P→P — pass on both (neutral) |
| `detected` | `f2p > 0` — at least one test transitions fail→pass |
| `resolved` | `f2p > 0 AND f2f == 0 AND p2f == 0` (SWT-Bench primary metric) |

`f2p` / `f2f` / `p2f` / `p2p` are 0 on user-supplied (`mode='repo'`) runs since there's no ground-truth fix.

The shipped numbers in [README.md](README.md) are computed by [scripts/featured_stats.py](scripts/featured_stats.py) reading [data/featured.db](data/featured.db) via [api/store.py](api/store.py)'s `featured_batch()`.

---

## Guiding constraints

- All runs go through webapp → API → DB. No CLI entry points.
- The harness owns side effects (subprocess, file writes, runtime preamble). Skills are LLM calls — they don't run pytest or write files. The agentic loop's auto-pytest hook (fires after Write or Edit on `ctx.test_file_path`) routes through `ctx.runtime.exec` like everything else.
- All process invocations go through `ctx.runtime.exec(...)`. Never call `subprocess.run` directly from `test_runner.py` or `oracle.py` — adding it back breaks Docker isolation. Host-side `git apply` against the mounted clone is fine (oracle uses this on Local/Docker runtimes).
- The agent gets the issue, never the gold patch and never `touched_files`. Mirroring SWE-Agent / OpenHands / Otter — the agent must localize from the issue alone for fairness.
- Pytest assertion failures are NOT improve signals. Only collection / setup / timeout failures trigger Improve. Silencing an assertion that matches the issue would silence an F→P detection.
