# GGPT — Generating Github Project Tests

GGPT is an AI agent that is capable of viewing GitHub issues, creating a test case to recreate the issue, and proposes a code fix for the issue. 

If you label any issue with `ggpt` the agent localizes the relevant code, writes a pytest file that reproduces the bug, and opens a PR closing the issue. Evaluated on [SWT-Bench Lite](https://swtbench.com/) — 79 real GitHub issues — using the F→P / F→F / P→F / P→P transition oracle. It is worth noting that the current highest success rate on SWT-Bench overall is a 56.2% resolved rate, which is only 8% higher than our run. 

<!-- screenshot: webapp /database page showing per-instance results. Drop into docs/img/database.png and reference here. -->

## Results

Run end-to-end on 79 SWT-Bench Lite instances (deepseek-chat, default preset, April 2026):

| Metric | Value |
|---|---|
| **Resolved** (SWT-Bench primary) | **48.1%** (38 / 79) |
| Detection rate (F→P > 0) | 48.1% (38 / 79) |
| F→P transitions (true positives) | 38 |
| F→F transitions (spurious) | 12 |
| P→F transitions (regressions) | 1 |

`resolved` is the strictest SWT-Bench metric: at least one test transitions fail→pass *and* no test transitions fail→fail or pass→fail. The shipped 79-instance batch is bundled into `data/featured.db`; the live Database tab in the webapp drills into every instance. Reproduce the headline numbers with `python -m scripts.featured_stats`.

## Set up

### 1. Add the workflow file

Add this as a file into your repo at **`.github/workflows/ggpt.yml`**:

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

Name it one of: `DEEPSEEK_API_KEY`, `ANTHROPIC_API_KEY`, or `OPENAI_API_KEY`. Whichever you set is the one GGPT uses (preference order: deepseek → anthropic → openai). It is worth noting that all data including API keys is kept strictly in your repo, and no other service including us gets access to any runs or API keys used with GGPT. 

### 3. Allow Actions to open PRs

**Settings → Actions → General → Workflow permissions** → check ✅ **"Allow GitHub Actions to create and approve pull requests"** and save. (Off by default on new repos; without it GGPT can write the test but can't open the PR.)

### 4. Create the trigger label

**Issues → Labels → New label** → name: `ggpt` → **Create label**. (Or `gh label create ggpt --repo <owner>/<repo>`.)

## How to use it

- **Label any issue with `ggpt`** → GGPT reads the issue body, generates a regression test, and opens a PR closing the issue.
- **Or comment `/ggpt` on an issue** → same thing.
- **On failure** → GGPT comments on the issue with a link to the action logs instead of opening a PR.

The PR adds one file: `tests/test_ggpt_issue_<n>.py` — a pytest regression test. Review it, tweak it if you want, and merge it like any other PR.

## How it works

The agent gets the issue text and a fresh clone of the repo at the base commit. It localizes the relevant code itself using Claude Code-shaped tools (`Glob`, `Grep`, `Read`, `Edit`, `Write`), writes a pytest file, and the harness auto-runs pytest after every modification so the agent can iterate against real feedback. A separate critique pass predicts whether each test will flip fail→pass once the bug is fixed; if the prediction is poor, a semantic improve pass re-explores.

When a gold patch is available (SWT-Bench), the runner grades post-hoc: run on buggy → apply patch → run on fixed → label each test's transition. **Grading never feeds back into the agent loop** — the agent must reproduce the bug from the issue alone, the way every fair benchmark requires.

<!-- pipeline diagram: ASCII pipeline diagram from ARCHITECTURE.md, or a polished SVG. Drop into docs/img/pipeline.svg and reference here. -->

For the full pipeline, file structure, runtime isolation, REST API, and local-dev instructions, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Tech stack

Python 3.12 · FastAPI · SQLAlchemy · React + Vite · Docker · SWT-Bench Lite · DeepSeek / Anthropic / OpenAI

<details>
<summary>Known limitation: the auto-PR doesn't trigger your CI</summary>

GitHub's anti-loop protection prevents the default `GITHUB_TOKEN` from triggering other workflows. The PR opens but your CI doesn't run on it automatically. Workarounds:

- Push an empty commit (`git commit --allow-empty -m "trigger ci"`) to wake CI, or
- Close and reopen the PR, or
- Swap `${{ github.token }}` for a personal access token (`GH_PAT`) inside the published workflow if you fork.

</details>
