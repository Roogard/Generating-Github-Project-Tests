# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Automatically generate unit tests for every function in any GitHub repository. Given a GitHub repo URL, the system extracts all Python functions via tree-sitter, generates unit tests per function using a multi-agent LangGraph approach, and writes organized output folders.

Uses an ML-guided strategy selection approach: an offline dataset generation phase runs all 7 agents + mutation testing to build training data, then trained sklearn regressors predict per-agent kill rates. A greedy set cover algorithm selects the minimum agent subset that maximizes mutant coverage — avoiding the cost of running all 7 agents for every function.

## Current Status

### Working
- **Function extraction** — clone any repo, parse with tree-sitter, extract all Python functions
- **Agent code** — LangGraph graph with 7 parallel nodes + prompt files all written
- **Output writer** — `write_function()` and `write_tests()` both implemented
- **Test runner** — `runner.py` executes generated tests with pytest, produces results.json
- **Feature extraction** — `features.py` extracts ~25 structural AST features per function
- **ML model** — `model.py` trains per-agent kill-rate regressors, greedy set cover selects agents
- **Dataset pipeline** — `dataset.py` orchestrates offline dataset generation
- **Mutation testing** — `mutator.py` integrates mutmut for measuring test effectiveness
- **CLI args** — `main.py` accepts --repo, --output, --concurrency, --guided, --model, --limit
- **Docker** — Dockerfile builds and runs

### Not Yet Validated
- **End-to-end dataset generation** — pipeline written but not yet run against real repos
- **Model training** — requires generated dataset first
- **Guided mode** — requires trained model first

## Commands

```bash
# Install dependencies
uv sync

# Run test generation (standard mode — all 7 agents)
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Run test generation (guided mode — ML-selected agents)
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs --guided --threshold 0.05

# Generate training dataset (offline, expensive)
uv run python -m src.dataset --repos data/repos.json --output data/dataset.json --concurrency 1

# Train ML model
uv run python -m src.model --dataset data/dataset.json --output data/model.pkl

# Run generated tests
uv run python -m src.runner --output ./outputs/repo_name

# Lint
uv run ruff check src/

# Docker build & run
docker build -t ghtest .
docker run -e ANTHROPIC_API_KEY=$ANTHROPIC_API_KEY -v $(pwd)/output:/output ghtest
```

Copy `.env.example` to `.env` and fill in your API key before running locally.

## Architecture

```
src/
├── main.py          # Entry point + CLI args + async runner
├── extractor.py     # clone repo + tree-sitter function extraction (Python only)
├── agents.py        # LLM factory + LangGraph state/nodes/graph
├── writer.py        # write output folders
├── runner.py        # execute generated tests with pytest, produce results.json
├── features.py      # extract ~25 structural AST features per function
├── model.py         # train sklearn classifiers + predict useful agents
├── mutator.py       # mutmut integration + unique kill computation
├── dataset.py       # offline dataset generation pipeline
└── prompts/         # per-agent system prompts (editable .md files)
    ├── statement.md # whitebox: statement coverage
    ├── block.md     # whitebox: block coverage
    ├── condition.md # whitebox: condition coverage
    ├── path.md      # whitebox: path coverage
    ├── bva.md       # blackbox: boundary value analysis
    ├── ecp.md       # blackbox: equivalence class partitioning
    └── mutation.md  # blackbox: mutation testing

data/
├── repos.json       # curated list of training repos
├── dataset.json     # generated dataset (features → agent effectiveness)
└── model.pkl        # trained sklearn classifiers
```

### Pipeline Flows

**Standard mode:** `clone → extract functions → run all 7 agents → write tests`

**Guided mode:** `clone → extract functions → extract features → predict kill rates → greedy select agents → run selected agents → write tests`

**Dataset generation (offline):** `clone repos → extract functions → extract features → run all 7 agents → run tests → mutmut → store kill vectors → write dataset`

### Key Modules

- `extractor.py` — clones repo, walks `.py` files with `os.walk`, parses with tree-sitter, returns plain dicts with `name`, `source`, `language`, `file_path`, `imports`
- `agents.py` — `build_graph(selected_agents=None)` creates a LangGraph `StateGraph` with parallel fan-out. Accepts optional agent subset for guided mode
- `features.py` — `extract_features(fn)` re-parses function source with tree-sitter, walks AST in single pass, returns dict of ~25 numeric features (complexity, branches, loops, etc.)
- `model.py` — trains one `GradientBoostingRegressor` per agent type predicting kill rate. `predict_agents(fn, threshold)` uses greedy set cover to select agents maximizing coverage with diminishing returns. Guarantees at least 2 agents
- `mutator.py` — `run_mutmut()` runs mutmut in isolated temp dir, returns killed/survived mutant sets. `compute_unique_kills()` finds per-agent unique contribution
- `dataset.py` — orchestrates full dataset generation across curated repos. Entry point: `python -m src.dataset`
- `writer.py` — `write_function()` writes the source file; `write_tests()` writes test files per function
- `runner.py` — `run_single_test()` executes one test file with pytest in subprocess; `run_tests()` aggregates results

## Prompt Files (`src/prompts/`)

Each agent has its own `.md` file. Edit these to tune agent behaviour — no Python changes needed.

## LLM Configuration

| Env var | Default | Description |
|---|---|---|
| `LLM_MODEL` | `claude-haiku-4-5` | Anthropic model name |
| `ANTHROPIC_API_KEY` | — | Required |

## TODO — Remaining Work

### Immediate (validate pipeline)
- [ ] Run dataset generation on one small repo to validate end-to-end
- [ ] Train model on generated dataset, inspect feature importances
- [ ] Test guided mode with trained model
- [ ] Verify Docker image works with CLI args

### CI/CD
- [ ] Create `.github/workflows/run-tests.yml`
- [ ] Workflow: checkout → install deps → run pipeline → execute tests → report results

### Future
- [ ] Evaluation framework comparing guided vs all-agents coverage
- [ ] BugsInPy benchmark for real-world validation
- [ ] Test set minimization (greedy selection for smallest high-coverage suite)

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes
