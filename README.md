# GGPT — Generating Github Project Tests

An issue-driven AI agent that reads GitHub bug reports and writes regression tests that reproduce the bug. Evaluated on **SWT-Bench Lite** (300 real GitHub issues) using the F→P / F→F / P→F / P→P transition oracle.

The agent is given a repo + base commit and the issue text. It localizes the relevant code itself via Claude Code-shaped tools (`Glob` / `Grep` / `Read` / `Edit` / `Write`), writes a pytest file, and the harness auto-runs pytest after any modification to the test file. When a gold patch is available (SWT-Bench), the runner grades post-hoc: run on buggy → apply patch → run on fixed → label each test's transition.

There are two ways to use it:

1. **GitHub Action** (recommended for everyday use) — drop a workflow file into your repo, label an issue with `ggpt`, get a PR. No backend, no hosting, runs in your repo's GitHub Actions runner. See [Use as a GitHub Action](#use-as-a-github-action) below.
2. **Local webapp** (for SWT-Bench benchmarking and ad-hoc runs) — a React dashboard backed by FastAPI for kicking off batch evaluations. See [Web UI](#web-ui) below.

---

## Use as a GitHub Action

Setup is one workflow file plus one secret. Once installed, **future capabilities** (`fix`, `refactor`, …) work on the same setup — adopters never need to come back and edit anything.

### Adopter setup

1. Drop [examples/workflows/ggpt-issue.yml](examples/workflows/ggpt-issue.yml) into your repo at `.github/workflows/ggpt.yml`.
2. Add at least one provider key under **Settings → Secrets and variables → Actions**:
   - `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`
3. Create a label called `ggpt` on the repo.

### Usage

- Apply the `ggpt` label to any issue → GGPT writes a regression test and opens a PR closing the issue.
- Or comment `/ggpt` on the issue → same flow.
- On failure (empty issue body, agent crash, no test produced), GGPT comments on the issue with a link to the action logs instead of opening a PR.

### Known limitation: PRs don't trigger CI

GitHub's anti-loop protection prevents the default `GITHUB_TOKEN` from firing other workflows. The auto-opened PR shows up but CI doesn't run on it. Workarounds:

- Push an empty commit to the PR branch (`git commit --allow-empty -m "trigger ci"`) to wake CI up, or
- Close and re-open the PR, or
- Replace `${{ github.token }}` references in the workflow with a personal access token stored as `GH_PAT` (gives the action a non-default identity that *can* trigger CI).

### Future capabilities, no re-setup

The trigger filter in the adopter template catches any label starting with `ggpt` and any comment starting with `/ggpt`. As new modes ship in this repo (e.g. `ggpt-fix` → `fix`), adopters get them automatically — the workflow file never needs to change. The only thing that does need to grow is the optional set of LLM provider secrets, if a genuinely new provider is added later.

---

## Quick Start

```bash
# Install Python deps (with the webapp + benchmark extras)
uv sync --all-extras

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

The React + Vite dashboard (`webapp/`) backed by a FastAPI server (`api/`) is the local entry point for SWT-Bench batch evaluation and manual runs against arbitrary repos. Kick off runs, watch progress, browse generated tests, and review SWT-Bench oracle results from the browser.

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
