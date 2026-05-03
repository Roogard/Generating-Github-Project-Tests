"""Run pytest on a test file and return structured results.

All process invocations go through a `Runtime` (local or Docker). The runtime
translates host paths to runtime-visible paths (identity for local; mount-
relative for Docker) so this module can stay path-agnostic.
"""
import json
import os

from src.runtime.base import Runtime, RuntimeResult


def run_tests(test_file, repo_dir, runtime: Runtime,
              timeout=60, per_test_timeout=None):
    """Run pytest on test_file and return structured results.

    When per_test_timeout is set, uses subprocess-per-test isolation: each test
    runs in its own pytest invocation bounded by per_test_timeout. On Windows,
    pytest-timeout's thread method calls os._exit() on hang, skipping the JSON
    report — isolation avoids that by putting each test in a disposable process.

    Falls back to the fast batch path when per_test_timeout is None.
    """
    if per_test_timeout is None:
        return _run_tests_batch(test_file, repo_dir, runtime, timeout)
    return _run_tests_isolated(test_file, repo_dir, runtime, timeout, per_test_timeout)


def _pytest_env(repo_dir, runtime: Runtime):
    """PYTHONPATH for pytest. We pass the runtime-translated repo_dir so the
    pytest subprocess (potentially inside the container) can import the
    target package."""
    return {"PYTHONPATH": runtime.translate(repo_dir)}


def _runtime_test_path(test_file: str, runtime: Runtime) -> str:
    """Where the test file is visible from inside the runtime.

    On SwtBenchRuntime, the host file gets copied into /testbed/<name>
    by the per-exec preamble; in-image pytest reads from there. On other
    runtimes it's just translate(test_file). Centralized here so call
    sites stay symmetric.
    """
    in_image = runtime.in_image_test_file_path()
    if in_image:
        return in_image
    return runtime.translate(os.path.abspath(test_file))


def _pytest_config_args(test_file: str, runtime: Runtime) -> list[str]:
    """Force pytest to use the harness's pytest.ini (sibling to the test
    file), not the target repo's setup.cfg / pyproject.toml.

    Repos often set `filterwarnings = error` or aggressive `addopts` that
    break collection of our independently-written test. SwtBench is opted
    out — there the repo's config is the intended one (the official sweb
    image expects to run pytest the same way the project does).
    """
    if runtime.in_image_test_file_path():
        return []
    host_ini = os.path.join(os.path.dirname(os.path.abspath(test_file)), "pytest.ini")
    if not os.path.isfile(host_ini):
        return []
    return ["-c", runtime.translate(host_ini)]


def _collect_nodeids(test_file, repo_dir, runtime: Runtime):
    """Ask pytest which test functions the file contains.

    pytest's `--collect-only -q` emits nodeids relative to its cwd, which don't
    resolve when passed back to a fresh pytest subprocess. We strip the path
    half and reconstruct with the caller's absolute test_file path (translated
    to the runtime's view).

    Returns a list of full nodeid strings or [] on collection error.
    """
    abs_test_file = os.path.abspath(test_file)
    runtime_test_file = _runtime_test_path(test_file, runtime)
    result = runtime.exec(
        [runtime.python_bin, "-m", "pytest", runtime_test_file,
         *_pytest_config_args(test_file, runtime),
         "--collect-only", "-q", "--no-header"],
        cwd=repo_dir, timeout=30, env=_pytest_env(repo_dir, runtime),
    )
    if result.returncode != 0 and "::" not in result.stdout:
        return []
    nodeids = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if "::" not in line or line.startswith("<") or line.startswith("="):
            continue
        test_part = line.split("::", 1)[1]  # everything after the first :: (handles class::method too)
        if test_part.startswith("test_") or "::test_" in test_part:
            nodeids.append(f"{runtime_test_file}::{test_part}")
    return nodeids


def _run_tests_isolated(test_file, repo_dir, runtime: Runtime,
                        outer_timeout, per_test_timeout):
    """Run each test function in its own pytest subprocess."""
    env = _pytest_env(repo_dir, runtime)
    abs_test_file = os.path.abspath(test_file)

    nodeids = _collect_nodeids(test_file, repo_dir, runtime)
    if not nodeids:
        return {"passed": [], "failed": [], "errors": ["__collection_error__"],
                "failure_details": [],
                "error_details": [{"nodeid": "__collection_error__",
                                   "longrepr": f"pytest found no tests in {os.path.basename(test_file)}"}],
                "test_file_path": abs_test_file,
                "stdout": "", "stderr": "", "returncode": 5}

    # Per-process wall-clock budget: per_test_timeout plus ~3s for pytest startup/teardown.
    sub_timeout = per_test_timeout + 3
    passed, failed, errors, timed_out = [], [], [], []
    failure_details, error_details = [], []
    combined_stdout = []

    for nodeid in nodeids:
        name = nodeid.split("::")[-1]
        report_host = runtime.tempfile_path(suffix=".json")
        report_runtime = runtime.translate(report_host)
        cmd = [runtime.python_bin, "-m", "pytest", nodeid,
               *_pytest_config_args(test_file, runtime),
               "--json-report", f"--json-report-file={report_runtime}",
               f"--timeout={per_test_timeout}",
               "-q", "--tb=short", "--no-header"]
        result = runtime.exec(cmd, cwd=repo_dir, timeout=sub_timeout, env=env)
        if result.timed_out:
            # Subprocess wall-clock kill — test hung past pytest-timeout too.
            # Treat as failure (the code under test is broken / diverges from spec)
            # and record in timed_out so callers can deselect these when measuring coverage.
            if os.path.exists(report_host):
                os.remove(report_host)
            failed.append(name)
            timed_out.append(name)
            failure_details.append({"nodeid": nodeid,
                                    "longrepr": f"hung past {per_test_timeout}s per-test timeout",
                                    "crash": {"timeout": per_test_timeout}})
            combined_stdout.append(f"{nodeid}: TIMEOUT (>{per_test_timeout}s)")
            continue

        combined_stdout.append(result.stdout)
        parsed = _parse_single_report(report_host, nodeid, result)
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
        "test_file_path": abs_test_file,
        "stdout": "\n".join(combined_stdout), "stderr": "", "returncode": 0 if not failed and not errors else 1,
    }


def _parse_single_report(report_file, nodeid, result: RuntimeResult):
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


def _run_tests_batch(test_file, repo_dir, runtime: Runtime, timeout):
    """Original single-subprocess path — faster, used when no per-test timeout is needed."""
    abs_test_file = os.path.abspath(test_file)
    runtime_test_file = _runtime_test_path(test_file, runtime)
    report_host = runtime.tempfile_path(suffix=".json")
    report_runtime = runtime.translate(report_host)
    env = _pytest_env(repo_dir, runtime)

    result = runtime.exec(
        [runtime.python_bin, "-m", "pytest", runtime_test_file,
         *_pytest_config_args(test_file, runtime),
         "--json-report", f"--json-report-file={report_runtime}",
         "-q", "--tb=short", "--no-header"],
        cwd=repo_dir, timeout=timeout, env=env,
    )
    if result.timed_out:
        if os.path.exists(report_host):
            os.remove(report_host)
        return {"passed": [], "failed": [], "errors": ["__timeout__"],
                "failure_details": [], "error_details": [],
                "stdout": "", "stderr": f"Timed out after {timeout}s", "returncode": -1}

    passed, failed, errors, failure_details, error_details = [], [], [], [], []
    if os.path.exists(report_host):
        with open(report_host, encoding="utf-8") as f:
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
        os.remove(report_host)
    else:
        errors.append("__import_or_collection_error__")
        error_details.append({"nodeid": "__import_or_collection_error__", "longrepr": result.stdout})

    if not passed and not failed and not errors and result.returncode != 0:
        errors.append("__collection_error__")
        error_details.append({"nodeid": "__collection_error__", "longrepr": result.stdout})

    return {
        "passed": passed, "failed": failed, "errors": errors,
        "failure_details": failure_details, "error_details": error_details,
        "test_file_path": abs_test_file,
        "stdout": result.stdout, "stderr": result.stderr, "returncode": result.returncode,
    }
