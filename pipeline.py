"""Core pipeline: clone → extract → generate tests → run."""
import ast
import os
import shutil
import subprocess
import sys
import tempfile

from dotenv import load_dotenv

from repo_utils import clone_repo, extract_functions, read_readme, extract_test_examples, extract_callees
from test_runner import run_tests, measure_coverage
from llm import build_config, generate_tests, repair_tests

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


def _run_all_tests(test_dir: str, repo_dir: str, timeout: int) -> tuple[dict, list]:
    outcomes = {}
    all_passed = []
    if not os.path.isdir(test_dir):
        return outcomes, all_passed
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            fpath = os.path.join(test_dir, fname)
            r = run_tests(fpath, repo_dir, timeout=timeout)
            p, f_, e = len(r["passed"]), len(r["failed"]), len(r["errors"])
            print(f"  {fname}: {p}p {f_}f {e}e")
            outcomes[fpath] = r
            all_passed.extend(r["passed"])
    return outcomes, all_passed


def _parse_failures(outcomes: dict) -> list:
    failures = []
    for path, result in outcomes.items():
        for i, name in enumerate(result.get("failed", [])):
            detail = (result.get("failure_details") or [None] * (i + 1))[i] or {}
            failures.append({"name": name, "kind": "failure", "path": path, "longrepr": detail.get("longrepr", "")})
        for i, name in enumerate(result.get("errors", [])):
            detail = (result.get("error_details") or [None] * (i + 1))[i] or {}
            failures.append({"name": name, "kind": "error", "path": path, "longrepr": detail.get("longrepr", "")})
    return failures


def _repair_pass(outcomes: dict, fns: list, cfg: dict, repo_dir: str, timeout: int) -> tuple[dict, list]:
    """One repair attempt: find tests with setup errors, ask LLM to fix them, re-run.

    Returns updated (outcomes, all_passed) if any repairs were made, otherwise the originals.
    """
    # Collect only setup/collection-phase errors (pytest outcome != passed/failed).
    # We deliberately exclude "failed" tests even when their traceback looks like a
    # setup error — a buggy function can raise TypeError/AttributeError at call time,
    # and "fixing" those would silently destroy legitimate bug detections.
    file_errors: dict = {}
    for path, result in outcomes.items():
        errors = []
        for i, name in enumerate(result.get("errors", [])):
            detail = (result.get("error_details") or [None] * (i + 1))[i] or {}
            longrepr = detail.get("longrepr", "")
            errors.append({"name": name, "longrepr": longrepr})
        if errors:
            file_errors[path] = errors

    if not file_errors:
        return outcomes, [n for r in outcomes.values() for n in r.get("passed", [])]

    repaired_any = False
    for path, errors in file_errors.items():
        try:
            with open(path, encoding="utf-8") as f:
                original_code = f.read()
        except OSError:
            continue
        print(f"  [repair] {os.path.basename(path)}: {len(errors)} setup error(s) — asking LLM to fix")
        fixed_code = repair_tests(original_code, errors, fns, cfg)
        if fixed_code != original_code:
            with open(path, "w", encoding="utf-8") as f:
                f.write(fixed_code)
            repaired_any = True

    if not repaired_any:
        return outcomes, [n for r in outcomes.values() for n in r.get("passed", [])]

    # Re-run only the repaired files
    new_outcomes = dict(outcomes)
    all_passed = []
    for path in file_errors:
        r = run_tests(path, repo_dir, timeout=timeout)
        p, f_, e = len(r["passed"]), len(r["failed"]), len(r["errors"])
        print(f"  [repair] {os.path.basename(path)}: {p}p {f_}f {e}e (after repair)")
        new_outcomes[path] = r
    for r in new_outcomes.values():
        all_passed.extend(r.get("passed", []))
    return new_outcomes, all_passed


_COVERAGE_THRESHOLD = 80.0


def _coverage_pass(test_dir: str, functions: list, cfg: dict, repo_dir: str, timeout: int) -> None:
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
            cov = measure_coverage(tf, fn, repo_dir, timeout=timeout)
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

    supp_tests = generate_tests(fns_needing_coverage, cfg)
    target_fn_names = {fn["name"] for fn in fns_needing_coverage}
    for kind, code in supp_tests.items():
        if not code or not code.strip():
            continue
        code = _strip_off_target_tests(code, target_fn_names)
        out_path = os.path.join(test_dir, f"test_{kind}_cov.py")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(code)
        print(f"  [coverage] wrote {os.path.basename(out_path)}")


def _install_deps(repo_dir: str):
    if not (os.path.isfile(os.path.join(repo_dir, "setup.py")) or
            os.path.isfile(os.path.join(repo_dir, "pyproject.toml"))):
        return
    uv = shutil.which("uv")
    cmd = ([uv, "pip", "install", "-e", repo_dir, "--quiet"] if uv
           else [sys.executable, "-m", "pip", "install", "-e", repo_dir, "-q", "--no-warn-script-location"])
    r = subprocess.run(cmd, check=False, capture_output=True)
    if r.returncode != 0:
        print(f"  [warn] install failed: {r.stderr.decode(errors='replace').strip()[:200]}")


# ── Public API ────────────────────────────────────────────────────────────────

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
    """Clone repo, generate tests for one function, run them.

    Returns: {status, error, output_dir, test_dir, fn_name, fn_file, failures, test_outcomes}
    """
    cfg = build_config(provider, model, api_key=api_key)
    timeout = PRESETS.get(preset, PRESETS["default"])["timeout"]
    run_dir = os.path.join(output_dir, repo_url.rstrip("/").split("/")[-1].replace(".git", ""))
    os.makedirs(run_dir, exist_ok=True)

    tmp = tempfile.mkdtemp()
    try:
        print(f"\nCloning {repo_url}...")
        clone_repo(repo_url, tmp)

        if install_deps:
            print("Installing deps...")
            _install_deps(tmp)

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
        tests = generate_tests([fn], cfg)
        _write_tests(test_dir, tests, tmp, target_fn_names={fn["name"]})
        outcomes, _ = _run_all_tests(test_dir, tmp, timeout)
        outcomes, _ = _repair_pass(outcomes, [fn], cfg, tmp, timeout)
        failures = _parse_failures(outcomes)
        return {
            "status": "done", "error": None,
            "output_dir": run_dir, "test_dir": test_dir,
            "fn_name": fn["name"], "fn_file": fn["file_path"],
            "failures": failures, "test_outcomes": outcomes,
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "output_dir": run_dir,
                "test_dir": "", "fn_name": fn_name, "fn_file": "",
                "failures": [], "test_outcomes": {}}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run_for_repo(
    functions: list,
    output_dir: str,
    repo_dir: str,
    cfg: dict,
    timeout: int = 60,
) -> list:
    """Generate and run tests for all functions from a pre-cloned repo.

    All functions are passed as a single context to the LLM.
    Returns flat list of all failures.
    """
    os.makedirs(output_dir, exist_ok=True)
    test_dir = os.path.join(output_dir, "tests")
    tests = generate_tests(functions, cfg)
    target_fn_names = {fn["name"] for fn in functions}
    _write_tests(test_dir, tests, repo_dir, target_fn_names=target_fn_names)
    outcomes, all_passed = _run_all_tests(test_dir, repo_dir, timeout)
    outcomes, all_passed = _repair_pass(outcomes, functions, cfg, repo_dir, timeout)
    _coverage_pass(test_dir, functions, cfg, repo_dir, timeout)
    # Re-run to pick up any coverage-supplemental test files written above
    outcomes, all_passed = _run_all_tests(test_dir, repo_dir, timeout)
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
