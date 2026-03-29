import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import subprocess
import tempfile


_PASSED = "passed"
_FAILED = "failed"
_ERRORS = "errors"


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
            _PASSED: [],
            _FAILED: [],
            _ERRORS: ["__timeout__"],
            "stdout": "",
            "stderr": f"Test timed out after {timeout}s",
            "returncode": -1,
        }

    tests_passed = []
    tests_failed = []
    tests_error = []
    failure_details = []
    error_details = []

    if os.path.exists(report_file):
        with open(report_file, encoding="utf-8") as f:
            report = json.load(f)
        for t in report.get("tests", []):
            name = t["nodeid"].split("::")[-1]
            outcome = t.get("outcome", "error")
            if outcome == _PASSED:
                tests_passed.append(name)
            elif outcome == _FAILED:
                tests_failed.append(name)
                call = t.get("call", {})
                failure_details.append({
                    "nodeid": t["nodeid"],
                    "longrepr": call.get("longrepr", ""),
                    "crash": call.get("crash", {}),
                })
            else:
                tests_error.append(name)
                setup = t.get("setup", {})
                error_details.append({
                    "nodeid": t["nodeid"],
                    "longrepr": setup.get("longrepr", "") or t.get("call", {}).get("longrepr", ""),
                })
        os.remove(report_file)
    else:
        tests_error.append("__import_or_collection_error__")
        # capture collection error from stdout (pytest prints it there)
        error_details.append({"nodeid": "__import_or_collection_error__", "longrepr": result.stdout})

    # pytest compiled the file but collected 0 tests (e.g. all errored during collection)
    if not tests_passed and not tests_failed and not tests_error and result.returncode != 0:
        tests_error.append("__collection_error__")
        error_details.append({"nodeid": "__collection_error__", "longrepr": result.stdout})

    return {
        _PASSED: tests_passed,
        _FAILED: tests_failed,
        _ERRORS: tests_error,
        "failure_details": failure_details,
        "error_details": error_details,
        "test_file_path": os.path.abspath(test_file),
        "stdout": result.stdout,
        "stderr": result.stderr,
        "returncode": result.returncode,
    }


