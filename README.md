# GGPT — Generating Github Project Tests

An issue-driven AI agent that reads GitHub bug reports and writes regression tests that reproduce the bug. Evaluated on **SWT-Bench Lite** (300 real GitHub issues) using the F→P / F→F / P→F / P→P transition oracle.

The agent is given a repo + base commit and the issue text. It localizes the relevant code itself via Claude Code-shaped tools (`Glob` / `Grep` / `Read` / `Edit` / `Write`), writes a pytest file, and the harness auto-runs pytest after any modification to the test file. When a gold patch is available (SWT-Bench), the runner grades post-hoc: run on buggy → apply patch → run on fixed → label each test's transition.

---

## Quick Start

```bash
# Install Python deps
uv sync

# Copy and fill in your API key
cp .env.example .env
```

Set provider and key in `.env`:

```
LLM_PROVIDER=deepseek
LLM_MODEL=deepseek-chat
DEEPSEEK_API_KEY=...
```

Other providers supported: `anthropic`, `openai`, `ollama`.

---

## Web UI

The React + Vite dashboard (`webapp/`) backed by a FastAPI server (`api/`) is the only entry point. There is no CLI — kick off runs, watch progress, browse generated tests, and review SWT-Bench oracle results from the browser.

### Dev (two terminals)

```bash
# Terminal 1 — backend on :8000
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

The FastAPI app auto-mounts `webapp/dist/` at `/` when it exists. Also available via the `ggpt-api` console script or `docker compose up --build`.

### Docker

```bash
cp .env.example .env   # fill in LLM key
docker compose up --build
```

Browse to http://localhost:8000. SQLite persists in the `ggpt_data` volume at `/data/ggpt.db`.

For per-run pytest isolation, build the runtime image once:

```bash
docker build -f Dockerfile.runtime -t ggpt-runtime .
```

If Docker isn't available, the harness falls back to a host subprocess (uv venv if `uv` is on PATH). Set `GGPT_RUNTIME=local` to force-skip Docker.

---

## Pages

- **Runs** — start a run from a repo URL + issue text, watch live progress, inspect generated test code.
- **Benchmark** — kick off an SWT-Bench Lite or Verified batch. Each instance becomes its own run.
- **Analytics** — F→P / F→F / P→F / P→P aggregates per project and per provider.

## REST API

| Prefix | File | Purpose |
|---|---|---|
| `/api/runs` | [api/routes.py](api/routes.py) | Create / list / inspect / download / delete runs (single endpoint dispatched by `source: 'repo' \| 'swtbench'`) |
| `/api/analytics` | [api/routes.py](api/routes.py) | Read-only summary feeding the Analytics page |

`POST /api/runs/` body (issue-driven):

- `source: 'repo'` — requires `repo_url` + `issue_text`. Optional `hints_text`, `install_deps`.
- `source: 'swtbench'` — requires `dataset` (`swtbench_lite` | `swtbench_verified`). Optional `instance_limit`, `instance_ids`, `use_official_images`.
- Shared: `provider`, `model`, `preset` (`fast` | `default` | `thorough`), `api_key`.

---

## Metrics (per Run row in DB)

| Field | Meaning |
|---|---|
| `tests_passed` / `tests_failed` | Pytest outcomes on the buggy code |
| `tests_errored` | Pytest collection / setup errors on the buggy code |
| `patch_applied` | The gold patch applied cleanly (benchmark only) |
| `f2p` | **F→P — fail on buggy, pass on fixed (true positives)** |
| `f2f` | F→F — fail on both (spurious / false positives) |
| `p2f` | P→F — pass on buggy, fail on fixed (regressions) |
| `p2p` | P→P — pass on both (neutral) |
| `detected` | `f2p > 0` |
| `resolved` | `f2p > 0 AND f2f == 0 AND p2f == 0` (SWT-Bench primary metric) |

`f2p` / `f2f` / `p2f` / `p2p` are 0 on user-supplied (`mode='repo'`) runs — there's no ground-truth fix.

See [CLAUDE.md](CLAUDE.md) for architecture details.
