# CLAUDE.md

## 1. System Overview

This system generates unit tests for Python functions extracted from any GitHub repository, executes them against the real codebase, and reports test failures as potential bugs.

The pipeline generates tests, runs them, applies a single one-shot fix attempt per failing function, then reports:

1. Clone the target repository and extract functions via tree-sitter
2. For each function, generate 7 test types (4 whitebox + 3 blackbox) using LLM agents
3. Write generated tests to disk
4. Generate a `run_tests.sh` automation script
5. Execute all tests against the real repo via pytest
6. For each function with failures: attempt a one-shot fix (diagnose + patch + re-run once)
7. Parse failures and errors from final test results
8. Print a bug report with expected vs actual values

Test agents are loaded from `src/prompts/`. Drop a new `.md` prompt file to add a test type — no code changes needed.

## 2. Test Types

### Whitebox (4)

| Type | Prompt | Goal |
|---|---|---|
| **statement** | `statement.md` | Execute every statement at least once |
| **block** | `block.md` | Execute every basic block (contiguous statements between branches) |
| **condition** | `condition.md` | Each boolean sub-expression evaluates to both True and False |
| **path** | `path.md` | Exercise all entry-to-exit execution paths |

### Blackbox (3)

| Type | Prompt | Goal |
|---|---|---|
| **bva** | `bva.md` | Probe boundary values of input domains |
| **ecp** | `ecp.md` | Partition input space into equivalence classes |
| **mutation** | `mutation.md` | Catch common coding mistakes (off-by-one, wrong operator, etc.) |

## 3. Pipeline

```
main():
    clone repo
    extract functions (tree-sitter)
    for each function:
        generate 7 test types (call_agent per type)
        write tests to generated_tests/
    generate automation/run_tests.sh
    for each test file:
        run_single_test (pytest)
    parse failures
    for each function with failures:
        run_one_shot_fix (diagnose + patch + re-run once)
    re-parse failures from final outcomes
    print bug report
    write bug_report.txt
```

### Step 1 — Clone + Extract
Reuses `extractor.py`: `clone_repo(url, tmp)` + `extract_functions(tmp)`. Returns list of function dicts with name, source, language, file_path, imports, start_line, end_line.

### Step 2 — Generate Tests
For each function, calls `call_agent(test_type, fn, config)` for all 7 types. Each agent loads its prompt from `src/prompts/{type}.md`, builds a user message with function context, and invokes the LLM.

### Step 3 — Write Tests
`write_generated_tests(fn, generated, output_dir, index)` writes files as:
- `test_whitebox_{type}.py` for whitebox types
- `test_blackbox_{type}.py` for blackbox types

### Step 4 — Generate Automation
`generate_automation(output_dir, repo_clone_dir)` creates `automation/run_tests.sh` — a shell script that sets PYTHONPATH and runs pytest on all generated test files.

### Step 5 — Execute Tests
Loops over all `test_*.py` files under `generated_tests/`, runs each via `run_single_test(test_file, repo_clone_dir)`. Uses pytest with `--json-report` for structured results.

### Step 6 — One-Shot Fix Pass
`run_one_shot_fix(fn, fn_key, ...)` is called once per function that has failures. It diagnoses the root cause (Stage 1 LLM call via `fix_diagnose.md`), generates a patch (Stage 2 LLM call via `fix_function.md`), validates the output is a real function (not a test file), writes the fix to disk, and re-runs all tests for that function once. No iteration, no rollback.

### Step 7 — Parse Failures
`parse_failures(test_outcomes)` extracts structured failure info from the final pytest JSON reports: test name, assertion expression, expected/actual values, file:line location.

### Step 8 — Bug Report
Prints and writes a formatted bug report grouped by function, showing each failure with type, location, expected vs actual values.

## 4. Output Structure

```
{output_dir}/{repo_name}/
    meta.json
    functions/
        {fn_name}_0/
            function.py
    generated_tests/
        {fn_name}_0/
            test_whitebox_statement.py
            test_whitebox_block.py
            test_whitebox_condition.py
            test_whitebox_path.py
            test_blackbox_bva.py
            test_blackbox_ecp.py
            test_blackbox_mutation.py
    fixed_functions/              # only present when a fix was attempted
        {fn_name}_0/
            iteration_0/
                fixed_function.py
                diagnosis.md
                diagnosis_context.md
                fix_context.md
    automation/
        run_tests.sh
    bug_report.txt
```

## 5. Architecture

```
src/
├── main.py          # entry point + CLI args + pipeline + run_one_shot_fix
├── config.py        # config loader (ghtest.toml + env vars + CLI)
├── extractor.py     # clone repo + tree-sitter function extraction
├── agents.py        # LLM factory + call_agent + call_fix_agent
├── writer.py        # write output folders + generate automation script
├── runner.py        # execute generated tests with pytest
├── reporter.py      # parse test failures + format bug report
└── prompts/         # drop a .md file here to add a test agent
    ├── statement.md    # statement coverage (whitebox)
    ├── block.md        # block coverage (whitebox)
    ├── condition.md    # condition/MC/DC coverage (whitebox)
    ├── path.md         # path coverage (whitebox)
    ├── bva.md          # boundary value analysis (blackbox)
    ├── ecp.md          # equivalence class partitioning (blackbox)
    ├── mutation.md     # mutation-style fault detection (blackbox)
    ├── fix_diagnose.md # Stage 1: root cause diagnosis for one-shot fix
    └── fix_function.md # Stage 2: patch generation for one-shot fix
```

## 6. Configuration

All settings can be configured via (in priority order): CLI flags → env vars → `ghtest.toml` → built-in defaults.

### `ghtest.toml` (optional, in project root or CWD)

```toml
[llm]
provider = "deepseek"       # "deepseek", "openai", "anthropic", "ollama"
model = "deepseek-chat"
base_url = ""               # auto-set per provider if empty
api_key_env = "DEEPSEEK_API_KEY"

[timeouts]
test = 60
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
| `TIMEOUT_TEST` | `60` | Test execution timeout (seconds) |

### CLI Flags

`--provider`, `--model`, `--repo`, `--output`, `--limit`, `--min-lines`, `--max-lines`, `--min-branches`, `--max-branches`, `--stratify`

## Commands

```bash
# Install dependencies
uv sync

# Run the pipeline
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Run with filters
uv run python -m src.main --repo https://github.com/user/repo --limit 5 --min-branches 2

# Lint
uv run ruff check src/
```

Copy `.env.example` to `.env` and fill in your API key before running locally.

## Code Style
- Plain dicts, not dataclasses
- No type annotations on functions
- No docstrings, no `@lru_cache`
- `os.walk` / `os.path`, not pathlib (except where libraries require Path)
- Minimal helper functions — inline the logic
- Functions over classes

## 7. Roadmap

### Phase 1: Linear Pipeline
- **1A. Core pipeline** — Done. Clone, extract, generate 7 test types, write, run, report.
- **1B. New test agents** — Done. Statement, block, and mutation-style fault detection prompts.
- **1C. Bug reporting** — Done. Structured failure parsing with expected/actual values, grouped by function.
- **1D. Automation script** — Done. `run_tests.sh` for standalone test execution.

### Phase 2: Improvements
- **2A. Fix pass** — Done. One-shot fix: diagnose root cause + generate patch + re-run once per failing function.
- **2B. Multi-language support** — Extend tree-sitter extraction and test runners beyond Python (JavaScript, TypeScript, Go).
- **2C. Coverage measurement** — Optional coverage report alongside bug report.

### Phase 3: Integration
- **3A. CI/CD integration** — `scripts/ci_check.py`: takes a git diff, extracts modified functions, runs pipeline, exits non-zero if bugs found.
- **3B. GitHub Action** — Publishable action that runs the pipeline on PRs.
- **3C. Test oracle export** — Consolidate strongest tests into a single file usable by repair tools.

## Next Step

### Fix the test oracle problem

**The problem:** Test generation agents copy the buggy function's output and use it as the expected value. After the one-shot fix corrects the bug, those tests now fail against the *correct* code — killing convergence even when the fix is right. This was the primary failure mode in every non-converging run.

**Root cause (from research):** This is a known issue in LLM test oracle generation. LLMs are systematically biased toward following the actual implementation rather than reasoning about intended behavior. The ECP and Path agents are the worst offenders.

**Two concrete changes to make:**

1. **Split oracle reasoning from input generation in prompts.** Rewrite the test generation prompts (especially `ecp.md`, `path.md`, `mutation.md`) to explicitly separate the two steps:
   - Step 1: generate test inputs based on the function's name and standard algorithm behavior
   - Step 2: fill in expected values by reasoning about what the function *should* return — explicitly without looking at the implementation

   Add a hard constraint to every prompt: "Do NOT derive expected values by tracing through the implementation. Reason from the function's name, its algorithm type, and standard correctness properties."

2. **Add property/invariant assertions alongside exact-value assertions.** Instead of only `assert quicksort([3,3,3]) == [3]`, also generate:
   ```python
   result = quicksort([3, 3, 3])
   assert len(result) == 3                                   # length preserved
   assert all(result[i] <= result[i+1] for i in range(len(result)-1))  # sorted
   assert sorted(result) == sorted([3, 3, 3])               # same elements
   ```
   Property checks are immune to the oracle-copying problem — they don't require knowing the "right" answer, only that invariants hold.

**Files to change:** `src/prompts/ecp.md`, `src/prompts/path.md`, `src/prompts/mutation.md`, `src/prompts/bva.md`, `src/prompts/statement.md`, `src/prompts/block.md`, `src/prompts/condition.md`

**Expected outcome:** Test suites that correctly fail against buggy code AND pass against the fixed code, enabling the one-shot fix to converge.
