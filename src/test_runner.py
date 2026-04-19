"""Run pytest on a test file and measure line/branch coverage for a target function."""
import json
import os
import subprocess
import sys
import tempfile


def run_tests(test_file, repo_dir, timeout=60, per_test_timeout=None):
    """Run pytest on test_file and return structured results.

    per_test_timeout: if set, passes --timeout=N to pytest-timeout to kill
    individual hanging tests after N seconds (requires pytest-timeout installed).
    """
    report_file = tempfile.mktemp(suffix=".json")
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_dir + os.pathsep + env.get("PYTHONPATH", "")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", test_file,
             "--json-report", f"--json-report-file={report_file}",
             *([f"--timeout={per_test_timeout}"] if per_test_timeout else []),
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


def measure_coverage(test_file, fn, repo_dir, timeout=60):
    """Run coverage.py on test_file and return coverage info for fn's line range.

    Returns dict with: covered_lines, uncovered_lines, coverage_pct, fn_start_line,
    fn_end_line, fn_source_lines (uncovered line -> source text), error.
    """
    fn_abs = os.path.normpath(os.path.join(repo_dir, fn["file_path"]))
    data_file = tempfile.mktemp(suffix=".coverage")
    json_file = tempfile.mktemp(suffix=".json")
    env = os.environ.copy()
    env["PYTHONPATH"] = repo_dir + os.pathsep + env.get("PYTHONPATH", "")
    try:
        subprocess.run(
            [sys.executable, "-m", "coverage", "run",
             f"--data-file={data_file}", f"--include={fn_abs}", "--branch",
             "-m", "pytest", test_file, "-q", "--no-header", "--tb=no"],
            capture_output=True, text=True, env=env, timeout=timeout,
        )
        result = subprocess.run(
            [sys.executable, "-m", "coverage", "json", f"--data-file={data_file}", "-o", json_file],
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
