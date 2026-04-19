# GitHub Project Test Generator

An agentic pipeline that clones a GitHub repo, extracts Python functions, generates unit tests using an LLM, runs them, and attempts to automatically fix any bugs it finds. Evaluated on BugsInPy with Claude Sonnet: **68% bug detection rate, 100% fix rate** on detected bugs. The main challenge was that the LLM sometimes wrote tests around the buggy behavior — tests that passed on broken code but failed once the fix was applied — requiring an oracle revision step after each fix.

---

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in your API key
cp .env.example .env

# Run on any public GitHub repo
uv run python main.py

# Or point it at a specific repo by editing REPOS in main.py
```

Configure what to run by editing the settings block at the top of [main.py](main.py):

```python
REPOS = ["https://github.com/user/repo"]   # regular repos
BUGSINPY_PROJECTS = ["black", "tqdm"]       # BugsInPy benchmark projects
```

Set your LLM provider and key in `.env`:

```
ANTHROPIC_API_KEY=...
LLM_PROVIDER=anthropic
LLM_MODEL=claude-sonnet-4-6
```

---

## Results

Evaluated on 20 bugs across 4 BugsInPy projects (black, tqdm, cookiecutter, tornado):

| Metric | Result |
|---|---|
| Bug detection rate | **68%** |
| Fix rate (on detected bugs) | **100%** |

"Detected" means the generated tests caught at least one failure on the buggy function. "Fixed" means the LLM's patch made all failures converge — including revising any test oracles that were written for the broken behavior.

---

## Web UI

The repo ships with a React + Vite dashboard (`webapp/`) backed by a FastAPI server (`api/`). The dashboard lets you kick off runs, browse generated tests, inspect the SQLite run history, and search the ChromaDB RAG memory.

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

Then browse to http://localhost:8000. SQLite and ChromaDB persist in the `ghtest_data` volume (`/data/ghtest.db`, `/data/chroma_db`).

### REST API endpoints

All routes are under `/api/` — see `webapp/src/api.js` for the client mirror.

| Prefix | File | Purpose |
|---|---|---|
| `/api/runs` | `api/routes.py` | Start / list / inspect / download / delete runs |
| `/api/db` | `api/db_routes.py` | Browse & query the SQLite store |
| `/api/vectordb` | `api/vectordb_routes.py` | ChromaDB stats, similarity search, delete examples |
| `/api/analytics` | `api/analytics_routes.py` | Aggregated dashboard summary |

Key run knobs (POST `/api/runs/`):

- `use_rag` — retrieve ChromaDB examples during generation (set `false` for a no-memory baseline)
- `save_to_rag` — ingest the generated tests back into ChromaDB
- `rag_success_only` — only ingest if ≥1 test passed
- `preset` — `fast` / `default` / `thorough` (affects per-test timeout)
- `function_limit` — cap how many functions are processed in whole-project mode
