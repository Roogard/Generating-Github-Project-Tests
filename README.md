# GGPT — Generating Github Project Tests

An issue-driven AI agent that reads GitHub bug reports and writes regression tests that reproduce them — installed as a GitHub Action, triggered by a label.

## Set it up (4 steps, ~2 minutes)

### 1. Add the workflow file

Drop this into your repo at **`.github/workflows/ggpt.yml`**:

```yaml
name: GGPT
on:
  issues:
    types: [labeled]
  issue_comment:
    types: [created]

jobs:
  ggpt:
    if: |
      (github.event_name == 'issues' &&
       startsWith(github.event.label.name, 'ggpt')) ||
      (github.event_name == 'issue_comment' &&
       startsWith(github.event.comment.body, '/ggpt'))
    uses: Roogard/Generating-Github-Project-Tests/.github/workflows/ggpt.yml@main
    permissions:
      contents: write
      pull-requests: write
      issues: write
    secrets: inherit
```

### 2. Add an LLM API key as a repo secret

**Settings → Secrets and variables → Actions → New repository secret**

Name it one of: `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`. Paste your key as the value. Whichever you set is the one GGPT uses (preference order: deepseek → anthropic → openai).

### 3. Allow Actions to open PRs

**Settings → Actions → General → Workflow permissions**

Check ✅ **"Allow GitHub Actions to create and approve pull requests"** and save. (Off by default on new repos; without it GGPT can write the test but can't open the PR.)

### 4. Create the trigger label

**Issues → Labels → New label** → name: `ggpt` → **Create label**.

(Or from a terminal: `gh label create ggpt --repo <owner>/<repo>`.)

## How to use it

- **Label any issue with `ggpt`** → GGPT reads the issue body, generates a regression test, and opens a PR closing the issue.
- **Or comment `/ggpt` on an issue** → same thing.
- **On failure** (empty issue body, agent crash, no test produced) → GGPT comments on the issue with a link to the action logs instead of opening a PR.

## What you get

The PR adds one file: `tests/test_ggpt_issue_<n>.py` — a pytest regression test that reproduces the bug described in the issue. Review it, tweak it if you want, and merge it like any other PR.

### Known limitation: the auto-PR doesn't fire your CI

GitHub's anti-loop protection prevents the default `GITHUB_TOKEN` from triggering other workflows. The PR opens but your CI doesn't run on it automatically. Workarounds:

- Push an empty commit (`git commit --allow-empty -m "trigger ci"`) to wake CI, or
- Close and reopen the PR, or
- Swap `${{ github.token }}` for a personal access token (`GH_PAT`) inside [the published workflow](.github/workflows/ggpt.yml) if you fork.

## Future capabilities — no re-setup

The trigger filter catches **any** label starting with `ggpt` and **any** comment starting with `/ggpt`. As new modes ship in this repo (`ggpt-fix` → write a fix, `ggpt-refactor` → propose a refactor, etc.), they work on your existing workflow file with **zero edits**. New LLM providers may eventually need a new secret name, but nothing else.

---

## How it works

The agent is given a repo + base commit and the issue text. It localizes the relevant code itself via Claude Code-shaped tools (`Glob` / `Grep` / `Read` / `Edit` / `Write`), writes a pytest file, and the harness auto-runs pytest after any modification to the test file. When a gold patch is available (SWT-Bench), the runner grades post-hoc: run on buggy → apply patch → run on fixed → label each test's transition.

Evaluated on **SWT-Bench Lite** (300 real GitHub issues) using the F→P / F→F / P→F / P→P transition oracle.

---

## Local development & SWT-Bench benchmarking

The bits below are for working on GGPT itself or running benchmark evaluations — adopters using the action don't need any of this.

### Quick Start

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
