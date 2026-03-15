# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Automatically generate unit tests for every function in any GitHub repository. Given a GitHub repo URL, the system extracts all Python functions via tree-sitter, generates unit tests per function using a multi-agent LangGraph approach, and writes organized output folders.

Uses a supervisor LLM to intelligently select which test generation agents to run for each function. The supervisor analyzes the function's structure and picks 2-4 agents (from 7 available) whose strengths match — avoiding the cost and time of running all 7 agents for every function. The supervisor can be enhanced with a memory mechanism that stores past results, allowing it to improve its selections over time without any model training.

## Current Status

### Working
- **Function extraction** — clone any repo, parse with tree-sitter, extract all Python functions
- **Agent code** — LangGraph graph with 7 parallel nodes + prompt files all written
- **Output writer** — `write_function()` and `write_tests()` both implemented
- **Test runner** — `runner.py` executes generated tests with pytest, produces results.json
- **Mutation testing** — `mutator.py` integrates mutmut + custom AST mutants for measuring test effectiveness
- **CLI args** — `main.py` accepts --repo, --output, --concurrency, --limit, --min-lines
- **Docker** — Dockerfile builds and runs

### Not Yet Implemented
- **Supervisor agent** — LLM that analyzes each function and selects 2-4 agents (from 7) to run
- **Memory mechanism** — stores past supervisor decisions + mutation results to improve future selections

## Commands

```bash
# Install dependencies
uv sync

# Run test generation (all 7 agents)
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Run test generation (supervisor selects agents per function)
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs --supervised

# Run generated tests
uv run python -m src.runner --output ./outputs/repo_name

# Lint
uv run ruff check src/

# Docker build & run
docker build -t ghtest .
docker run -e DEEPSEEK_API_KEY=$DEEPSEEK_API_KEY -v $(pwd)/output:/output ghtest
```

Copy `.env.example` to `.env` and fill in your API key before running locally.

## Architecture

```
src/
├── main.py          # Entry point + CLI args + async runner
├── extractor.py     # clone repo + tree-sitter function extraction (Python only)
├── agents.py        # LLM factory + LangGraph state/nodes/graph
├── supervisor.py    # supervisor LLM that selects which agents to run per function
├── writer.py        # write output folders
├── runner.py        # execute generated tests with pytest, produce results.json
├── mutator.py       # mutmut integration + custom AST mutants + unique kill computation
└── prompts/         # per-agent system prompts (editable .md files)
    ├── supervisor.md # supervisor agent prompt
    ├── statement.md # whitebox: statement coverage
    ├── block.md     # whitebox: block coverage
    ├── condition.md # whitebox: condition coverage
    ├── path.md      # whitebox: path coverage
    ├── bva.md       # blackbox: boundary value analysis
    ├── ecp.md       # blackbox: equivalence class partitioning
    └── mutation.md  # blackbox: mutation testing
```

### Pipeline Flows

**Standard mode:** `clone → extract functions → run all 7 agents → write tests → mutation testing`

**Supervised mode:** `clone → extract functions → supervisor selects agents → run selected agents → write tests → mutation testing`

### Key Modules

- `extractor.py` — clones repo, walks `.py` files with `os.walk`, parses with tree-sitter, returns plain dicts with `name`, `source`, `language`, `file_path`, `imports`
- `agents.py` — `build_graph(selected_agents=None)` creates a LangGraph `StateGraph` with parallel fan-out. Accepts optional agent subset for supervised mode
- `supervisor.py` — `select_agents(fn, memory=None)` calls the LLM to analyze a function and pick 2-4 agents whose strengths match its structure. Falls back to all 7 if parsing fails
- `mutator.py` — `run_mutmut()` runs mutmut + custom AST mutants in isolated temp dir, returns killed/survived mutant sets. `compute_unique_kills()` finds per-agent unique contribution
- `writer.py` — `write_function()` writes the source file; `write_tests()` writes test files per function
- `runner.py` — `run_single_test()` executes one test file with pytest in subprocess; `run_tests()` aggregates results

## Prompt Files (`src/prompts/`)

Each agent has its own `.md` file. Edit these to tune agent behaviour — no Python changes needed.

## LLM Configuration

| Env var | Default | Description |
|---|---|---|
| `LLM_MODEL` | `deepseek-chat` | DeepSeek model name |
| `DEEPSEEK_API_KEY` | — | Required |

## TODO — Remaining Work

### Immediate
- [ ] Implement supervisor agent (`src/supervisor.py` + `src/prompts/supervisor.md`)
- [ ] Wire `--supervised` flag into `main.py`
- [ ] Add memory mechanism for supervisor to learn from past results
- [ ] Verify Docker image works with CLI args

### CI/CD
- [ ] Create `.github/workflows/run-tests.yml`
- [ ] Workflow: checkout → install deps → run pipeline → execute tests → report results

### Future
- [ ] Evaluation framework comparing supervised vs all-agents coverage
- [ ] Memory-driven supervisor improvements over time

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes
