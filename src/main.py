import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ast
import shutil
import tempfile

from dotenv import load_dotenv

from src.config import load_config
from src.extractor import clone_repo, extract_functions
from src.agents import call_agent, call_fix_agent, call_oracle_revision_agent, strip_code_fences
from src.runner import run_single_test
from src.writer import write_meta, write_function, write_generated_tests, generate_automation, write_fixed_function, write_fix_artifacts, replace_function_in_repo
from src.reporter import parse_failures, print_bug_report, write_bug_report


WHITEBOX_TYPES = ["whitebox"]
BLACKBOX_TYPES = ["blackbox"]


def _is_valid_function_fix(code, fn_name):
    """Return True only if code is a valid Python function fix (not a test file)."""
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


def parse_args():
    p = argparse.ArgumentParser(description="Generate unit tests for a GitHub repo and detect bugs")
    p.add_argument("--repo", default="https://github.com/keon/algorithms", help="GitHub repo URL")
    p.add_argument("--output", default="./eval_output", help="Output directory")
    p.add_argument("--limit", type=int, default=3, help="Max functions to process")
    p.add_argument("--min-lines", type=int, default=0, dest="min_lines", help="Skip functions shorter than N lines")
    p.add_argument("--max-lines", type=int, default=0, dest="max_lines", help="Skip functions longer than N lines")
    p.add_argument("--min-branches", type=int, default=0, dest="min_branches", help="Skip functions with fewer than N branches")
    p.add_argument("--max-branches", type=int, default=0, dest="max_branches", help="Skip functions with more than N branches")
    p.add_argument("--stratify", action="store_true", help="Sample evenly across simple/moderate/complex functions")
    p.add_argument("--provider", default=None, help="LLM provider (deepseek, openai, anthropic, ollama)")
    p.add_argument("--model", default=None, help="LLM model name")
    return vars(p.parse_args())


def _build_config_overrides(args):
    overrides = {}
    if args.get("provider"):
        overrides.setdefault("llm", {})["provider"] = args["provider"]
    if args.get("model"):
        overrides.setdefault("llm", {})["model"] = args["model"]
    return overrides or None


def _fn_complexity(source):
    lines = len(source.strip().splitlines())
    try:
        tree = ast.parse(source)
        branches = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler))
        )
    except SyntaxError:
        branches = 0
    return lines, branches


def _classify_complexity(source):
    lines, branches = _fn_complexity(source)
    if lines <= 15 and branches <= 2:
        return "simple"
    elif lines <= 40 and branches <= 6:
        return "moderate"
    else:
        return "complex"


def _stratified_sample(functions, limit):
    import random
    buckets = {"simple": [], "moderate": [], "complex": []}
    for fn in functions:
        buckets[_classify_complexity(fn["source"])].append(fn)
    for b in buckets:
        random.shuffle(buckets[b])
    per_bucket = max(1, limit // 3)
    selected = []
    overflow = []
    for bucket_name in ["simple", "moderate", "complex"]:
        pool = buckets[bucket_name]
        selected.extend(pool[:per_bucket])
        overflow.extend(pool[per_bucket:])
    random.shuffle(overflow)
    remaining = limit - len(selected)
    if remaining > 0:
        selected.extend(overflow[:remaining])
    return selected[:limit]


def _run_fn_tests(fn_key, output_dir, repo_clone_dir, config):
    """Run all test files for a function directory. Returns outcomes dict."""
    outcomes = {}
    test_dir = os.path.join(output_dir, "generated_tests", fn_key)
    if not os.path.isdir(test_dir):
        return outcomes
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            outcomes[(fn_key, fname)] = run_single_test(
                os.path.join(test_dir, fname), repo_clone_dir, timeout=config["timeouts"]["test"]
            )
    return outcomes


def run_one_shot_fix(fn, fn_key, test_outcomes, repo_clone_dir, output_dir, idx, config):
    """Single fix attempt: diagnose + patch + re-run once. No iteration."""
    fn_failures = [f for f in parse_failures(test_outcomes) if f["function"] == fn_key]
    if not fn_failures or all(f["kind"] == "error" for f in fn_failures):
        if fn_failures:
            print("all failures are collection errors, skipping fix")
        return test_outcomes, False

    print(f"  attempting one-shot fix ({len(fn_failures)} failure(s))...", end=" ", flush=True)

    fixed_raw = call_fix_agent(fn, fn_failures, config)
    if not fixed_raw or not fixed_raw.strip():
        print("no output")
        return test_outcomes, False

    fixed_code = strip_code_fences(fixed_raw)
    if not _is_valid_function_fix(fixed_code, fn["name"]):
        print("invalid fix output (test file or malformed), skipping")
        return test_outcomes, False

    write_fix_artifacts(fn, output_dir, idx, 0,
                        diagnosis=getattr(fixed_raw, "diagnosis", ""),
                        diagnosis_context=getattr(fixed_raw, "diagnosis_context", ""),
                        fix_context=getattr(fixed_raw, "fix_context", ""))
    fn["end_line"] = replace_function_in_repo(fn, fixed_code, repo_clone_dir)
    fn["source"] = fixed_code
    write_fixed_function(fn, fixed_code, output_dir, idx, iteration=0)

    outcomes = _run_fn_tests(fn_key, output_dir, repo_clone_dir, config)
    remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

    # oracle revision: revise stale expected values in tests that still fail after a correct fix
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
            revised_code = strip_code_fences(revised_raw)
            try:
                ast.parse(revised_code)
                with open(test_path, "w", encoding="utf-8") as fh:
                    fh.write(revised_code)
            except SyntaxError:
                pass

        outcomes = _run_fn_tests(fn_key, output_dir, repo_clone_dir, config)
        remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

    print("converged" if not remaining else f"{len(remaining)} failure(s) remain")
    return outcomes, True


def main():
    load_dotenv()
    args = parse_args()
    config = load_config(_build_config_overrides(args))

    repo = args["repo"]
    output_base = args["output"]
    limit = args["limit"]
    min_lines = args["min_lines"]
    max_lines = args["max_lines"]
    min_branches = args["min_branches"]
    max_branches = args["max_branches"]
    stratify = args["stratify"]

    all_types = WHITEBOX_TYPES + BLACKBOX_TYPES
    print(f"Test types: whitebox={WHITEBOX_TYPES}, blackbox={BLACKBOX_TYPES}")
    print(f"LLM: {config['llm']['provider']}/{config['llm']['model']}")

    repo_name = repo.rstrip("/").split("/")[-1].replace(".git", "")
    output_dir = os.path.join(output_base, repo_name)
    write_meta(repo, output_dir)

    tmp = tempfile.mkdtemp()
    print(f"Cloning {repo}...")
    clone_repo(repo, tmp)

    print("Extracting functions...")
    all_functions = extract_functions(tmp)
    print(f"Found {len(all_functions)} function(s)")

    if not all_functions:
        shutil.rmtree(tmp, ignore_errors=True)
        return

    # Apply filters
    if min_lines > 0:
        all_functions = [fn for fn in all_functions if len(fn["source"].strip().splitlines()) >= min_lines]
        print(f"After --min-lines {min_lines}: {len(all_functions)} function(s)")
    if max_lines > 0:
        all_functions = [fn for fn in all_functions if len(fn["source"].strip().splitlines()) <= max_lines]
        print(f"After --max-lines {max_lines}: {len(all_functions)} function(s)")
    if min_branches > 0:
        all_functions = [fn for fn in all_functions if _fn_complexity(fn["source"])[1] >= min_branches]
        print(f"After --min-branches {min_branches}: {len(all_functions)} function(s)")
    if max_branches > 0:
        all_functions = [fn for fn in all_functions if _fn_complexity(fn["source"])[1] <= max_branches]
        print(f"After --max-branches {max_branches}: {len(all_functions)} function(s)")

    if stratify:
        functions = _stratified_sample(all_functions, limit)
        buckets = {}
        for fn in functions:
            b = _classify_complexity(fn["source"])
            buckets[b] = buckets.get(b, 0) + 1
        print(f"Stratified sample: {len(functions)} function(s) — {buckets}")
    else:
        functions = all_functions[:limit]
        print(f"Using first {limit} function(s)")

    # --- Step 1-2: Generate + write tests for each function ---

    print("\nGenerating tests...")
    for i, fn in enumerate(functions):
        print(f"\n--- Function {i + 1}/{len(functions)}: {fn['name']} ---")
        write_function(fn, output_dir, i)

        generated = {}
        for test_type in all_types:
            print(f"  generating {test_type}...", end=" ", flush=True)
            code = call_agent(test_type, fn, config)
            if code and code.strip():
                generated[test_type] = code
                print(f"ok ({len(code)} chars)")
            else:
                print("empty")

        write_generated_tests(fn, generated, output_dir, i)
        print(f"  wrote {len(generated)} test file(s)")

    # --- Step 3: Generate automation script ---

    generate_automation(output_dir, tmp)
    print(f"\nAutomation script: {os.path.join(output_dir, 'automation', 'run_tests.sh')}")

    # --- Step 4: Execute all tests ---

    print("\nRunning tests...")
    test_outcomes = {}
    generated_tests_base = os.path.join(output_dir, "generated_tests")

    if os.path.isdir(generated_tests_base):
        for fn_dir in sorted(os.listdir(generated_tests_base)):
            fn_path = os.path.join(generated_tests_base, fn_dir)
            if not os.path.isdir(fn_path):
                continue
            for fname in sorted(os.listdir(fn_path)):
                if fname.startswith("test_") and fname.endswith(".py"):
                    test_file = os.path.join(fn_path, fname)
                    print(f"  {fn_dir}/{fname}...", end=" ", flush=True)
                    result = run_single_test(test_file, tmp, timeout=config["timeouts"]["test"])
                    p = len(result["passed"])
                    f_count = len(result["failed"])
                    e = len(result["errors"])
                    print(f"{p} passed, {f_count} failed, {e} errors")
                    test_outcomes[(fn_dir, fname)] = result

    # --- Step 5-6: Parse failures + one-shot fix ---

    failures = parse_failures(test_outcomes)

    if failures:
        print("\nRunning one-shot fix pass...")
        fn_by_key = {f"{fn['name']}_{i}": (fn, i) for i, fn in enumerate(functions)}

        # group test_outcomes by function directory
        outcomes_by_fn = {}
        for (fn_dir, fname), result in test_outcomes.items():
            outcomes_by_fn.setdefault(fn_dir, {})[(fn_dir, fname)] = result

        for fn_key, fn_outcomes in outcomes_by_fn.items():
            if fn_key not in fn_by_key:
                continue
            fn, idx = fn_by_key[fn_key]
            fn_failures = [f for f in failures if f["function"] == fn_key]
            if not fn_failures:
                continue
            print(f"  {fn_key}:")
            final_outcomes, _ = run_one_shot_fix(
                fn, fn_key, fn_outcomes, tmp, output_dir, idx, config,
            )
            test_outcomes.update(final_outcomes)

        failures = parse_failures(test_outcomes)

    print_bug_report(failures, repo)
    write_bug_report(failures, repo, output_dir)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone. Output: {output_dir}")
    if failures:
        print(f"Bug report: {os.path.join(output_dir, 'bug_report.txt')}")


def cli():
    main()


if __name__ == "__main__":
    main()
