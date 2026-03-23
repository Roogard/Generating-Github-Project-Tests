# CLAUDE.md

## 1. System Overview

This system generates unit tests for Python functions extracted from any GitHub repository. The previous architecture was a linear pipeline — extract functions, pick agents, generate tests once, done. No feedback, no refinement.

The new architecture is a **stateful agent harness**. Instead of a single pass, the system runs an iterative loop:

1. The **supervisor** observes the current state (what tests exist, pass/fail results, mutation scores)
2. It picks an **action** (generate tests, run tests, run mutation testing, refine, or stop)
3. The **step function** executes that action and returns a new state
4. Repeat until the mutation score is high enough or the step budget runs out

Existing modules (`call_agent`, `run_all_agents`, `run_single_test`, `write_tests`) become **action handlers** inside the step function. Nothing gets rewritten — just wrapped.

Test agents are auto-discovered from `src/prompts/` (excluding `refine.md`, `fix.md`, `mutate.md`). Default set: **bva**, **ecp**, **path**, **condition**. Drop a new `.md` prompt file to add an agent — no code changes needed. Can also be overridden via `ghtest.toml` or the `test_types` config key.

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
    "line_coverage": 0.0,           # 0.0–1.0, from pytest-cov
    "branch_coverage": 0.0,         # 0.0–1.0, from pytest-cov
    "assertion_density": 0.0,       # normalized assert count per test fn (0.0–1.0)
    "test_diversity": 0.0,          # fraction of mutation tag categories killed (0.0–1.0)
    "quality_score": 0.0,           # composite: 0.5*mutation + 0.25*branch + 0.15*assertion + 0.10*diversity
    "llm_mutation_score": 0.0,      # kill rate on LLM-generated semantic mutants only (0.0–1.0)

    # history — list of past actions and their outcomes
    "history": [],                  # [{"step": int, "action": str, "outcome": str}]
    "step_count": 0,

    # termination
    "done": False,
}
```

`make_initial_state(fn, index, output_dir, repo_clone_dir)` returns this dict with empty/zero defaults.

## 3. Action Space

Ten discrete actions. The supervisor picks exactly one per step.

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
- Updates `state["line_coverage"]` and `state["branch_coverage"]` (0.0–1.0)
- Recomputes `state["quality_score"]`
- Outcome: summary like "line: 85.0%, branch: 72.0%, quality=0.72"

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

## 5. Supervisor Policy

```python
def supervisor_policy(state):
    history_actions = [h["action"] for h in state["history"]]
    has_tests = bool(state["generated_tests"])
    has_test_results = bool(state["test_results"])
    has_mutation = state["mutant_count"] > 0
    mutation_score = state["mutation_score"]
    refine_count = history_actions.count("refine_tests")
```

Decision logic, evaluated in order:

1. **Planned generates remaining** → return next `generate_X_tests` not yet in `generated_tests`.
2. **Tests need running** (never run, or fixed/refined/regenerated since last run) → return `run_tests`.
3. **Tests have errors or failures AND `fix_attempts < 2`** → return `fix_tests`. Loops back to step 2.
4. **Mutation testing needed** (never run, or re-run needed after changes) → return `run_mutation_testing`.
5. **Coverage not yet measured** (or re-run needed) → return `run_coverage`.
6. **Composite quality score >= 0.80** → return `stop`. Quality score = 0.5*mutation + 0.25*branch + 0.15*assertion_density + 0.10*test_diversity.
7. **Agent has 0 unique kills AND quality < 0.80** → return `generate_{weak_agent}_tests`. Loops back to step 2.
8. **Haven't refined yet** → return `refine_tests`. Loops back to step 2.
9. **Otherwise** → return `stop`.

The policy is pure heuristics — no LLM call. Fast and deterministic.

## 6. Iterative Loop

```python
def run_harness(fn, index, output_dir, repo_clone_dir, max_steps=20):
    state = make_initial_state(fn, index, output_dir, repo_clone_dir)

    for i in range(max_steps):
        action = supervisor_policy(state)
        print(f"  [{fn['name']}] step {i+1}: {action}")
        state = step(state, action)
        if state["done"]:
            break

    return state
```

**Stopping conditions:**
- `quality_score >= 0.80` — tests are good enough (composite of mutation, coverage, assertion density, diversity)
- `max_steps` reached (default 20) — budget exhausted
- One refinement cycle completed and score still low — stop to avoid infinite loops

**Trajectory logging:** After each run, the full state is serialized to `{output_dir}/trajectories/{fn_name}_{index}.json` for offline analysis and future RL/DPO training.

**Typical run (10–16 steps):**
1. `generate_bva_tests`
2. `generate_ecp_tests`
3. `generate_path_tests`
4. `generate_condition_tests`
5. `run_tests`
6. `fix_tests` (if errors/failures exist)
7. `run_tests` (re-run after fix)
8. `run_mutation_testing`
9. `run_coverage`
10. If score >= 0.85: `stop` (done in 10 steps)
11. If score < 0.85 and weak agent: `generate_X_tests` → `run_tests` → `run_mutation_testing` → `run_coverage`
12. If still < 0.85: `refine_tests` → `run_tests` → `run_mutation_testing` → `run_coverage` → `stop`

## 7. Design Constraints

- Plain dicts, not dataclasses — the state is a `dict`
- No type annotations on functions
- No docstrings, no `@lru_cache`
- Functions over classes — `run_harness` is a function, not a `Harness` class
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Reuse `call_agent`, `run_all_agents`, `run_single_test`, `write_tests`, `compute_unique_kills` directly
- No RL yet — heuristic supervisor policy only
- One refinement cycle max for v1
- Test agents auto-discovered from `src/prompts/`, overridable via config

## 8. Future Extensions

- **LLM-based supervisor policy** — replace heuristic with LLM call that takes serialized state and returns action string. Step function and action space stay identical.
- **RL optimization** — trajectory logs (`{output_dir}/trajectories/`) contain `(state, action, outcome)` data for policy gradient or DPO. Reward signal = `quality_score` at termination.
- **Multi-cycle refinement** — remove the one-cycle cap. Add diminishing-returns detection (if score improved < 2% on last cycle, stop).
- **Coverage-guided generation** — `run_coverage` already collects data; add `generate_coverage_tests` action that feeds uncovered lines into a coverage-targeted prompt.
- **Memory-informed supervisor** — connect ChromaDB `retrieve_similar()` to supervisor policy to deprioritize agents with historically 0 unique kills on similar functions.
- **Test oracle export** — consolidate strongest tests into a single oracle file usable by code repair tools (SWE-agent, OpenHands).
- **DSPy prompt optimization** — optimize `refine.md` prompt after ~50 labeled examples.
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
├── harness.py       # state, step function, supervisor policy, loop
├── extractor.py     # clone repo + tree-sitter function extraction
├── agents.py        # LLM factory + call_agent + call_agent_with_context
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
    └── mutate.md    # LLM-based realistic fault injection prompt (special)
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

### CLI Flags

`--provider`, `--model`, `--quality-threshold`, `--max-steps`

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes

## 9. Roadmap

### Phase 2: Better Generation
- **2A. Coverage-guided generation** — After `run_coverage`, extract `missing_lines` per function. New action `generate_coverage_tests` feeds uncovered lines + source context into a targeted prompt (`prompts/coverage.md`). Supervisor triggers it when `branch_coverage < 0.90`.
- **2B. Multi-cycle refinement** — Remove the one-refinement cap in `supervisor_policy`. Allow up to 3 cycles; stop early if quality improvement < 0.02 (track `state["score_history"]`).
- **2C. Connect memory to supervisor** — Call `retrieve_similar()` in `run_harness` before the loop; store in `state["memory_context"]`. Supervisor uses past agent performance to deprioritize weak agents for similar functions.

### Phase 3: Bigger Picture
- **3A. Test oracle export** — `export_test_oracle(state, output_path)` in `writer.py`: consolidates strongest tests (by unique kills) into a single oracle file usable by repair tools (SWE-agent, OpenHands).
- **3B. Trajectory analysis** — `scripts/analyze_trajectories.py`: aggregate statistics across trajectory logs — which agents/prompts work by difficulty tier, refinement ROI, coverage vs mutation correlation.
- **3C. CI/CD integration** — `scripts/ci_check.py`: takes a git diff, extracts modified functions via tree-sitter, runs harness on each, exits non-zero if quality below threshold. Wire into a GitHub Action.
