# GitHub Project Test Generator

An agentic pipeline that clones a GitHub repo, extracts Python functions, generates unit tests using an LLM, and runs them. Evaluated on BugsInPy with Claude Sonnet: **68% bug detection rate** — generated tests catch a failure on the buggy function when one exists.

---

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in your API key
cp .env.example .env
```

Set your LLM provider and key in `.env`:

```
ANTHROPIC_API_KEY=...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

Then launch the web UI (see below) — all runs go through the dashboard.

---

## Results

Evaluated on 20 bugs across 4 BugsInPy projects (black, tqdm, cookiecutter, tornado):

| Metric | Result |
|---|---|
| Bug detection rate | **68%** |

"Detected" means the generated tests caught at least one failure on the buggy function.

---

## Web UI

The repo ships with a React + Vite dashboard (`webapp/`) backed by a FastAPI server (`api/`). The dashboard is the only entry point — kick off runs, browse generated tests, compare base-vs-RAG benchmark results, and search the ChromaDB RAG memory.

### Dev setup (two terminals)

```bash
# Terminal 1 — backend on :8000
uvicorn api.app:app --reload

# Terminal 2 — frontend dev server on :5173 (proxies /api to :8000)
cd webapp
npm install
npm run dev
```

Open http://localhost:5173.

### Production bundle (one terminal)

```bash
cd webapp && npm run build   # emits webapp/dist
cd .. && uvicorn api.app:app # serves API + built frontend on http://localhost:8000
```

The FastAPI app auto-mounts `webapp/dist/` at `/` when it exists.

### Docker

```bash
cp .env.example .env   # fill in LLM key
docker compose up --build
```

Then browse to http://localhost:8000. SQLite and ChromaDB persist in the `ggpt_data` volume (`/data/ggpt.db`, `/data/chroma_db`).

### REST API endpoints

All routes are under `/api/` — see `webapp/src/api.js` for the client mirror.

| Prefix | File | Purpose |
|---|---|---|
| `/api/runs` | `api/routes.py` | Start / list / inspect / download / delete runs; start benchmarks (admin) |
| `/api/vectordb` | `api/browser_routes.py` | ChromaDB stats, similarity search, example browser |
| `/api/analytics` | `api/browser_routes.py` | Benchmark-interpreter summary (SWT totals, base vs RAG, per-project/provider) |

Key run knobs (POST `/api/runs/`):

- `use_rag` — retrieve ChromaDB examples during generation (set `false` for a no-memory baseline)
- `preset` — `fast` / `default` / `thorough` (affects per-test timeout)
- `function_limit` — cap how many functions are processed in whole-project mode

Benchmarks (QuixBugs) run via the admin-gated `/runs/benchmark` page — each program becomes its own Run and feeds the Analytics dashboard automatically.

Promoting a run into memory is a separate, explicit step — every run persists to
SQLite, and you opt in to adding it to ChromaDB afterward via either:

- `POST /api/runs/{id}/promote-to-memory`, or
- the **📥 Promote to memory** button on the run detail page (admin-only).

Each run can be promoted at most once; the `promoted_to_memory_at` timestamp on the run record
tracks when it happened.
