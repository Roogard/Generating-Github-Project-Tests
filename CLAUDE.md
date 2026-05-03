# GGPT (Generating Github Project Tests)

An issue-driven AI agent that reads GitHub bug reports and writes regression
tests that reproduce the bug. Evaluated on **SWT-Bench Lite** (300 real
GitHub issues) using the F→P / F→F / P→F / P→P transition oracle.

The agent is given:
  1. A repo URL + base commit (or HF dataset row), already cloned and runnable.
  2. The issue text (and optional PR-review hints).

It localizes the relevant code itself via Claude Code-shaped tools (Glob,
Grep, Read, Edit, Write), writes a pytest file, and the harness auto-runs
pytest after any modification to the test file. The agent declares done by
emitting a final assistant message with no tool calls — the file on disk
IS the submission.

When the task carries a `gold_patch` (SWT-Bench / repos with a known fix),
the runner grades post-hoc: run tests on buggy → apply patch → run on fixed
→ label each test's transition. **Grading never feeds back into the agent
loop** — the agent must reproduce the bug from the issue alone.

---

## Architecture

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

Real iteration happens **inside Generate's agentic loop** — explore → write
→ run pytest → reflect → revise. The outer harness only invokes Improve
once, and only if the test file has infrastructure problems (collection
error, fixture failure, AttributeError on construction). Pytest assertion
failures do NOT trigger Improve — they may be the F→P detection we want.

---

## File structure

```
src/
  agent.py           run_agent(task) — single entrypoint, dispatches to harness
  runner.py          Runs adapters; persists Run rows; grades post-hoc
  llm.py             Provider plumbing (build_config, get_llm)
  test_runner.py     pytest runner (JSON report + per-test isolation)
  oracle.py          SWT-bench classifier + buggy↔fixed transitions + grade_with_oracle (post-hoc only)
  persist.py         Single persistence path (Run + Function rows)
  types.py           AgentTask, AgentResult, OracleGrade, RunBatch
  config.py          Centralized env-var configuration (single grep target)
  logging.py         Structured logging via structlog (console-pretty or JSON)
  text_utils.py      Code-fence stripping + truncation (single home, shared by harness/agentic/base)
  harness/
    __init__.py      Back-compat re-exports
    state.py         HarnessContext + BudgetExhausted + read/write_test_file
    feedback.py      Feedback + build_feedback (pytest result → next_action gate)
    pipeline.py      run_harness (Analyze → Generate → Improve(infra) → Critique → Improve(semantic) → Finalize)
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
    agentic.py       Reusable tool-using LLM loop (used by Generate + Improve)
    tools.py         Glob, Grep, Read, Edit, Write — Claude Code-shaped agent tool kit
    analyze.py       AnalyzeSkill — issue → JSON test plan
    generate.py      GenerateSkill — agentic; explores repo, writes tests
    improve.py       ImproveSkill — dual-mode: infrastructure (collection/setup failures) and semantic (Critique-driven, may re-explore)
    critique.py      CritiqueSkill — predicts F→P / F→F / P→F / P→P; needs_revision triggers semantic Improve
    prompts/         _shared.md + analyze.md + generate.md + improve.md + critique.md

api/
  app.py             FastAPI app + lifespan + SPA mount
  db.py              SQLite via SQLAlchemy
  models.py          ORM: Run, Function + RunStatus StrEnum
  routes.py          REST: /api/runs/* + /api/analytics/summary
  store.py           Thin DAL + summary_stats

webapp/              React + Vite dashboard — the only user-facing entry point
  src/pages/         RunsList, RunDetail, Benchmark, Analytics
```

---

## Running it

The web dashboard is the only entry point — there is no CLI.

**Prereqs:**
- Python 3.12 (managed by your `.venv`)
- Node 20+ for the webapp
- **Docker Desktop** (recommended) — used to isolate per-run pytest execution.
  - Generic image: `docker build -f Dockerfile.runtime -t ggpt-runtime .`
  - For SWT-Bench: per-instance official sweb images (`swebench/sweb.eval.x86_64.<instance>:latest`) are pulled on demand.

If Docker isn't available, the harness falls back to `LocalRuntime` (host
subprocess + uv venv if `uv` is on PATH). Set `GGPT_RUNTIME=local` to
force-skip Docker.

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

**Benchmarks:** the `/benchmark` page kicks off an SWT-Bench batch. Each HF
instance becomes its own Run in the DB; the Analytics page aggregates
F→P / F→F / P→F / P→P numbers per project and per provider.

---

## Metrics (per Run row in DB)

| Field | Meaning |
|-------|---------|
| `tests_passed` / `tests_failed` | Pytest outcomes on the buggy code |
| `tests_errored` | Pytest collection / setup errors on the buggy code |
| `patch_applied` | The gold patch applied cleanly (benchmark only) |
| `f2p` | **F→P — fail on buggy, pass on fixed (true positives)** |
| `f2f` | F→F — fail on both (spurious / false positives — the killer) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions) |
| `p2p` | P→P — pass on both (neutral) |
| `detected` | `f2p > 0` — at least one test transitions fail→pass |
| `resolved` | `f2p > 0 AND f2f == 0 AND p2f == 0` (SWT-bench primary metric) |

`f2p` / `f2f` / `p2f` / `p2p` are 0 on user-supplied (`mode='repo'`) runs
since there's no ground-truth fix.

---

## Guiding constraints

- All runs go through webapp → API → DB. No CLI entry points.
- The harness owns side effects (subprocess, file writes, runtime preamble).
  Skills are LLM calls — they don't run pytest or write files. The agentic
  loop's auto-pytest hook (fires after Write or Edit on `ctx.test_file_path`)
  routes through `ctx.runtime.exec` like everything else.
- All process invocations go through `ctx.runtime.exec(...)`. Never call
  `subprocess.run` directly from `test_runner.py` or `oracle.py` — adding
  it back breaks Docker isolation. Host-side `git apply` against the
  mounted clone is fine (oracle uses this on Local/Docker runtimes).
- The agent gets the issue, never the gold patch and never `touched_files`.
  Mirroring SWE-Agent / OpenHands / Otter — the agent must localize from
  the issue alone for fairness.
- Pytest assertion failures are NOT improve signals. Only collection /
  setup / timeout failures trigger Improve. Silencing an assertion that
  matches the issue would silence an F→P detection.
