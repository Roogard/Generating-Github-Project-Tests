"""Core pipeline: clone → extract → generate tests → run."""
import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile

from dotenv import load_dotenv

from src.repo_utils import clone_repo, extract_functions, read_readme, extract_test_examples, extract_callees
from src.test_runner import run_tests, measure_coverage
from src.llm import build_config, generate_tests, repair_tests

load_dotenv()

PRESETS = {
    "fast":     {"timeout": 30},
    "default":  {"timeout": 60},
    "thorough": {"timeout": 120},
}


# ── File helpers ──────────────────────────────────────────────────────────────

def _strip_off_target_tests(code: str, target_fn_names: set) -> str:
    """Remove test functions whose bodies never call any of the target functions.

    Uses Python's ast module to walk each test function's body and collect all
    function call names. If none match target_fn_names the test is dropped,
    preventing scope creep where the LLM tests unrelated helpers.
    """
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return code

    def called_names(node) -> set:
        names = set()
        for n in ast.walk(node):
            if isinstance(n, ast.Call):
                if isinstance(n.func, ast.Name):
                    names.add(n.func.id)
                elif isinstance(n.func, ast.Attribute):
                    names.add(n.func.attr)
        return names

    kept = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"):
            if not called_names(node).isdisjoint(target_fn_names):
                kept.append(node)
            # silently drop tests that only call functions outside the target set
        else:
            kept.append(node)

    if len(kept) == len(tree.body):
        return code  # nothing stripped, return original to avoid any reformat churn

    tree.body = kept
    return ast.unparse(tree)


def _write_tests(test_dir: str, tests: dict, repo_dir: str = "", target_fn_names: set | None = None):
    os.makedirs(test_dir, exist_ok=True)
    if repo_dir:
        with open(os.path.join(test_dir, "conftest.py"), "w", encoding="utf-8") as f:
            f.write(f"import sys; sys.path.insert(0, {repr(os.path.abspath(repo_dir))})\n")
    for kind, code in tests.items():
        if code and code.strip():
            if target_fn_names:
                code = _strip_off_target_tests(code, target_fn_names)
            with open(os.path.join(test_dir, f"test_{kind}.py"), "w", encoding="utf-8") as f:
                f.write(code)


def _run_all_tests(test_dir: str, repo_dir: str, timeout: int, per_test_timeout: int | None = None, python_bin: str | None = None) -> tuple[dict, list]:
    outcomes = {}
    all_passed = []
    if not os.path.isdir(test_dir):
        return outcomes, all_passed
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            fpath = os.path.join(test_dir, fname)
            r = run_tests(fpath, repo_dir, timeout=timeout, per_test_timeout=per_test_timeout, python_bin=python_bin)
            p, f_, e = len(r["passed"]), len(r["failed"]), len(r["errors"])
            print(f"  {fname}: {p}p {f_}f {e}e")
            outcomes[fpath] = r
            all_passed.extend(r["passed"])
    return outcomes, all_passed


def _extract_assertion_info(longrepr: str) -> dict:
    """Parse pytest's longrepr string to extract assertion text, expected, and actual values."""
    info = {"assertion": "", "expected": "", "actual": ""}
    if not longrepr:
        return info
    lines = longrepr.splitlines() if isinstance(longrepr, str) else []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("assert ") and not info["assertion"]:
            info["assertion"] = stripped
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("E") and "assert" in stripped:
            expr = re.sub(r'^E\s+', '', stripped)
            m = re.match(r'assert\s+(.+?)\s*==\s*(.+)', expr)
            if m:
                info["actual"] = m.group(1).strip()
                info["expected"] = m.group(2).strip()
            break
    return info


def _parse_failures(outcomes: dict) -> list:
    failures = []
    for path, result in outcomes.items():
        for i, name in enumerate(result.get("failed", [])):
            detail = (result.get("failure_details") or [None] * (i + 1))[i] or {}
            longrepr = detail.get("longrepr", "")
            ainfo = _extract_assertion_info(longrepr)
            failures.append({
                "name": name, "kind": "failure", "path": path,
                "test_file_path": path, "longrepr": longrepr,
                "assertion": ainfo["assertion"],
                "expected": ainfo["expected"],
                "actual": ainfo["actual"],
            })
        for i, name in enumerate(result.get("errors", [])):
            detail = (result.get("error_details") or [None] * (i + 1))[i] or {}
            failures.append({
                "name": name, "kind": "error", "path": path,
                "test_file_path": path, "longrepr": detail.get("longrepr", ""),
                "assertion": "", "expected": "", "actual": "",
            })
    return failures


# Exception types that indicate a broken test (not a genuine bug detection).
# KeyError/AttributeError/NameError/ImportError in a test body mean the test
# made wrong structural assumptions about the API — not that the function is buggy.
_CLEARLY_STRUCTURAL = frozenset([
    'KeyError', 'AttributeError', 'NameError', 'ImportError', 'ModuleNotFoundError',
])
_MAX_REPAIR_ITERS = 3


def _is_structural_failure(failure: dict) -> bool:
    """Return True if this test failed due to a structural error in the test itself.

    Collection/import errors are always structural. Assertion failures are structural
    only when a non-assertion exception (KeyError, AttributeError, etc.) appears in
    the traceback, indicating the test body itself is broken rather than the function
    under test returning a wrong value.
    """
    if failure.get('kind') == 'error':
        return True
    longrepr = failure.get('longrepr', '')
    return any(f'{kw}:' in longrepr for kw in _CLEARLY_STRUCTURAL)


def _repair_pass(outcomes: dict, fns: list, cfg: dict, repo_dir: str, timeout: int, python_bin: str | None = None) -> tuple[dict, list]:
    """One repair attempt: find structurally broken tests, ask LLM to fix them, re-run.

    Handles both collection/import errors AND failed tests whose tracebacks contain
    structural exceptions (KeyError, AttributeError, NameError, ImportError).
    Clean AssertionError failures are left untouched — they may be genuine bug detections.

    Returns updated (outcomes, all_passed) if any repairs were made, otherwise the originals.
    """
    file_structural: dict = {}
    for path, result in outcomes.items():
        broken = []
        # Collection / setup errors
        for i, name in enumerate(result.get("errors", [])):
            detail = (result.get("error_details") or [None] * (i + 1))[i] or {}
            broken.append({"name": name, "kind": "error", "longrepr": detail.get("longrepr", "")})
        # Failed tests with structural exceptions in their tracebacks
        for i, name in enumerate(result.get("failed", [])):
            detail = (result.get("failure_details") or [None] * (i + 1))[i] or {}
            longrepr = detail.get("longrepr", "")
            failure = {"name": name, "kind": "failure", "longrepr": longrepr}
            if _is_structural_failure(failure):
                broken.append(failure)
        if broken:
            file_structural[path] = broken

    if not file_structural:
        return outcomes, [n for r in outcomes.values() for n in r.get("passed", [])]

    repaired_any = False
    for path, broken in file_structural.items():
        try:
            with open(path, encoding="utf-8") as f:
                original_code = f.read()
        except OSError:
            continue
        nerrors = sum(1 for b in broken if b["kind"] == "error")
        nstruct = sum(1 for b in broken if b["kind"] == "failure")
        print(f"  [repair] {os.path.basename(path)}: {nerrors} error(s) + {nstruct} structural failure(s) — asking LLM to fix")
        fixed_code = repair_tests(original_code, broken, fns, cfg)
        if fixed_code != original_code:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            repaired_any = True

    if not repaired_any:
        return outcomes, [n for r in outcomes.values() for n in r.get("passed", [])]

    # Re-run only the repaired files
    new_outcomes = dict(outcomes)
    for path in file_structural:
        r = run_tests(path, repo_dir, timeout=timeout, python_bin=python_bin)
        p, f_, e = len(r["passed"]), len(r["failed"]), len(r["errors"])
        print(f"  [repair] {os.path.basename(path)}: {p}p {f_}f {e}e (after repair)")
        new_outcomes[path] = r
    all_passed = [n for r in new_outcomes.values() for n in r.get("passed", [])]
    return new_outcomes, all_passed


def _run_repair_loop(outcomes: dict, fns: list, cfg: dict, repo_dir: str, timeout: int, python_bin: str | None = None) -> tuple[dict, list, list]:
    """Run _repair_pass up to _MAX_REPAIR_ITERS times, stopping when no structural issues remain or no progress."""
    all_passed: list = []
    repair_log: list = []
    for attempt_num in range(1, _MAX_REPAIR_ITERS + 1):
        prev = sum(len(r.get("errors", [])) for r in outcomes.values()) + sum(
            1 for f in _parse_failures(outcomes) if _is_structural_failure(f))
        if prev == 0:
            break
        outcomes, all_passed = _repair_pass(outcomes, fns, cfg, repo_dir, timeout, python_bin=python_bin)
        after = sum(len(r.get("errors", [])) for r in outcomes.values()) + sum(
            1 for f in _parse_failures(outcomes) if _is_structural_failure(f))
        repair_log.append({
            "attempt_number": attempt_num,
            "attempt_type": "structural_repair",
            "failures_before": prev,
            "failures_after": after,
            "converged": after == 0,
        })
        if after >= prev:
            break
    return outcomes, all_passed, repair_log


_COVERAGE_THRESHOLD = 80.0


def _coverage_pass(test_dir: str, functions: list, cfg: dict, repo_dir: str, timeout: int, use_rag: bool = True, python_bin: str | None = None) -> None:
    """Measure coverage after the initial run and generate a supplemental test file for under-covered functions.

    Writes test_whitebox_cov.py / test_blackbox_cov.py (separate files so the originals are untouched).
    Only fires when at least one target function has coverage below _COVERAGE_THRESHOLD.
    """
    # Measure coverage per function across both test files
    test_files = [
        os.path.join(test_dir, "test_whitebox.py"),
        os.path.join(test_dir, "test_blackbox.py"),
    ]
    fns_needing_coverage = []
    for fn in functions:
        # Combine coverage from both test files for this function
        all_uncovered: set = set()
        best_pct = 0.0
        for tf in test_files:
            if not os.path.isfile(tf):
                continue
            cov = measure_coverage(tf, fn, repo_dir, timeout=timeout, python_bin=python_bin)
            if cov.get("error"):
                continue
            best_pct = max(best_pct, cov["coverage_pct"])
            all_uncovered.update(cov.get("uncovered_lines", []))
        if best_pct < _COVERAGE_THRESHOLD and all_uncovered:
            lines = fn["source"].splitlines()
            start = fn["start_line"]
            hint_lines = []
            for lineno in sorted(all_uncovered)[:20]:  # cap at 20 lines to keep prompt size reasonable
                idx = lineno - start
                src = lines[idx].rstrip() if 0 <= idx < len(lines) else ""
                hint_lines.append(f"  line {lineno}: {src}")
            fn_copy = dict(fn)
            fn_copy["uncovered_hint"] = "\n".join(hint_lines)
            fns_needing_coverage.append(fn_copy)
            print(f"  [coverage] {fn['name']}: {best_pct:.0f}% — requesting supplemental tests ({len(all_uncovered)} uncovered lines)")

    if not fns_needing_coverage:
        return

    supp_tests = generate_tests(fns_needing_coverage, cfg, use_rag=use_rag)
    target_fn_names = {fn["name"] for fn in fns_needing_coverage}
    for kind, code in supp_tests.items():
        if not code or not code.strip():
            continue
        code = _strip_off_target_tests(code, target_fn_names)
        out_path = os.path.join(test_dir, f"test_{kind}_cov.py")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  [coverage] wrote {os.path.basename(out_path)}")


def _setup_run_env(repo_dir: str) -> tuple[str | None, str | None]:
    """Build an ephemeral uv venv for one pipeline run.

    Installs pytest + coverage + the target repo (non-editable) into a fresh venv
    so each run is isolated and the server's own interpreter stays clean.
    Returns (python_bin, venv_dir). The caller must rmtree venv_dir in its finally.
    Returns (None, None) if uv is missing — caller falls back to sys.executable.
    """
    uv = shutil.which("uv")
    if not uv:
        print("  [warn] uv not on PATH; falling back to server interpreter (no per-run isolation)")
        return None, None

    venv_dir = tempfile.mkdtemp(prefix="ggpt-venv-")
    r = subprocess.run([uv, "venv", venv_dir, "--quiet"], capture_output=True)
    if r.returncode != 0:
        print(f"  [warn] uv venv failed: {r.stderr.decode(errors='replace').strip()[:200]}")
        shutil.rmtree(venv_dir, ignore_errors=True)
        return None, None

    py = (os.path.join(venv_dir, "Scripts", "python.exe") if os.name == "nt"
          else os.path.join(venv_dir, "bin", "python"))

    pkgs = ["pytest", "pytest-json-report", "pytest-timeout", "coverage"]
    if (os.path.isfile(os.path.join(repo_dir, "setup.py")) or
            os.path.isfile(os.path.join(repo_dir, "pyproject.toml"))):
        pkgs.append(repo_dir)

    r = subprocess.run([uv, "pip", "install", "--python", py, *pkgs, "--quiet"],
                       capture_output=True)
    if r.returncode != 0:
        print(f"  [warn] deps install failed: {r.stderr.decode(errors='replace').strip()[:300]}")

    return py, venv_dir


#called at end of pipeline run, takes results and saves them in database

def _add_to_db(run_id: int, result: dict) -> None:
    from api.store import session_scope, update_run, save_function_result, finalize_run
    from api.constants import RunStatus
    from datetime import datetime

    with session_scope() as db:
        update_run(db, run_id,
            status=RunStatus.DONE,
            output_dir=result["output_dir"],
            finished_at=datetime.utcnow(),
        )
        for fn_result in result.get("results", [result]):
            save_function_result(db, run_id, fn_result)
        finalize_run(db, run_id)


#general pipeline for a single function

def run_pipeline(
    repo_url: str,
    fn_name: str,
    *,
    run_id: int | None = None,
    description: str = "",
    provider: str = "deepseek",
    model: str | None = None,
    preset: str = "default",
    output_dir: str = "eval_output",
    install_deps: bool = True,
    api_key: str | None = None,
    use_rag: bool = True,
) -> dict:
    """Clone repo, generate tests for one function, run them.

    Returns: {status, error, output_dir, test_dir, fn_name, fn_file, failures, test_outcomes}
    """
    cfg = build_config(provider, model, api_key=api_key)
    timeout = PRESETS.get(preset, PRESETS["default"])["timeout"]
    run_dir = os.path.join(output_dir, repo_url.rstrip("/").split("/")[-1].replace(".git", ""))
    os.makedirs(run_dir, exist_ok=True)

    tmp = tempfile.mkdtemp()
    venv_dir: str | None = None
    python_bin: str | None = None
    try:
        print(f"\nCloning {repo_url}...")
        clone_repo(repo_url, tmp)

        if install_deps:
            print("Setting up ephemeral run env...")
            python_bin, venv_dir = _setup_run_env(tmp)

        print(f"Extracting '{fn_name}'...")
        all_functions = extract_functions(tmp)
        matches = [f for f in all_functions if f["name"] == fn_name]
        if not matches:
            all_names = sorted({f["name"] for f in all_functions})
            return {"status": "error", "error": f"'{fn_name}' not found. Available: {all_names[:20]}",
                    "output_dir": run_dir, "test_dir": "", "fn_name": fn_name, "fn_file": "",
                    "failures": [], "test_outcomes": {}}
        fn = matches[0]
        if description:
            fn["description"] = description
        fn["spec"] = read_readme(tmp)
        fn["test_examples"] = extract_test_examples(tmp, {fn_name}).get(fn_name, [])
        fn["callees"] = extract_callees(fn["source"], all_functions)
        print(f"  {fn['file_path']} lines {fn['start_line']}-{fn['end_line']}")
        print(f"  LLM: {provider}/{cfg['model']}  preset={preset}  spec: {len(fn['spec'])} chars")

        test_dir = os.path.join(run_dir, "tests")
        tests = generate_tests([fn], cfg, use_rag=use_rag)
        _write_tests(test_dir, tests, tmp, target_fn_names={fn["name"]})
        outcomes, _ = _run_all_tests(test_dir, tmp, timeout, python_bin=python_bin)
        outcomes, _, repair_log = _run_repair_loop(outcomes, [fn], cfg, tmp, timeout, python_bin=python_bin)

        # Measure coverage per test file
        coverage_map: dict = {}
        for fname in sorted(os.listdir(test_dir)):
            if fname.startswith("test_") and fname.endswith(".py"):
                fpath = os.path.join(test_dir, fname)
                cov = measure_coverage(fpath, fn, tmp, timeout=timeout, python_bin=python_bin)
                if not cov.get("error"):
                    coverage_map[fpath] = {
                        "coverage_pct": cov.get("coverage_pct"),
                        "covered_lines": cov.get("covered_lines", []),
                        "uncovered_lines": cov.get("uncovered_lines", []),
                    }

        failures = _parse_failures(outcomes)

        result = {
            "status": "done", "error": None,
            "output_dir": run_dir, "test_dir": test_dir,
            "fn_name": fn["name"], "fn_file": fn["file_path"],
            "fn_source": fn.get("source", ""),
            "failures": failures, "test_outcomes": outcomes,
            "coverage": coverage_map,
            "repair_attempts": repair_log,
        }
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    except Exception as e:
        result = {"status": "error", "error": str(e), "output_dir": run_dir,
                  "test_dir": "", "fn_name": fn_name, "fn_file": "",
                  "failures": [], "test_outcomes": {}}
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if venv_dir:
            shutil.rmtree(venv_dir, ignore_errors=True)


def _write_project_run_scripts(out_dir: str, project_name: str) -> None:
    yml = f"""\
name: Generated Tests — {project_name}
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Install project
        run: pip install -e . || pip install -r requirements.txt || true
      - name: Run generated tests
        run: pytest . -v --tb=short
"""
    with open(os.path.join(out_dir, "run_tests.yml"), "w", encoding="utf-8") as f:
        f.write(yml)
    with open(os.path.join(out_dir, "run_tests.sh"), "w", encoding="utf-8") as f:
        f.write("#!/bin/bash\nset -e\npytest . -v --tb=short\n")


def run_project_for_api(
    repo_url: str,
    *,
    run_id: int | None = None,
    provider: str = "deepseek",
    model: str | None = None,
    preset: str = "default",
    output_dir: str = "eval_output",
    install_deps: bool = True,
    api_key: str | None = None,
    limit: int | None = None,
    progress_callback=None,
    use_rag: bool = True,
) -> dict:
    """Clone repo once, generate+run tests for every function, return aggregated results.

    progress_callback(current: int, total: int) is called after each function completes.
    """
    from typing import Callable  # noqa: F401 — inline to avoid circular at import time

    cfg = build_config(provider, model, api_key=api_key)
    timeout = PRESETS.get(preset, PRESETS["default"])["timeout"]
    project_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    run_dir = os.path.join(output_dir, project_name)
    os.makedirs(run_dir, exist_ok=True)

    tmp = tempfile.mkdtemp()
    venv_dir: str | None = None
    python_bin: str | None = None
    try:
        print(f"\nCloning {repo_url}...")
        clone_repo(repo_url, tmp)

        if install_deps:
            print("Setting up ephemeral run env...")
            python_bin, venv_dir = _setup_run_env(tmp)

        spec = read_readme(tmp)

        print("Extracting functions...")
        all_fns = extract_functions(tmp)
        functions = [
            f for f in all_fns
            if not os.path.basename(f["file_path"]).startswith("test_")
            and "/test" not in f["file_path"].replace("\\", "/")
            and not (f["name"].startswith("__") and f["name"].endswith("__"))
        ]
        if limit:
            functions = functions[:limit]

        total = len(functions)
        print(f"  {total} functions found")
        if progress_callback:
            progress_callback(0, total)

        # Project-level conftest
        with open(os.path.join(run_dir, "conftest.py"), "w", encoding="utf-8") as fh:
            fh.write(f"import sys\nsys.path.insert(0, {repr(os.path.abspath(tmp))})\n")

        fn_names = {fn["name"] for fn in functions}
        test_examples = extract_test_examples(tmp, fn_names)
        for fn in functions:
            fn["spec"] = spec
            fn["test_examples"] = test_examples.get(fn["name"], [])
            fn["callees"] = extract_callees(fn["source"], all_fns)

        results = []
        for i, fn in enumerate(functions):
            fn_label = f"{fn['file_path']}::{fn['name']}"
            print(f"\n[{i + 1}/{total}] {fn_label}")
            fn_run_dir = os.path.join(run_dir, fn["name"])
            os.makedirs(fn_run_dir, exist_ok=True)
            test_dir = os.path.join(fn_run_dir, "tests")

            try:
                tests = generate_tests([fn], cfg, use_rag=use_rag)
                _write_tests(test_dir, tests, tmp, target_fn_names={fn["name"]})
                outcomes, _ = _run_all_tests(test_dir, tmp, timeout, python_bin=python_bin)
                outcomes, _, repair_log = _run_repair_loop(outcomes, [fn], cfg, tmp, timeout, python_bin=python_bin)

                coverage_map: dict = {}
                if os.path.isdir(test_dir):
                    for fname in sorted(os.listdir(test_dir)):
                        if fname.startswith("test_") and fname.endswith(".py"):
                            fpath = os.path.join(test_dir, fname)
                            cov = measure_coverage(fpath, fn, tmp, timeout=timeout, python_bin=python_bin)
                            if not cov.get("error"):
                                coverage_map[fpath] = {
                                    "coverage_pct": cov.get("coverage_pct"),
                                    "covered_lines": cov.get("covered_lines", []),
                                    "uncovered_lines": cov.get("uncovered_lines", []),
                                }

                failures = _parse_failures(outcomes)

                results.append({
                    "status": "done", "error": None,
                    "output_dir": fn_run_dir, "test_dir": test_dir,
                    "fn_name": fn["name"], "fn_file": fn["file_path"],
                    "fn_source": fn.get("source", ""),
                    "failures": failures, "test_outcomes": outcomes,
                    "coverage": coverage_map,
                    "repair_attempts": repair_log,
                })
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({
                    "status": "error", "error": str(e),
                    "output_dir": fn_run_dir,
                    "test_dir": test_dir if os.path.isdir(test_dir) else "",
                    "fn_name": fn["name"], "fn_file": fn["file_path"],
                    "fn_source": fn.get("source", ""),
                    "failures": [], "test_outcomes": {},
                    "coverage": {},
                    "repair_attempts": [],
                })

            if progress_callback:
                progress_callback(i + 1, total)

        _write_project_run_scripts(run_dir, project_name)

        ok = sum(1 for r in results if r["status"] == "done")
        print(f"\nDone. {ok}/{total} functions → {run_dir}")
        result = {
            "status": "done",
            "output_dir": run_dir,
            "project_name": project_name,
            "results": results,
            "total_functions": total,
        }
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    except Exception as e:
        result = {
            "status": "error",
            "error": str(e),
            "output_dir": run_dir,
            "project_name": project_name,
            "results": [],
            "total_functions": 0,
        }
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if venv_dir:
            shutil.rmtree(venv_dir, ignore_errors=True)


def run_for_repo(
    functions: list,
    output_dir: str,
    repo_dir: str,
    cfg: dict,
    timeout: int = 60,
    per_test_timeout: int | None = None,
    coverage_pass: bool = True,
    use_rag: bool = True,
    python_bin: str | None = None,
) -> list:
    """Generate and run tests for all functions from a pre-cloned repo.

    All functions are passed as a single context to the LLM.
    Returns flat list of all failures.
    """
    os.makedirs(output_dir, exist_ok=True)
    test_dir = os.path.join(output_dir, "tests")
    tests = generate_tests(functions, cfg, use_rag=use_rag)
    target_fn_names = {fn["name"] for fn in functions}
    _write_tests(test_dir, tests, repo_dir, target_fn_names=target_fn_names)
    outcomes, all_passed = _run_all_tests(test_dir, repo_dir, timeout, per_test_timeout, python_bin=python_bin)
    outcomes, all_passed, _ = _run_repair_loop(outcomes, functions, cfg, repo_dir, timeout, python_bin=python_bin)

    if coverage_pass:
        _coverage_pass(test_dir, functions, cfg, repo_dir, timeout, use_rag=use_rag, python_bin=python_bin)
        # Re-run to pick up any coverage-supplemental test files written above
        outcomes, all_passed = _run_all_tests(test_dir, repo_dir, timeout, per_test_timeout, python_bin=python_bin)
    failures = _parse_failures(outcomes)
    total_passed = sum(len(r["passed"]) for r in outcomes.values())
    total_errored = sum(len(r["errors"]) for r in outcomes.values())
    total_run = sum(len(r["passed"]) + len(r["failed"]) + len(r["errors"]) for r in outcomes.values())
    return {
        "failures": failures,
        "passed_names": all_passed,
        "tests_run": total_run,
        "tests_passed": total_passed,
        "tests_errored": total_errored,
    }
