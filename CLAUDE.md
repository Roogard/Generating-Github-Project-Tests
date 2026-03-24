# CLAUDE.md

## 1. System Overview

This system generates unit tests for Python functions extracted from any GitHub repository. The previous architecture was a linear pipeline — extract functions, pick agents, generate tests once, done. No feedback, no refinement.

The new architecture is a **stateful agent harness**. Instead of a single pass, the system runs an iterative loop:

1. The **supervisor** observes the current state (what tests exist, pass/fail results, mutation scores)
2. It picks an **action** (generate tests, run tests, run mutation testing, refine, or stop)
3. The **step function** executes that action and returns a new state
4. Repeat until the mutation score is high enough or the step budget runs out

Existing modules (`call_agent`, `run_all_agents`, `run_single_test`, `write_tests`) become **action handlers** inside the step function. Nothing gets rewritten — just wrapped.

Test agents are auto-discovered from `src/prompts/` (excluding `refine.md`, `fix.md`, `mutate.md`, `coverage.md`). Default set: **bva**, **ecp**, **path**, **condition**. Drop a new `.md` prompt file to add an agent — no code changes needed. Can also be overridden via `ghtest.toml` or the `test_types` config key.

## 2. State Definition

The state is a plain dict. One state per function under test.

```python
state = {
    # identity
    "function_info": {
        "name": str,
        "source": str,
        "language": str,
        "file_path": str,
        "imports": str,
        "start_line": int,          # 1-indexed first line of function in source file
        "end_line": int,            # 1-indexed last line of function in source file
    },
    "index": int,                   # function index in the batch
    "output_dir": str,              # base output directory
    "repo_clone_dir": str,          # path to cloned repo

    # generated tests — test_type -> test code string
    "generated_tests": {},

    # test results — test_type -> {"passed": [...], "failed": [...], "errors": [...], "stdout": str, "stderr": str}
    "test_results": {},

    # mutation results
    "mutation_score": 0.0,          # overall kill rate (0.0–1.0)
    "mutant_count": 0,              # total mutants generated
    "agent_kills": {},              # test_type -> set of killed mutant IDs
    "survived_mutants": [],         # list of survived mutant descriptions
    "killed_mutants": [],           # list of killed mutant descriptions
    "unique_kills": {},             # test_type -> int (mutants killed only by this agent)

    # quality signals
    "fix_attempts": 0,              # how many times fix_tests has run (max 2)
    "line_coverage": 0.0,           # 0.0–1.0, from pytest-cov (function-scoped)
    "branch_coverage": 0.0,         # 0.0–1.0, from pytest-cov (function-scoped)
    "assertion_density": 0.0,       # normalized assert count per test fn (0.0–1.0)
    "test_diversity": 0.0,          # fraction of mutation tag categories killed (0.0–1.0)
    "quality_score": 0.0,           # composite: 0.5*mutation + 0.25*branch + 0.15*assertion + 0.10*diversity
    "llm_mutation_score": 0.0,      # kill rate on LLM-generated semantic mutants only (0.0–1.0)
    "missing_lines": [],            # uncovered line numbers within the function (from pytest-cov)
    "missing_branches": [],         # uncovered branch pairs [[from, to], ...] within the function
    "score_history": [],            # quality_score after each coverage measurement (for diminishing-returns detection)

    # GRPO reward signal — multi-channel, populated by run_mutation_testing and run_coverage
    # NOT used by the supervisor; stored for RL/GRPO training on trajectory logs.
    # GRPO normalizes each channel independently via z-score within a group — do NOT collapse to scalar before passing to GRPO.
    "grpo_rewards": {
        "mutation": 0.0,          # kill rate (0.0–1.0)
        "branch_coverage": 0.0,   # function-scoped branch coverage (0.0–1.0)
        "assertion_density": 0.0, # normalized assert count per test fn (0.0–1.0)
        "test_diversity": 0.0,    # fraction of mutation tag categories killed (0.0–1.0)
        "unique_kills_ratio": 0.0,# mutants killed by only one agent / total mutants (0.0–1.0)
        "llm_mutation": 0.0,      # kill rate on LLM-generated semantic mutants (0.0–1.0)
        "quality_score": 0.0,     # composite scalar — same as state["quality_score"], for checkpointing
    },

    # history — list of past actions and their outcomes
    "history": [],                  # [{"step": int, "action": str, "outcome": str}]
    "step_count": 0,

    # termination
    "done": False,
}
```

`make_initial_state(fn, index, output_dir, repo_clone_dir)` returns this dict with empty/zero defaults.

## 3. Action Space

Eleven discrete actions. The supervisor picks exactly one per step.

### `generate_bva_tests`
- Calls `call_agent("bva", state["function_info"])`
- Stores returned test code in `state["generated_tests"]["bva"]`
- Outcome: number of chars generated, or "empty response"

### `generate_ecp_tests`
- Calls `call_agent("ecp", state["function_info"])`
- Stores in `state["generated_tests"]["ecp"]`

### `generate_path_tests`
- Calls `call_agent("path", state["function_info"])`
- Stores in `state["generated_tests"]["path"]`

### `generate_condition_tests`
- Calls `call_agent("condition", state["function_info"])`
- Stores in `state["generated_tests"]["condition"]`

### `run_tests`
- Writes test files to disk via `write_tests()`
- Runs each test file with `run_single_test(test_file, repo_clone_dir)`
- Populates `state["test_results"]` with pass/fail/error/stdout/stderr per test type
- Computes `state["assertion_density"]` (normalized assert count per test function)
- Outcome: summary like "3 passed, 1 failed, 0 errors"

### `run_mutation_testing`
- Builds `test_files_dict` from written test files on disk
- Calls `run_all_agents(func_file, test_files_dict, repo_clone_dir, source, original_file, fn=fn)`
- Generates both AST mutants (14 categories) and LLM-generated semantic mutants (5-10 plausible bugs via `generate_llm_mutants`)
- Computes `unique_kills` via `compute_unique_kills(agent_kills)` and stores in `state["unique_kills"]`
- Updates `state["mutation_score"]`, `state["mutant_count"]`, `state["agent_kills"]`, `state["survived_mutants"]`, `state["killed_mutants"]`
- Computes `state["test_diversity"]` (fraction of mutation tag categories killed) and `state["llm_mutation_score"]` (kill rate on LLM mutants only)
- Recomputes `state["quality_score"]`
- Outcome: summary like "42/50 killed (84.0%), llm=70.0%, quality=0.72"

### `fix_tests`
- For each test type with errors or failures, re-calls `call_agent_with_context("fix", ...)` with the current test code and error output (stdout/stderr)
- Overwrites `state["generated_tests"][test_type]` with the fixed code
- Increments `state["fix_attempts"]` (max 2 attempts before giving up)
- Outcome: "fixed N test types"

### `run_coverage`
- Collects all test file paths from disk
- Runs `pytest --cov --cov-branch --cov-report=json` via subprocess
- Parses JSON coverage report for line and branch coverage percentages
- Coverage is **function-scoped**: filters executed/missing lines and branches to the function's `start_line..end_line` range
- Updates `state["line_coverage"]` and `state["branch_coverage"]` (0.0–1.0)
- Stores `state["missing_lines"]` and `state["missing_branches"]` for coverage-guided generation
- Appends `state["quality_score"]` to `state["score_history"]`
- Recomputes `state["quality_score"]`
- Outcome: summary like "line: 85.0%, branch: 72.0%, quality=0.72"

### `generate_coverage_tests`
- Reads `state["missing_lines"]` and `state["missing_branches"]` from prior `run_coverage`
- Builds numbered source with uncovered lines/branches highlighted
- Calls `call_agent_with_context("coverage", fn, extra_context)` with uncovered info + existing tests
- Stores result in `state["generated_tests"]["coverage"]`
- Not auto-discovered (in `SPECIAL_PROMPTS`); triggered by supervisor when `branch_coverage < 0.90`
- Outcome: number of chars generated, or "empty response"

### `refine_tests`
- For each test type with surviving mutants, re-calls `call_agent` with extra context appended to the user message: the survived mutant descriptions
- Overwrites `state["generated_tests"][test_type]` with the refined code
- Outcome: "refined N agents"

### `stop`
- Sets `state["done"] = True`
- Outcome: "stopped"

## 4. Step Function

```python
def step(state, action):
    new = {**state}
    new["generated_tests"] = dict(state["generated_tests"])
    new["test_results"] = dict(state["test_results"])
    new["agent_kills"] = dict(state["agent_kills"])
    new["history"] = list(state["history"])
    new["step_count"] = state["step_count"] + 1

    outcome = _dispatch(new, action)

    new["history"].append({
        "step": new["step_count"],
        "action": action,
        "outcome": outcome,
    })
    return new
```

`_dispatch(state, action)` is an if/elif chain:

- **`generate_*_tests`**: extract test_type from the action name (strip `generate_` and `_tests`). Call `call_agent(test_type, state["function_info"])`. Store result. Return char count.
- **`run_tests`**: build a result dict compatible with `write_tests`, write to disk, then loop over test files calling `run_single_test`. Store results. Return summary.
- **`run_mutation_testing`**: collect test file paths, call `run_all_agents`, call `compute_unique_kills`. Update mutation fields. Return summary.
- **`fix_tests`**: for each test type with errors/failures, call `call_agent_with_context("fix", ...)` with error output. Overwrite test code. Return count.
- **`run_coverage`**: collect test file paths, run `pytest --cov --cov-branch`, parse JSON report. Update coverage fields. Return summary.
- **`refine_tests`**: for each test type in `generated_tests`, rebuild user message with survived mutant context appended. Call `call_agent` with augmented message. Overwrite test code. Return count.
- **`stop`**: set `done = True`. Return "stopped".

Each action handler calls existing module functions directly. No new abstractions.

## 5. LLM Supervisor

The supervisor is an LLM that picks one action per step using tool calling. It replaces the previous heuristic policy.

### Architecture (single-turn per step)

Each step is a fresh LLM call:
1. Build system prompt (role + strategy guide + quality formula + memory context)
2. Build user message (serialized current state — metrics, history, survived mutants, etc.)
3. Call LLM with `bind_tools(tools, tool_choice="any")` — forces exactly one tool call
4. Extract tool name → action string, extract `reasoning` arg → logged in trajectory
5. Pass action + reasoning to `step(state, action, reasoning)` — unchanged dispatch

The state already contains full `history` (all past actions, outcomes, and reasoning), so no multi-turn conversation is needed. Context stays bounded.

### Tool Definitions

Each action is a LangChain tool. Every tool takes a `reasoning: str` parameter — the LLM must explain why it chose this action. Test type tools (`generate_X_tests`) are built dynamically from auto-discovered prompts.

### Memory Integration

Before the loop, `run_harness()` fetches memory context:
- `retrieve_similar(collection, fn, k=5)` — similar functions + their agent performance
- `get_reflections(db, limit=10)` — lessons learned from past batches
- `format_memory_context(...)` — formats into markdown injected into the system prompt

Fetched once per function (static for the duration of the harness run).

### Supervisor Config

Separate `[supervisor]` config section — defaults to the main `[llm]` settings but can use a different model (e.g., stronger model for supervision, cheaper for generation). Set via `ghtest.toml`, env vars (`SUPERVISOR_PROVIDER`, `SUPERVISOR_MODEL`), or CLI (`--supervisor-provider`, `--supervisor-model`).

### Error Handling

If the LLM fails (network error, no tool call, invalid action name), `llm_supervisor()` returns `(None, None)`. The loop skips that iteration without burning a step. After 3 consecutive errors, the loop stops.

## 6. Iterative Loop

```python
def run_harness(fn, index, output_dir, repo_clone_dir, config, max_steps=None):
    state = make_initial_state(fn, index, output_dir, repo_clone_dir, config)

    # fetch memory context once before the loop
    memory_context = _fetch_memory_context(fn, state["planned_generates"])

    for i in range(max_steps):
        action, reasoning = llm_supervisor(state, memory_context)
        if action is None:
            continue  # skip on error, retry next iteration
        state = step(state, action, reasoning)
        if state["done"]:
            break

    _save_trajectory(state)
    return state
```

**Stopping conditions:**
- The LLM calls `stop` — it decides tests are good enough or further improvement is unlikely
- `max_steps` reached (default 20) — budget exhausted
- 3 consecutive supervisor errors — LLM is not responding

**Trajectory logging:** After each run, the full state (including reasoning per step) is serialized to `{output_dir}/trajectories/{fn_name}_{index}.json` for offline analysis and future RL/GRPO training.

## 7. Design Constraints

- Plain dicts, not dataclasses — the state is a `dict`
- No type annotations on functions
- No docstrings, no `@lru_cache`
- Functions over classes — `run_harness` is a function, not a `Harness` class
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Reuse `call_agent`, `run_all_agents`, `run_single_test`, `write_tests`, `compute_unique_kills` directly
- LLM supervisor via tool calling — no heuristic fallback
- Test agents auto-discovered from `src/prompts/`, overridable via config

## 8. Future Extensions

- **GRPO optimization** — trajectory logs contain `grpo_rewards` dicts with 7 channels. For GRPO training: use the multi-channel dict, NOT the collapsed `quality_score`. GRPO normalizes rewards within groups via z-score — passing a single compressed scalar (where all runs score 0.81–0.84) produces near-zero advantages and zero gradients. Instead, pass individual channels (mutation, branch_coverage, etc.) so GRPO can normalize each independently. See: *From Absolute to Relative* (2601.23058) and *Mind the Gap* (2309.02395).
- **DSPy prompt optimization** — optimize `refine.md` prompt after ~50 labeled examples.
- **Test oracle export** — consolidate strongest tests into a single oracle file usable by code repair tools (SWE-agent, OpenHands).
- **Trajectory analysis** — aggregate statistics across 50+ trajectory logs to data-drive prompt engineering and supervisor tuning.

## Commands

```bash
# Install dependencies
uv sync

# Run the harness
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Run the benchmark suite
uv run python scripts/benchmark.py --limit 5

# Lint
uv run ruff check src/
```

Copy `.env.example` to `.env` and fill in your API key before running locally.

## Architecture

```
src/
├── main.py          # entry point + CLI args
├── config.py        # config loader (ghtest.toml + env vars + CLI)
├── harness.py       # state, step function, LLM supervisor (tool calling), loop
├── skills.py        # action handlers (generate, run, fix, refine, coverage, mutate, stop) + dispatch
├── extractor.py     # clone repo + tree-sitter function extraction
├── agents.py        # LLM factory + call_agent + call_agent_with_context + get_supervisor_llm
├── memory.py        # ChromaDB memory: store results, retrieve similar, reflexions
├── writer.py        # write output folders
├── runner.py        # execute generated tests with pytest
├── mutator.py       # AST mutants + mutation testing
└── prompts/         # drop a .md file here to add a test agent
    ├── bva.md       # boundary value analysis prompt
    ├── ecp.md       # equivalence class partitioning prompt
    ├── path.md      # path coverage prompt
    ├── condition.md # condition/MC/DC coverage prompt
    ├── refine.md    # test refinement prompt (special, not a test agent)
    ├── fix.md       # test repair prompt (special, not a test agent)
    ├── mutate.md    # LLM-based realistic fault injection prompt (special)
    └── coverage.md  # coverage-guided test generation prompt (special, triggered by supervisor)
```

## Configuration

All settings can be configured via (in priority order): CLI flags → env vars → `ghtest.toml` → built-in defaults.

### `ghtest.toml` (optional, in project root or CWD)

```toml
[llm]
provider = "deepseek"       # "deepseek", "openai", "anthropic", "ollama"
model = "deepseek-chat"
base_url = ""               # auto-set per provider if empty
api_key_env = "DEEPSEEK_API_KEY"

[harness]
quality_threshold = 0.80
max_steps = 20
max_fix_attempts = 2
test_types = []             # empty = auto-discover from src/prompts/

[supervisor]
provider = ""               # empty = use llm.provider
model = ""                  # empty = use llm.model
temperature = 0.0

[timeouts]
test = 60
coverage = 120
mutmut = 600
custom_mutant = 10
```

### Environment Variables

| Env var | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `deepseek` | LLM provider name |
| `LLM_MODEL` | `deepseek-chat` | Model name |
| `LLM_BASE_URL` | (auto) | Custom API endpoint |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `QUALITY_THRESHOLD` | `0.80` | Quality score target |
| `MAX_STEPS` | `20` | Max harness steps |
| `SUPERVISOR_PROVIDER` | (same as LLM) | Supervisor LLM provider |
| `SUPERVISOR_MODEL` | (same as LLM) | Supervisor LLM model |

### CLI Flags

`--provider`, `--model`, `--quality-threshold`, `--max-steps`, `--supervisor-provider`, `--supervisor-model`

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes

## 9. Roadmap

### Phase 2: Better Generation
- **2A. Coverage-guided generation** — ✅ Done. `generate_coverage_tests` action feeds uncovered lines/branches into `prompts/coverage.md`. Supervisor triggers when `branch_coverage < 0.90`. Coverage is now function-scoped (uses `start_line`/`end_line` from tree-sitter).
- **2B. Multi-cycle refinement** — ✅ Done. Up to 3 refinement cycles; stops early if quality improvement < 0.02 between coverage measurements (tracked via `state["score_history"]`).

### Phase 3: LLM Supervisor + Memory
- **3A. LLM supervisor** — ✅ Done. Replaced heuristic `supervisor_policy()` with `llm_supervisor()` using LangChain tool calling. Each action is a tool with a `reasoning: str` parameter. The LLM sees serialized state (metrics, history, survived mutants) and picks one tool per step. Single-turn per step (no multi-turn conversation). Reasoning logged in trajectory history.
- **3B. Memory-informed supervisor** — ✅ Done. `run_harness()` fetches `retrieve_similar()` + `get_reflections()` before the loop. Memory context is injected into the supervisor system prompt so the LLM can leverage past agent performance on similar functions.
- **3C. Separate supervisor config** — ✅ Done. `[supervisor]` config section with its own provider/model/temperature. Defaults to main `[llm]` settings. Configurable via `ghtest.toml`, env vars, or CLI flags (`--supervisor-provider`, `--supervisor-model`).

### Phase 4: Bigger Picture
- **4A. Test oracle export** — `export_test_oracle(state, output_path)` in `writer.py`: consolidates strongest tests (by unique kills) into a single oracle file usable by repair tools (SWE-agent, OpenHands).
- **4B. Trajectory analysis** — `scripts/analyze_trajectories.py`: aggregate statistics across trajectory logs — which agents/prompts work by difficulty tier, refinement ROI, coverage vs mutation correlation.
- **4C. CI/CD integration** — `scripts/ci_check.py`: takes a git diff, extracts modified functions via tree-sitter, runs harness on each, exits non-zero if quality below threshold. Wire into a GitHub Action.
