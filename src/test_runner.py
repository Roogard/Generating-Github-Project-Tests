"""Run pytest on a test file and measure line/branch coverage for a target function."""
import json
import os
import subprocess
import sys
import tempfile


def run_tests(test_file, repo_dir, timeout=60, per_test_timeout=None, python_bin=None):
    """Run pytest on test_file and return structured results.

    When per_test_timeout is set, uses subprocess-per-test isolation: each test
    runs in its own pytest invocation bounded by per_test_timeout. On Windows,
    pytest-timeout's thread method calls os._exit() on hang, skipping the JSON
    report — isolation avoids that by putting each test in a disposable process.

    Falls back to the fast batch path when per_test_timeout is None.

    python_bin: optional path to a Python interpreter (e.g. an ephemeral uv venv)
    whose site-packages should be used. Defaults to sys.executable.
    """
    if per_test_timeout is None:
        return _run_tests_batch(test_file, repo_dir, timeout, python_bin)
    return _run_tests_isolated(test_file, repo_dir, timeout, per_test_timeout, python_bin)


def _pytest_env(repo_dir):
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_dir + os.pathsep + env.get("PYTHONPATH", "")
    return env


def _collect_nodeids(test_file, repo_dir, python_bin=None):
    """Ask pytest which test functions the file contains.

    pytest's `--collect-only -q` emits nodeids relative to its cwd, which don't
    resolve when passed back to a fresh pytest subprocess. We strip the path
    half and reconstruct with the caller's absolute test_file path.

    Returns a list of full nodeid strings like `C:\\abs\\path\\test.py::test_foo`
    or [] on collection error.
    """
    py = python_bin or sys.executable
    abs_test_file = os.path.abspath(test_file)
    try:
        result = subprocess.run(
            [py, "-m", "pytest", abs_test_file, "--collect-only", "-q", "--no-header"],
            capture_output=True, text=True, env=_pytest_env(repo_dir), timeout=30,
        )
    except subprocess.TimeoutExpired:
        return []
    if result.returncode != 0 and "::" not in result.stdout:
        return []
    nodeids = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" not in line or line.startswith("<") or line.startswith("="):
            continue
        test_part = line.split("::", 1)[1]  # everything after the first :: (handles class::method too)
        if test_part.startswith("test_") or "::test_" in test_part:
            nodeids.append(f"{abs_test_file}::{test_part}")
    return nodeids


def _run_tests_isolated(test_file, repo_dir, outer_timeout, per_test_timeout, python_bin):
    """Run each test function in its own pytest subprocess.

    A subprocess timeout of per_test_timeout + overhead bounds each test. A test
    that gets killed that way is reported as failed (not errored) — an infinite
    loop under test IS a test failure for our purposes.
    """
    py = python_bin or sys.executable
    env = _pytest_env(repo_dir)

    nodeids = _collect_nodeids(test_file, repo_dir, python_bin)
    if not nodeids:
        return {"passed": [], "failed": [], "errors": ["__collection_error__"],
                "failure_details": [],
                "error_details": [{"nodeid": "__collection_error__",
                                   "longrepr": f"pytest found no tests in {os.path.basename(test_file)}"}],
                "test_file_path": os.path.abspath(test_file),
                "stdout": "", "stderr": "", "returncode": 5}

    # Per-process wall-clock budget: per_test_timeout plus ~3s for pytest startup/teardown.
    sub_timeout = per_test_timeout + 3
    passed, failed, errors, timed_out = [], [], [], []
    failure_details, error_details = [], []
    combined_stdout = []

    for nodeid in nodeids:
        name = nodeid.split("::")[-1]
        report_file = tempfile.mktemp(suffix=".json")
        cmd = [py, "-m", "pytest", nodeid,
               "--json-report", f"--json-report-file={report_file}",
               f"--timeout={per_test_timeout}",
               "-q", "--tb=short", "--no-header"]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, env=env, timeout=sub_timeout)
        except subprocess.TimeoutExpired:
            # Subprocess wall-clock kill — test hung past pytest-timeout too.
            # Treat as failure (the code under test is broken / diverges from spec)
            # and record in timed_out so callers can deselect these when measuring coverage.
            if os.path.exists(report_file):
                os.remove(report_file)
            failed.append(name)
            timed_out.append(name)
            failure_details.append({"nodeid": nodeid,
                                    "longrepr": f"hung past {per_test_timeout}s per-test timeout",
                                    "crash": {"timeout": per_test_timeout}})
            combined_stdout.append(f"{nodeid}: TIMEOUT (>{per_test_timeout}s)")
            continue

        combined_stdout.append(result.stdout)
        parsed = _parse_single_report(report_file, nodeid, result)
        longrepr = parsed["longrepr"] or ""
        is_timeout = "Timeout" in longrepr or "timeout" in longrepr.lower()[:40]
        if parsed["outcome"] == "passed":
            passed.append(name)
        elif parsed["outcome"] == "failed":
            failed.append(name)
            if is_timeout:
                timed_out.append(name)
            failure_details.append({"nodeid": nodeid,
                                    "longrepr": longrepr,
                                    "crash": parsed["crash"]})
        else:  # error or unknown
            # pytest-timeout reports timeouts with outcome=error AND a "Timeout"
            # longrepr. Promote those to timed_out so callers can treat them as
            # "test killed because code under test hung" — the signal an F→P
            # detection needs — rather than "test broken / setup error".
            if is_timeout:
                failed.append(name)  # counts as failure for F→P accounting
                timed_out.append(name)
                failure_details.append({"nodeid": nodeid, "longrepr": longrepr,
                                        "crash": {"timeout": per_test_timeout}})
            else:
                errors.append(name)
                error_details.append({"nodeid": nodeid, "longrepr": longrepr})

    return {
        "passed": passed, "failed": failed, "errors": errors, "timed_out": timed_out,
        "failure_details": failure_details, "error_details": error_details,
        "test_file_path": os.path.abspath(test_file),
        "stdout": "\n".join(combined_stdout), "stderr": "", "returncode": 0 if not failed and not errors else 1,
    }


def _parse_single_report(report_file, nodeid, result):
    """Extract outcome/longrepr from a single-test JSON report. Cleans up the file."""
    try:
        if not os.path.exists(report_file):
            return {"outcome": "error", "longrepr": result.stdout[-600:] if result.stdout else "(no output)",
                    "crash": {}}
        with open(report_file, encoding="utf-8") as f:
            report = json.load(f)
        os.remove(report_file)
    except (OSError, json.JSONDecodeError) as e:
        return {"outcome": "error", "longrepr": f"report parse failed: {e}", "crash": {}}

    tests = report.get("tests", [])
    if not tests:
        return {"outcome": "error", "longrepr": result.stdout[-600:], "crash": {}}
    t = tests[0]
    outcome = t.get("outcome", "error")
    call = t.get("call", {}) or {}
    setup = t.get("setup", {}) or {}
    longrepr = call.get("longrepr", "") or setup.get("longrepr", "") or ""
    return {"outcome": outcome, "longrepr": longrepr, "crash": call.get("crash", {}) or {}}


def _run_tests_batch(test_file, repo_dir, timeout, python_bin):
    """Original single-subprocess path — faster, used when no per-test timeout is needed."""
    py = python_bin or sys.executable
    report_file = tempfile.mktemp(suffix=".json")
    env = _pytest_env(repo_dir)
    try:
        result = subprocess.run(
            [py, "-m", "pytest", test_file,
             "--json-report", f"--json-report-file={report_file}",
             "-q", "--tb=short", "--no-header"],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        if os.path.exists(report_file):
            os.remove(report_file)
        return {"passed": [], "failed": [], "errors": ["__timeout__"],
                "failure_details": [], "error_details": [],
                "stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1}

    passed, failed, errors, failure_details, error_details = [], [], [], [], []
    if os.path.exists(report_file):
        with open(report_file, encoding="utf-8") as f:
            report = json.load(f)
        for t in report.get("tests", []):
            name = t["nodeid"].split("::")[-1]
            outcome = t.get("outcome", "error")
            if outcome == "passed":
                passed.append(name)
            elif outcome == "failed":
                failed.append(name)
                call = t.get("call", {})
                failure_details.append({"nodeid": t["nodeid"], "longrepr": call.get("longrepr", ""), "crash": call.get("crash", {})})
            else:
                errors.append(name)
                setup = t.get("setup", {})
                error_details.append({"nodeid": t["nodeid"], "longrepr": setup.get("longrepr", "") or t.get("call", {}).get("longrepr", "")})
        os.remove(report_file)
    else:
        errors.append("__import_or_collection_error__")
        error_details.append({"nodeid": "__import_or_collection_error__", "longrepr": result.stdout})

    if not passed and not failed and not errors and result.returncode != 0:
        errors.append("__collection_error__")
        error_details.append({"nodeid": "__collection_error__", "longrepr": result.stdout})

    return {
        "passed": passed, "failed": failed, "errors": errors,
        "failure_details": failure_details, "error_details": error_details,
        "test_file_path": os.path.abspath(test_file),
        "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode,
    }


def measure_coverage(test_file, fn, repo_dir, timeout=60, per_test_timeout=None,
                     deselect_tests=None, python_bin=None):
    """Run coverage.py on test_file and return coverage info for fn's line range.

    per_test_timeout: pytest-timeout value (applies per-test, but on Windows
        a session kill on timeout loses all data — prefer deselecting known
        hangers instead).
    deselect_tests: list of test function names (e.g. ['test_one', 'test_two'])
        to exclude via pytest --deselect. Use after run_tests identifies tests
        that hung or errored; running coverage without them yields usable
        coverage data for the tests that actually work.

    Returns dict with: covered_lines, uncovered_lines, coverage_pct, fn_start_line,
    fn_end_line, fn_source_lines (uncovered line -> source text), error.
    """
    py = python_bin or sys.executable
    fn_abs = os.path.normpath(os.path.join(repo_dir, fn["file_path"]))
    data_file = tempfile.mktemp(suffix=".coverage")
    json_file = tempfile.mktemp(suffix=".json")
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_dir + os.pathsep + env.get("PYTHONPATH", "")
    # Use `-k "not test_foo and not test_bar"` — matches test names without any
    # path normalization dance that --deselect needs on Windows.
    k_args = []
    if deselect_tests:
        expr = " and ".join(f"not {name}" for name in deselect_tests)
        k_args = ["-k", expr]
    try:
        subprocess.run(
            [py, "-m", "coverage", "run",
             f"--data-file={data_file}", f"--include={fn_abs}", "--branch",
             "-m", "pytest", test_file,
             *k_args,
             *([f"--timeout={per_test_timeout}"] if per_test_timeout else []),
             "-q", "--no-header", "--tb=no"],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
        result = subprocess.run(
            [py, "-m", "coverage", "json", f"--data-file={data_file}", "-o", json_file],
            capture_output=True, text=True, env=env, timeout=30,
        )
        if result.returncode != 0 or not os.path.exists(json_file):
            return _cov_error(fn, f"coverage json failed: {result.stderr.strip()}")

        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        needle = os.path.normcase(fn_abs)
        file_entry = next(
            (v for k, v in data.get("files", {}).items() if os.path.normcase(os.path.normpath(k)) == needle),
            None,
        )
        if file_entry is None:
            return _cov_error(fn, f"file not found in coverage report: {fn_abs}")

        start, end = fn["start_line"], fn["end_line"]
        covered = [l for l in file_entry.get("executed_lines", []) if start <= l <= end]
        uncovered = [l for l in file_entry.get("missing_lines", []) if start <= l <= end]
        total = len(covered) + len(uncovered)
        pct = (len(covered) / total * 100.0) if total > 0 else 100.0

        src_lines = fn["source"].splitlines()
        source_map = {n: src_lines[n - start] for n in uncovered if 0 <= n - start < len(src_lines)}

        return {
            "covered_lines": sorted(covered), "uncovered_lines": sorted(uncovered),
            "coverage_pct": round(pct, 1), "fn_start_line": start, "fn_end_line": end,
            "fn_source_lines": source_map, "error": None,
        }
    except subprocess.TimeoutExpired:
        return _cov_error(fn, f"coverage timed out after {timeout}s")
    except Exception as e:
        return _cov_error(fn, str(e))
    finally:
        for p in (data_file, json_file):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass


def _cov_error(fn, message):
    return {
        "covered_lines": [], "uncovered_lines": [], "coverage_pct": 0.0,
        "fn_start_line": fn.get("start_line", 0), "fn_end_line": fn.get("end_line", 0),
        "fn_source_lines": {}, "error": message,
    }
