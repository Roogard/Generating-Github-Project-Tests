"""
Core pipeline — the single callable both the CLI and API use.

    from src.pipeline import run_pipeline

    result = run_pipeline(
        repo_url="https://github.com/keon/algorithms",
        fn_name="binary_search",
    )
"""

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from concurrent.futures import ThreadPoolExecutor

from dotenv import load_dotenv

load_dotenv()


# ── Shared helpers ────────────────────────────────────────────────────────────

def repo_name_from_url(url: str) -> str:
    return url.rstrip("/").split("/")[-1].replace(".git", "")


def _iter_test_files(test_dir: str):
    if not os.path.isdir(test_dir):
        return
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            yield fname

# ── Provider defaults ─────────────────────────────────────────────────────────

_PROVIDERS = {
    "deepseek":  {"base_url": "https://api.deepseek.com",        "api_key_env": "DEEPSEEK_API_KEY"},
    "openai":    {"base_url": "https://api.openai.com/v1",        "api_key_env": "OPENAI_API_KEY"},
    "anthropic": {"base_url": "",                                  "api_key_env": "ANTHROPIC_API_KEY"},
    "ollama":    {"base_url": "http://localhost:11434/v1",         "api_key_env": ""},
}

_DEFAULT_MODELS = {
    "deepseek":  "deepseek-chat",
    "openai":    "gpt-4o",
    "anthropic": "claude-sonnet-4-6",
    "ollama":    "llama3.2",
}

PRESETS = {
    "fast":     {"max_iterations": 1, "coverage_threshold": 70.0, "test_timeout": 30},
    "default":  {"max_iterations": 3, "coverage_threshold": 80.0, "test_timeout": 60},
    "thorough": {"max_iterations": 5, "coverage_threshold": 90.0, "test_timeout": 120},
}


def _build_config(provider: str, model: str | None, api_key: str | None = None) -> dict:
    p = _PROVIDERS.get(provider, _PROVIDERS["deepseek"])
    return {
        "llm": {
            "provider":    provider,
            "model":       model or _DEFAULT_MODELS.get(provider, "deepseek-chat"),
            "base_url":    os.environ.get("LLM_BASE_URL", p["base_url"]),
            "api_key_env": p["api_key_env"],
            "api_key":     api_key,  # explicit key takes priority over env var in get_llm()
        },
        "timeouts": {
            "test": int(os.environ.get("TIMEOUT_TEST", "60")),
        },
    }


# ── Pip helpers ───────────────────────────────────────────────────────────────

def _pip(*args):
    uv = shutil.which("uv")
    if uv:
        r = subprocess.run([uv, "pip", "install", *args, "--quiet"], check=False, capture_output=True)
        if r.returncode == 0:
            return r
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install", *args, "-q", "--no-warn-script-location"],
        check=False, capture_output=True,
    )
    if r.returncode == 0:
        return r
    subprocess.run([sys.executable, "-m", "ensurepip", "--upgrade"], check=False, capture_output=True)
    return subprocess.run(
        [sys.executable, "-m", "pip", "install", *args, "-q", "--no-warn-script-location"],
        check=False, capture_output=True,
    )


def _install_deps(repo_dir: str):
    if os.path.isfile(os.path.join(repo_dir, "setup.py")) or \
       os.path.isfile(os.path.join(repo_dir, "pyproject.toml")):
        r = _pip("-e", repo_dir)
        if r.returncode != 0:
            print(f"  [warn] repo install failed: {r.stderr.decode(errors='replace').strip()[:200]}")


# ── Internal pipeline helpers ─────────────────────────────────────────────────

def _run_coverage_for_fn(fn, output_dir, repo_dir, index, config):
    from src.coverage import measure_coverage
    fn_key = f"{fn['name']}_{index}"
    test_dir = os.path.join(output_dir, "generated_tests", fn_key)
    best = None
    for fname in _iter_test_files(test_dir):
        cov = measure_coverage(
            os.path.join(test_dir, fname), fn, repo_dir,
            timeout=config["timeouts"]["test"],
        )
        if cov["error"]:
            continue
        if best is None or cov["coverage_pct"] > best["coverage_pct"]:
            best = cov
    return best


def _run_fn_tests(fn_key, output_dir, repo_dir, config):
    from src.runner import run_single_test
    outcomes = {}
    test_dir = os.path.join(output_dir, "generated_tests", fn_key)
    for fname in _iter_test_files(test_dir):
        outcomes[(fn_key, fname)] = run_single_test(
            os.path.join(test_dir, fname), repo_dir,
            timeout=config["timeouts"]["test"],
        )
    return outcomes


def _is_valid_fix(code, fn_name):
    if not code or not code.strip():
        return False
    if "import pytest" in code or "def test_" in code:
        return False
    if f"def {fn_name}" not in code:
        return False
    try:
        ast.parse(code)
        return True
    except SyntaxError:
        return False


def _one_shot_fix(fn, fn_key, test_outcomes, repo_dir, output_dir, idx, config):
    from src.agents import call_fix_agent, call_oracle_revision_agent, strip_code_fences, _extract_code
    from src.reporter import parse_failures
    from src.writer import write_fix_artifacts, write_fixed_function, replace_function_in_repo

    fn_failures = [f for f in parse_failures(test_outcomes) if f["function"] == fn_key]
    if not fn_failures or all(f["kind"] == "error" for f in fn_failures):
        return test_outcomes, False

    print(f"  fixing ({len(fn_failures)} failure(s))...", end=" ", flush=True)
    fix = call_fix_agent(fn, fn_failures, config)
    if not fix["code"] or not fix["code"].strip():
        print("no output")
        return test_outcomes, False

    fixed_code = strip_code_fences(fix["code"])
    if not _is_valid_fix(fixed_code, fn["name"]):
        print("invalid fix, skipping")
        return test_outcomes, False

    write_fix_artifacts(fn, output_dir, idx, 0,
                        diagnosis=fix["diagnosis"],
                        diagnosis_context=fix["diagnosis_context"],
                        fix_context=fix["fix_context"])
    fn["end_line"] = replace_function_in_repo(fn, fixed_code, repo_dir)
    fn["source"] = fixed_code
    write_fixed_function(fn, fixed_code, output_dir, idx, iteration=0)

    outcomes = _run_fn_tests(fn_key, output_dir, repo_dir, config)
    remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

    if remaining:
        print(f"{len(remaining)} failure(s), revising oracles...", end=" ", flush=True)
        by_file = {}
        for f in remaining:
            by_file.setdefault(f.get("test_file_path", ""), []).append(f)
        for test_path, file_failures in by_file.items():
            if not test_path or not os.path.isfile(test_path):
                continue
            with open(test_path, encoding="utf-8") as fh:
                original_test_code = fh.read()
            revised_raw = call_oracle_revision_agent(fn, original_test_code, file_failures, config)
            if not revised_raw or not revised_raw.strip():
                continue
            revised_code = _extract_code(revised_raw)
            try:
                ast.parse(revised_code)
                with open(test_path, "w", encoding="utf-8") as fh:
                    fh.write(revised_code)
            except SyntaxError as e:
                print(f"oracle revision invalid ({e}), skipping")
        outcomes = _run_fn_tests(fn_key, output_dir, repo_dir, config)
        remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

    print("converged" if not remaining else f"{len(remaining)} failure(s) remain")
    return outcomes, True


def _generate_initial_tests(fn, cfg):
    # whitebox and blackbox are independent LLM calls — run them concurrently
    from src.agents import call_agent
    with ThreadPoolExecutor(max_workers=2) as ex:
        futures = {t: ex.submit(call_agent, t, fn, cfg) for t in ("whitebox", "blackbox")}
        out = {}
        for t, fut in futures.items():
            code = fut.result()
            if code and code.strip():
                out[t] = code
                print(f"  {t}: ok ({len(code)} chars)")
            else:
                print(f"  {t}: empty")
    return out


def _coverage_loop(fn, run_output, repo_dir, index, cfg, max_iter, threshold, delta_min=2.0):
    from src.agents import generate_with_critique
    from src.writer import write_generated_tests
    prev_pct = 0.0
    for iteration in range(1, max_iter + 1):
        cov = _run_coverage_for_fn(fn, run_output, repo_dir, index, cfg)
        if cov is None:
            print(f"  [cov {iteration}] collection error, stopping")
            break
        pct = cov["coverage_pct"]
        delta = pct - prev_pct
        print(f"  [cov {iteration}] {pct:.1f}%", end="")
        if pct >= threshold:
            print(" ✓ threshold met")
            break
        if iteration > 1 and delta < delta_min:
            print(f" stalled (Δ={delta:.1f}%), stopping")
            break
        print(" → regenerating", flush=True)
        prev_pct = pct
        result = generate_with_critique(fn, cfg, coverage_info=cov)
        refreshed = {t: result[t] for t in ("whitebox", "blackbox") if result.get(t, "").strip()}
        if not refreshed:
            print(f"  [cov {iteration}] critic returned empty, stopping")
            break
        write_generated_tests(fn, refreshed, run_output, index)


def _run_all_tests(output_dir, repo_dir, timeout):
    from src.runner import run_single_test
    outcomes = {}
    tests_dir = os.path.join(output_dir, "generated_tests")
    if not os.path.isdir(tests_dir):
        return outcomes
    for fn_dir in sorted(os.listdir(tests_dir)):
        fn_path = os.path.join(tests_dir, fn_dir)
        for fname in _iter_test_files(fn_path):
            print(f"  {fn_dir}/{fname}...", end=" ", flush=True)
            r = run_single_test(os.path.join(fn_path, fname), repo_dir, timeout=timeout)
            p, f_, e = len(r["passed"]), len(r["failed"]), len(r["errors"])
            print(f"{p} passed, {f_} failed, {e} errors")
            outcomes[(fn_dir, fname)] = r
    return outcomes


# ── Public API ────────────────────────────────────────────────────────────────

def run_for_functions(functions, output_dir, repo_dir, config,
                      max_iter=3, threshold=80.0, delta_min=2.0):
    """Generate tests for every function, run them, attempt one-shot fixes.

    Returns (test_outcomes, failures, fix_attempted).
    Used by main.py's BugsInPy loop; run_pipeline is the single-function equivalent.
    """
    from src.writer import write_function, write_generated_tests, generate_automation
    from src.reporter import parse_failures

    print("\nGenerating tests...")
    for i, fn in enumerate(functions):
        print(f"\n[{i+1}/{len(functions)}] {fn['name']}")
        write_function(fn, output_dir, i)
        generated = _generate_initial_tests(fn, config)
        write_generated_tests(fn, generated, output_dir, i)
        # Coverage loop only runs when max_iter > 1 to avoid extra work in fast mode
        if max_iter > 1:
            _coverage_loop(fn, output_dir, repo_dir, i, config, max_iter, threshold, delta_min)

    generate_automation(output_dir, repo_dir)

    print("\nRunning tests...")
    test_outcomes = _run_all_tests(output_dir, repo_dir, config["timeouts"]["test"])

    failures = parse_failures(test_outcomes)
    any_fix_attempted = False
    if failures:
        print("\nFix pass...")
        fn_by_key = {f"{fn['name']}_{i}": (fn, i) for i, fn in enumerate(functions)}
        outcomes_by_fn = {}
        for (fn_dir, fname), result in test_outcomes.items():
            outcomes_by_fn.setdefault(fn_dir, {})[(fn_dir, fname)] = result
        for fn_key, fn_outcomes in outcomes_by_fn.items():
            if fn_key not in fn_by_key:
                continue
            fn, idx = fn_by_key[fn_key]
            if not any(f["function"] == fn_key for f in failures):
                continue
            print(f"  {fn_key}:")
            updated, attempted = _one_shot_fix(fn, fn_key, fn_outcomes, repo_dir, output_dir, idx, config)
            if attempted:
                any_fix_attempted = True
            test_outcomes.update(updated)

    failures = parse_failures(test_outcomes)
    return test_outcomes, failures, any_fix_attempted




def run_pipeline(
    repo_url: str,
    fn_name: str,
    *,
    description: str = "",
    provider: str = "deepseek",
    model: str | None = None,
    preset: str = "default",
    output_dir: str = "eval_output",
    install_deps: bool = True,
    api_key: str | None = None,
) -> dict:
    """Clone a repo, generate tests for one function, run them, attempt a fix.

    Returns:
        {
            "status":        "done" | "error",
            "error":         str | None,
            "output_dir":    str,
            "fn_name":       str,
            "fn_file":       str,
            "failures":      list[dict],
            "fix_attempted": bool,
            "test_outcomes": dict,   # raw pytest results per test file
        }
    """
    from src.extractor import clone_repo, extract_functions
    from src.writer import write_meta, write_function, write_generated_tests
    from src.reporter import parse_failures

    cfg     = _build_config(provider, model, api_key=api_key)
    preset_cfg = PRESETS.get(preset, PRESETS["default"])
    max_iter  = preset_cfg["max_iterations"]
    threshold = preset_cfg["coverage_threshold"]
    timeout   = preset_cfg["test_timeout"]
    cfg["timeouts"]["test"] = timeout

    run_output = os.path.join(output_dir, repo_name_from_url(repo_url))
    write_meta(repo_url, run_output)

    tmp = tempfile.mkdtemp()
    try:
        print(f"\nCloning {repo_url}...")
        clone_repo(repo_url, tmp)

        if install_deps:
            print("Installing repo deps...")
            _install_deps(tmp)

        print(f"Extracting '{fn_name}'...")
        all_fns = extract_functions(tmp)
        matches = [f for f in all_fns if f["name"] == fn_name]
        if not matches:
            names = sorted({f["name"] for f in all_fns})
            return {
                "status": "error",
                "error": f"'{fn_name}' not found. Available ({len(names)}): {names[:20]}",
                "output_dir": run_output, "fn_name": fn_name, "fn_file": "",
                "failures": [], "fix_attempted": False, "test_outcomes": {},
            }

        fn = matches[0]
        if description:
            fn["description"] = description

        print(f"Target : {fn['file_path']} lines {fn['start_line']}-{fn['end_line']}")
        print(f"LLM    : {provider}/{cfg['llm']['model']}  preset={preset}")

        from src.writer import generate_automation
        write_function(fn, run_output, 0)
        generated = _generate_initial_tests(fn, cfg)
        write_generated_tests(fn, generated, run_output, 0)
        _coverage_loop(fn, run_output, tmp, 0, cfg, max_iter, threshold)
        generate_automation(run_output, tmp)

        print("\nRunning tests...")
        test_outcomes = _run_all_tests(run_output, tmp, timeout)

        # ── Fix ───────────────────────────────────────────────────────────────
        failures = parse_failures(test_outcomes)
        fix_attempted = False
        if failures:
            fn_key = f"{fn['name']}_0"
            fn_outcomes = {k: v for k, v in test_outcomes.items() if k[0] == fn_key}
            if any(f["function"] == fn_key for f in failures):
                print(f"\nFix pass — {fn_key}:")
                test_outcomes, fix_attempted = _one_shot_fix(
                    fn, fn_key, fn_outcomes, tmp, run_output, 0, cfg
                )

        failures = parse_failures(test_outcomes)
        return {
            "status": "done",
            "error": None,
            "output_dir": run_output,
            "fn_name": fn["name"],
            "fn_file": fn["file_path"],
            "failures": failures,
            "fix_attempted": fix_attempted,
            "test_outcomes": {str(k): v for k, v in test_outcomes.items()},
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "output_dir": run_output,
            "fn_name": fn_name, "fn_file": "",
            "failures": [], "fix_attempted": False, "test_outcomes": {},
        }
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
