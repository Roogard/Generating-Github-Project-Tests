"""
Test runner.

Executes the generated test files against the original repo and writes results.json.
Use this after the main pipeline to see how many tests pass/fail.

Usage:
    uv run python -m src.runner --output ./eval_output/algorithms

Output: <output_dir>/results.json with pass/fail/error counts per function per test type.
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import shutil
import subprocess
import tempfile

from src.extractor import clone_repo


def discover_tests(test_cases_dir):
    tests = []
    for func_dir in sorted(os.listdir(test_cases_dir)):
        func_path = os.path.join(test_cases_dir, func_dir)
        if not os.path.isdir(func_path):
            continue
        for fname in sorted(os.listdir(func_path)):
            if fname.startswith("test_") and fname.endswith(".py"):
                test_type = fname[len("test_"):-len(".py")]
                tests.append({
                    "function": func_dir,
                    "test_type": test_type,
                    "path": os.path.join(func_path, fname),
                })
    return tests


def run_single_test(test_file, repo_clone_dir, timeout=60):
    report_file = tempfile.mktemp(suffix=".json")
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_clone_dir + os.pathsep + env.get("PYTHONPATH", "")

    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file,
             "--json-report", f"--json-report-file={report_file}",
             "-q", "--tb=short", "--no-header"],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        if os.path.exists(report_file):
            os.remove(report_file)
        return {
            "passed": [],
            "failed": [],
            "errors": ["__timeout__"],
            "stdout": "",
            "stderr": f"Test timed out after {timeout}s",
            "returncode": -1,
        }

    tests_passed = []
    tests_failed = []
    tests_error = []

    if os.path.exists(report_file):
        with open(report_file, encoding="utf-8") as f:
            report = json.load(f)
        for t in report.get("tests", []):
            name = t["nodeid"].split("::")[-1]
            outcome = t.get("outcome", "error")
            if outcome == "passed":
                tests_passed.append(name)
            elif outcome == "failed":
                tests_failed.append(name)
            else:
                tests_error.append(name)
        os.remove(report_file)
    else:
        tests_error.append("__import_or_collection_error__")

    # pytest compiled the file but collected 0 tests (e.g. all errored during collection)
    if not tests_passed and not tests_failed and not tests_error and result.returncode != 0:
        tests_error.append("__collection_error__")

    return {
        "passed": tests_passed,
        "failed": tests_failed,
        "errors": tests_error,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


def run_tests(output_dir):
    meta_path = os.path.join(output_dir, "meta.json")
    with open(meta_path, encoding="utf-8") as f:
        meta = json.load(f)

    repo_url = meta["repo_url"]
    repo_name = meta["repo_name"]
    test_cases_dir = os.path.join(output_dir, "test_cases")

    tmp = tempfile.mkdtemp()
    print(f"Cloning {repo_url}...")
    clone_repo(repo_url, tmp)

    tests = discover_tests(test_cases_dir)
    print(f"Found {len(tests)} test file(s)")

    total_passed = 0
    total_failed = 0
    total_errors = 0
    functions = {}

    for t in tests:
        func_name = t["function"]
        test_type = t["test_type"]
        print(f"  Running {func_name}/{test_type}...", end=" ")

        result = run_single_test(t["path"], tmp)

        p, f_count, e = len(result["passed"]), len(result["failed"]), len(result["errors"])
        total_passed += p
        total_failed += f_count
        total_errors += e
        print(f"{p} passed, {f_count} failed, {e} errors")

        if func_name not in functions:
            functions[func_name] = {}
        functions[func_name][test_type] = {
            "passed": result["passed"],
            "failed": result["failed"],
            "errors": result["errors"],
        }

    shutil.rmtree(tmp, ignore_errors=True)

    results = {
        "repo": repo_name,
        "repo_url": repo_url,
        "total": total_passed + total_failed + total_errors,
        "passed": total_passed,
        "failed": total_failed,
        "errors": total_errors,
        "functions": functions,
    }

    results_path = os.path.join(output_dir, "results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"\nResults written to {results_path}")
    print(f"Total: {results['total']} | Passed: {total_passed} | Failed: {total_failed} | Errors: {total_errors}")

    return results


if __name__ == "__main__":
    output = "./eval_output/algorithms"
    for arg in sys.argv[1:]:
        if arg.startswith("--output="):
            output = arg.split("=", 1)[1]
        elif sys.argv[sys.argv.index(arg) - 1] == "--output":
            output = arg
    if "--output" in sys.argv and sys.argv[-1] == "--output":
        print("Error: --output requires a path")
        sys.exit(1)

    run_tests(output)
