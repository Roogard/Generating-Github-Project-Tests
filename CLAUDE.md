# CLAUDE.md

## 1. System Overview

This system generates unit tests for Python functions extracted from any GitHub repository. The previous architecture was a linear pipeline — extract functions, pick agents, generate tests once, done. No feedback, no refinement.

The new architecture is a **stateful agent harness**. Instead of a single pass, the system runs an iterative loop:

1. The **supervisor** observes the current state (what tests exist, pass/fail results, mutation scores)
2. It picks an **action** (generate tests, run tests, run mutation testing, refine, or stop)
3. The **step function** executes that action and returns a new state
4. Repeat until the mutation score is high enough or the step budget runs out

Existing modules (`call_agent`, `run_all_agents`, `run_single_test`, `write_tests`) become **action handlers** inside the step function. Nothing gets rewritten — just wrapped.

Four test agents: **bva**, **ecp**, **path**, **condition**.

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

    # test results — test_type -> {"passed": [...], "failed": [...], "errors": [...]}
    "test_results": {},

    # mutation results
    "mutation_score": 0.0,          # overall kill rate (0.0–1.0)
    "mutant_count": 0,              # total mutants generated
    "agent_kills": {},              # test_type -> set of killed mutant IDs
    "survived_mutants": [],         # list of survived mutant descriptions
    "killed_mutants": [],           # list of killed mutant descriptions

    # history — list of past actions and their outcomes
    "history": [],                  # [{"step": int, "action": str, "outcome": str}]
    "step_count": 0,

    # termination
    "done": False,
}
```

`make_initial_state(fn, index, output_dir, repo_clone_dir)` returns this dict with empty/zero defaults.

## 3. Action Space

Eight discrete actions. The supervisor picks exactly one per step.

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
- Populates `state["test_results"]` with pass/fail/error per test type
- Outcome: summary like "3 passed, 1 failed, 0 errors"

### `run_mutation_testing`
- Builds `test_files_dict` from written test files on disk
- Calls `run_all_agents(func_file, test_files_dict, repo_clone_dir, source, original_file)`
- Computes `unique_kills` via `compute_unique_kills(agent_kills)`
- Updates `state["mutation_score"]`, `state["mutant_count"]`, `state["agent_kills"]`, `state["survived_mutants"]`, `state["killed_mutants"]`
- Outcome: summary like "42/50 killed (84.0%)"

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

1. **No tests generated yet** → return `generate_{first}_tests` from `state["planned_generates"]`.
2. **Planned generates remaining** → return next `generate_X_tests` not yet in `generated_tests`.
3. **Tests generated but never run** → return `run_tests`.
4. **Tests run but no mutation testing** → return `run_mutation_testing`.
5. **Mutation score >= 0.85** → return `stop`.
6. **Score < 0.85 and haven't refined yet** → return `refine_tests`.
7. **Refined but not re-tested** → return `run_tests`.
8. **Re-tested but mutation not re-run** → return `run_mutation_testing`.
9. **Second mutation pass done** → return `stop` (one refinement cycle for v1).

The policy is pure heuristics — no LLM call. Fast and deterministic.

## 6. Iterative Loop

```python
def run_harness(fn, index, output_dir, repo_clone_dir, max_steps=15):
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
- `mutation_score >= 0.85` — tests are good enough
- `max_steps` reached (default 15) — budget exhausted
- One refinement cycle completed and score still low — stop to avoid infinite loops

**Typical run (6–10 steps):**
1. `generate_bva_tests`
2. `generate_ecp_tests`
3. `generate_path_tests`
4. `generate_condition_tests`
5. `run_tests`
6. `run_mutation_testing`
7. If score >= 0.85: `stop` (done in 7 steps)
8. If score < 0.85: `refine_tests` → `run_tests` → `run_mutation_testing` → `stop` (done in 10 steps)

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
- 4 test agents only: bva, ecp, path, condition

## 8. Future Extensions

- **LLM-based supervisor policy** — replace heuristic with LLM call that takes serialized state and returns action string. Step function and action space stay identical.
- **RL optimization** — the `(state, action, outcome)` triples in history are trajectory data for policy gradient or DPO. Reward signal = mutation_score at termination.
- **Multi-cycle refinement** — remove the one-cycle cap. Add diminishing-returns detection (if score improved < 2% on last cycle, stop).
- **Coverage-guided generation** — add `run_coverage` action using `pytest --cov`. Policy targets uncovered lines.
- **Trajectory logging** — dump full state history to JSON for offline analysis.
- **DSPy prompt optimization** — optimize `refine.md` prompt after ~50 labeled examples.

## Commands

```bash
# Install dependencies
uv sync

# Run the harness
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Lint
uv run ruff check src/
```

Copy `.env.example` to `.env` and fill in your API key before running locally.

## Architecture

```
src/
├── main.py          # entry point + CLI args
├── harness.py       # state, step function, supervisor policy, loop
├── extractor.py     # clone repo + tree-sitter function extraction
├── agents.py        # LLM factory + call_agent + call_agent_with_context
├── memory.py        # ChromaDB memory: store results, retrieve similar, reflexions
├── writer.py        # write output folders
├── runner.py        # execute generated tests with pytest
├── mutator.py       # AST mutants + mutation testing
└── prompts/
    ├── bva.md       # boundary value analysis prompt
    ├── ecp.md       # equivalence class partitioning prompt
    ├── path.md      # path coverage prompt
    ├── condition.md # condition/MC/DC coverage prompt
    └── refine.md    # test refinement prompt
```

## LLM Configuration

| Env var | Default | Description |
|---|---|---|
| `LLM_MODEL` | `deepseek-chat` | DeepSeek model name |
| `DEEPSEEK_API_KEY` | — | Required |

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes
