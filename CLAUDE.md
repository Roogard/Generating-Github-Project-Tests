# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Goal

Automatically generate unit tests for every function in any GitHub repository. Given a GitHub repo URL, the system extracts all Python functions via tree-sitter, generates unit tests per function using a multi-agent LangGraph approach, and writes organized output folders.

Uses a supervisor LLM to intelligently select which test generation agents to run for each function. The supervisor analyzes the function's structure and picks 2-4 agents (from 7 available) whose strengths match — avoiding the cost and time of running all 7 agents for every function.

The supervisor improves over time via a memory system (no model training needed): it stores past decisions + mutation results in a structured memory, retrieves similar past functions as few-shot examples, and generates reflexion summaries that capture high-level patterns. This is an inference-time learning approach that works with API models.

## Current Status

### Working
- **Function extraction** — clone any repo, parse with tree-sitter, extract all Python functions
- **Supervisor agent** — LLM analyzes each function and selects 2-4 agents (from 7) to run
- **Memory system** — ChromaDB stores past (function source, agents, mutation scores), retrieves similar functions as few-shot examples, generates reflexion summaries
- **Agent code** — LangGraph graph with parallel nodes + prompt files all written
- **Output writer** — `write_function()` and `write_tests()` both implemented
- **Test runner** — `runner.py` executes generated tests with pytest, produces results.json
- **Mutation testing** — `mutator.py` integrates mutmut + custom AST mutants for measuring test effectiveness
- **CLI args** — `main.py` accepts --repo, --output, --concurrency, --limit, --min-lines, --mode
- **Docker** — Dockerfile builds and runs

## Commands

```bash
# Install dependencies
uv sync

# Training mode — runs all 7 agents, stores ground truth to memory
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs --mode train

# Testing mode (default) — supervisor uses memory to select agents
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs --mode test

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
├── memory.py        # ChromaDB memory: store results, retrieve similar, reflexions
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

**Training:** `clone → extract → supervisor picks (logged) → run ALL 7 agents → write tests → mutation testing → store results in ChromaDB → generate reflections`

**Testing:** `clone → extract → retrieve similar from ChromaDB → supervisor picks (with memory) → run SELECTED agents → write tests → mutation testing → store results → generate reflections`

### Key Modules

- `extractor.py` — clones repo, walks `.py` files with `os.walk`, parses with tree-sitter, returns plain dicts with `name`, `source`, `language`, `file_path`, `imports`
- `agents.py` — `build_graph(selected_agents)` creates a LangGraph `StateGraph` with parallel fan-out for the selected agents
- `supervisor.py` — `select_agents(fn, memory_context=None)` calls the LLM to analyze a function and pick 2-4 agents. Accepts optional memory context with past examples + reflections
- `memory.py` — ChromaDB-backed memory. `store_result()` saves function source + mutation scores. `retrieve_similar()` finds K nearest past functions by source code embedding. `generate_reflections()` asks the LLM to summarize lessons from a batch. `format_memory_context()` builds prompt context from retrieved examples + reflections
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

### Later
- [ ] Verify Docker image works with CLI args
- [ ] Create `.github/workflows/run-tests.yml`
- [ ] DSPy prompt optimization (after ~50 labeled examples)
- [ ] Lightweight router/classifier as fast path (after ~200 labeled examples)

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes
