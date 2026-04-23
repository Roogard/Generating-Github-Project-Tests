"""Pipeline orchestration: clone → extract → run agent per function → persist.

Each function gets its own TestGenEnv and an agentic loop. The loop lives in
`src/agent/`. This module handles repo setup, extraction, venv, and DB hand-off.
"""
import os
import shutil
import subprocess
import tempfile

from dotenv import load_dotenv

from src.agent import TestGenEnv, run_agent
from src.llm import build_config
from src.repo_utils import clone_repo, extract_functions, read_readme, extract_test_examples, extract_callees

load_dotenv()

PRESETS = {
    "fast":     {"timeout": 60,  "max_turns": 2, "per_test_timeout": 2},
    "default":  {"timeout": 180, "max_turns": 4, "per_test_timeout": 5},
    "thorough": {"timeout": 300, "max_turns": 8, "per_test_timeout": 10},
}


# Path fragments that mark a file as a "reference" / "correct" implementation,
# not the primary code under test. Applied when a function name matches in
# multiple files — QuixBugs is the motivating case (python_programs/ vs
# correct_python_programs/). Only kicks in on ambiguity; a single match is
# always returned as-is.
_REFERENCE_PATH_HINTS = ("correct_", "/correct/", "/reference/", "/solution", "/solutions/", "/fixed/")


def _select_primary_match(matches: list[dict]) -> dict:
    """Given multiple functions with the same name, pick the primary (non-reference) one.

    Falls back to the first match if every candidate looks like a reference impl.
    """
    if len(matches) == 1:
        return matches[0]

    def is_reference(fn: dict) -> bool:
        path = ("/" + fn.get("file_path", "").replace("\\", "/")).lower()
        return any(hint in path for hint in _REFERENCE_PATH_HINTS)

    primary = [f for f in matches if not is_reference(f)]
    return primary[0] if primary else matches[0]


# ── venv setup ────────────────────────────────────────────────────────────────

def _setup_run_env(repo_dir: str) -> tuple[str | None, str | None]:
    """Build an ephemeral uv venv for one pipeline run.

    Returns (python_bin, venv_dir). Caller must rmtree venv_dir in its finally.
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


# ── DB persistence ────────────────────────────────────────────────────────────

def _add_to_db(run_id: int, result: dict) -> None:
    from api.store import session_scope, update_run, save_function_result, finalize_run
    from api.constants import RunStatus
    from datetime import datetime

    with session_scope() as db:
        update_run(db, run_id,
            status=RunStatus.DONE if result.get("status") == "done" else RunStatus.ERROR,
            output_dir=result.get("output_dir"),
            error_message=result.get("error"),
            finished_at=datetime.utcnow(),
        )
        for fn_result in result.get("results", [result]):
            if fn_result.get("fn_name"):  # skip top-level error shells with no fn
                save_function_result(db, run_id, fn_result)
        finalize_run(db, run_id)


# ── Core: run the agent on one function ───────────────────────────────────────

def run_agent_on_function(
    fn: dict,
    cfg: dict,
    repo_dir: str,
    out_dir: str,
    *,
    python_bin: str | None = None,
    timeout: int = 60,
    max_turns: int = 4,
    per_test_timeout: int | None = None,
    benchmark_context: dict | None = None,
) -> dict:
    """Run the agentic loop for one function. Returns a persist-ready dict."""
    os.makedirs(out_dir, exist_ok=True)
    test_dir = os.path.join(out_dir, "tests")
    env = TestGenEnv(
        fn=fn,
        repo_dir=repo_dir,
        test_dir=test_dir,
        python_bin=python_bin,
        timeout=timeout,
        max_turns=max_turns,
        per_test_timeout=per_test_timeout,
        benchmark_context=benchmark_context,
    )
    try:
        agent_result = run_agent(env, cfg)
    except Exception as e:
        print(f"  ERROR in agent loop: {type(e).__name__}: {e}")
        return {
            "status": "error", "error": str(e),
            "output_dir": out_dir, "test_dir": test_dir,
            "fn_name": fn["name"], "fn_file": fn.get("file_path", ""),
            "fn_source": fn.get("source", ""),
            "test_code": "",
            "tests_passed": 0, "tests_failed": 0, "tests_run": 0, "tests_errored": 0,
            "coverage_pct": None, "coverage": {}, "metrics": {},
            "turns_used": 0, "finish_reason": None, "history": [],
        }

    return {
        "status": "done", "error": None,
        "output_dir": out_dir, "test_dir": test_dir,
        "fn_name": fn["name"], "fn_file": fn.get("file_path", ""),
        "fn_source": fn.get("source", ""),
        "test_code": agent_result.get("test_code", ""),
        "test_file_path": agent_result.get("test_file_path", ""),
        "tests_passed": agent_result.get("tests_passed", 0),
        "tests_failed": agent_result.get("tests_failed", 0),
        "tests_errored": agent_result.get("tests_errored", 0),
        "tests_run": agent_result.get("tests_run", 0),
        "coverage_pct": agent_result.get("coverage_pct"),
        "coverage": agent_result.get("coverage", {}),
        "metrics": agent_result.get("metrics", {}),
        "turns_used": agent_result.get("turns_used", 0),
        "finish_reason": agent_result.get("finish_reason"),
        "history": agent_result.get("history", []),
    }


# ── API entry: single function ────────────────────────────────────────────────

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
    use_rag: bool = True,  # kept for request-shape compatibility; agent uses it via search_similar_tests tool
) -> dict:
    """Clone a repo, run the agent on one function, persist results."""
    del use_rag  # Agent handles retrieval itself via search_similar_tests.
    cfg = build_config(provider, model, api_key=api_key)
    preset_cfg = PRESETS.get(preset, PRESETS["default"])
    timeout = preset_cfg["timeout"]
    max_turns = preset_cfg["max_turns"]
    per_test_timeout = preset_cfg.get("per_test_timeout")

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
            result = {"status": "error", "error": f"'{fn_name}' not found. Available: {all_names[:20]}",
                      "output_dir": run_dir}
            if run_id is not None:
                _add_to_db(run_id, result)
            return result

        fn = _select_primary_match(matches)
        if len(matches) > 1:
            dropped = [m["file_path"] for m in matches if m is not fn]
            print(f"  [extract] {len(matches)} files define '{fn_name}'; chose {fn['file_path']} (skipped {dropped})")
        if description:
            fn["description"] = description
        fn["spec"] = read_readme(tmp)
        fn["test_examples"] = extract_test_examples(tmp, {fn_name}).get(fn_name, [])
        fn["callees"] = extract_callees(fn["source"], all_functions)
        print(f"  {fn['file_path']} lines {fn['start_line']}-{fn['end_line']}")
        print(f"  LLM: {provider}/{cfg['model']}  preset={preset}  turns<={max_turns}")

        fn_result = run_agent_on_function(
            fn, cfg, tmp, run_dir,
            python_bin=python_bin, timeout=timeout, max_turns=max_turns,
            per_test_timeout=per_test_timeout,
        )
        if run_id is not None:
            _add_to_db(run_id, fn_result)
        return fn_result
    except Exception as e:
        result = {"status": "error", "error": str(e), "output_dir": run_dir,
                  "fn_name": fn_name, "fn_file": ""}
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if venv_dir:
            shutil.rmtree(venv_dir, ignore_errors=True)


# ── API entry: whole project ─────────────────────────────────────────────────

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
    """Clone once, run the agent on every function, aggregate results."""
    del use_rag  # Agent handles retrieval itself.
    cfg = build_config(provider, model, api_key=api_key)
    preset_cfg = PRESETS.get(preset, PRESETS["default"])
    timeout = preset_cfg["timeout"]
    max_turns = preset_cfg["max_turns"]
    per_test_timeout = preset_cfg.get("per_test_timeout")

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
            fn_result = run_agent_on_function(
                fn, cfg, tmp, fn_run_dir,
                python_bin=python_bin, timeout=timeout, max_turns=max_turns,
                per_test_timeout=per_test_timeout,
            )
            results.append(fn_result)
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
            "status": "error", "error": str(e),
            "output_dir": run_dir, "project_name": project_name,
            "results": [], "total_functions": 0,
        }
        if run_id is not None:
            _add_to_db(run_id, result)
        return result
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        if venv_dir:
            shutil.rmtree(venv_dir, ignore_errors=True)
