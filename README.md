# GitHub Project Test Generator

Automatically generates and runs unit tests for any Python GitHub repository, then reports test failures as potential bugs.

**Pipeline:**

```
Clone repo → Extract functions → Generate tests → Write to disk → Generate run_tests.sh → Execute tests → Parse failures → Bug report
```

---

## How It Works

The pipeline is linear — no iteration, no optimization loop. It is orchestrated by `src/main.py`.

### Step 1 — Clone & Extract (`src/extractor.py`)

- `clone_repo(url, target_dir)` — clones the target GitHub repo via git
- `extract_functions(repo_path)` — walks all `.py` files and uses tree-sitter to parse out function definitions
- `get_imports(source_bytes, language)` — extracts import statements for each file

Each extracted function is a plain dict: `name`, `source`, `language`, `file_path`, `imports`, `start_line`, `end_line`.

### Step 2 — Generate Tests (`src/agents.py`)

For each function, the pipeline calls `call_agent(prompt_name, fn, config)` once per test type (7 total). Each call:

- Loads a prompt from `src/prompts/{type}.md`
- Formats the function context via `build_user_message(fn)`
- Invokes the LLM via `get_llm(config)` (supports DeepSeek, OpenAI, Anthropic, Ollama)

To add a new test type, drop a `.md` prompt file into `src/prompts/` — no code changes needed.

### Step 3 — Write Tests (`src/writer.py`)

- `write_meta(repo_url, output_dir)` — saves `meta.json` with repo info
- `write_function(fn, output_dir, index)` — saves the raw function source
- `write_generated_tests(fn, generated_tests, output_dir, index)` — writes one `.py` file per test type:
  - `test_whitebox_{type}.py` for whitebox types
  - `test_blackbox_{type}.py` for blackbox types

### Step 4 — Generate Automation Script (`src/writer.py`)

- `generate_automation(output_dir, repo_clone_dir)` — creates `automation/run_tests.sh`, a shell script that sets `PYTHONPATH` and runs pytest over all generated test files

### Step 5 — Execute Tests (`src/runner.py`)

- `discover_tests(test_cases_dir)` — finds all `test_*.py` files under `generated_tests/`
- `run_single_test(test_file, repo_clone_dir, timeout=60)` — runs pytest with `--json-report` on each file and returns structured results
- Handles timeouts, import errors, and collection errors

### Step 6 — Parse Failures (`src/reporter.py`)

- `parse_failures(test_outcomes)` — converts raw pytest JSON results into structured failure dicts with `kind` (failure/error), test name, and location
- `_extract_assertion_info(longrepr)` — parses pytest's failure output to pull out the assertion expression, expected value, and actual value

### Step 7 — Bug Report (`src/reporter.py`)

- `format_bug_report(failures, repo_url)` — formats failures grouped by function with expected vs. actual values
- `print_bug_report(failures, repo_url)` — prints the report to stdout
- `write_bug_report(failures, repo_url, output_dir)` — writes `bug_report.txt`

---

## Test Types

### Whitebox (4) — require source code access

| Type | Prompt | Goal |
|---|---|---|
| `statement` | `src/prompts/statement.md` | Execute every statement at least once |
| `block` | `src/prompts/block.md` | Execute every basic block between branches |
| `condition` | `src/prompts/condition.md` | Each boolean sub-expression evaluates to both True and False |
| `path` | `src/prompts/path.md` | Exercise all entry-to-exit execution paths |

### Blackbox (3) — treat function as a black box

| Type | Prompt | Goal |
|---|---|---|
| `bva` | `src/prompts/bva.md` | Probe boundary values of input domains |
| `ecp` | `src/prompts/ecp.md` | Partition input space into equivalence classes |
| `mutation` | `src/prompts/mutation.md` | Catch common coding mistakes (off-by-one, wrong operator, etc.) |

---

## Output Structure

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
    automation/
        run_tests.sh
    bug_report.txt
```

---

## Quick Start

```bash
# Install dependencies
uv sync

# Copy and fill in your API key
cp .env.example .env

# Run the pipeline on any public GitHub repo
uv run python -m src.main --repo https://github.com/user/repo --output ./outputs

# Limit to 5 functions with at least 2 branches
uv run python -m src.main --repo https://github.com/user/repo --limit 5 --min-branches 2
```

---

## Configuration

Settings are loaded in priority order: CLI flags → environment variables → `ghtest.toml` → built-in defaults.

### Environment Variables

| Variable | Default | Description |
|---|---|---|
| `LLM_PROVIDER` | `deepseek` | LLM provider (`deepseek`, `openai`, `anthropic`, `ollama`) |
| `LLM_MODEL` | `deepseek-chat` | Model name |
| `LLM_BASE_URL` | (auto) | Custom API endpoint |
| `DEEPSEEK_API_KEY` | — | DeepSeek API key |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `TIMEOUT_TEST` | `60` | Test execution timeout (seconds) |

### `ghtest.toml` (optional)

```toml
[llm]
provider = "deepseek"
model = "deepseek-chat"
api_key_env = "DEEPSEEK_API_KEY"

[timeouts]
test = 60
```

### CLI Flags

`--provider`, `--model`, `--repo`, `--output`, `--limit`, `--min-lines`, `--max-lines`, `--min-branches`, `--max-branches`, `--stratify`
