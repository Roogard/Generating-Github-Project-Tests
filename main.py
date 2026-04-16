"""
Entry point for GHTest.

Whole-project mode (primary deliverable):
  python main.py --project <repo_url_or_path> [--spec spec.md] [options]
  Generates test_<fn>_whitebox.py + test_<fn>_blackbox.py for every function,
  plus conftest.py and run_tests.yml (GitHub Actions).

Single-function mode:
  python main.py <repo_url> <function_name> [options]

BugsInPy batch mode (SWT-bench evaluation):
  python main.py --batch
  Configure BUGSINPY_PROJECTS and BUGS_PER_PROJECT below.

Re-analyze results:
  python main.py --analyze eval_output/bugsinpy_<timestamp>/results.json

Options:
  --provider    deepseek (default), anthropic, openai, ollama
  --model       Override model name
  --preset      fast | default (default) | thorough
  --output-dir  Where to write output (default: eval_output)
  --spec        Spec file for --project mode (defaults to repo README)
  --desc        Plain-English description (single-function mode)
  --no-install  Skip pip-installing the repo
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

from dotenv import load_dotenv

from repo_utils import clone_repo, clone_repo_at_commit, extract_functions, read_readme, get_issue_description, extract_test_examples, extract_callees
from pipeline import run_pipeline, run_for_repo, PRESETS
from llm import build_config, generate_tests

load_dotenv()

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# ── BugsInPy settings (edit these to run the benchmark) ──────────────────────
BUGSINPY_PROJECTS: list[str] = ["tqdm", "cookiecutter"]
BUGS_PER_PROJECT = 5
BUGSINPY_PATH: str | None = None   # local BugsInPy clone path; None = auto-clone
INSTALL_DEPS = True
OUTPUT_DIR = "./eval_output"


# ── Bug report helpers ────────────────────────────────────────────────────────

def print_bug_report(failures: list, repo_url: str = ""):
    if not failures:
        print("\nNo potential bugs detected. All generated tests passed.")
        return
    fn_set = {f["name"] for f in failures}
    print(f"\n{'=' * 64}")
    print("BUG REPORT" + (f"  —  {repo_url}" if repo_url else ""))
    print(f"{'=' * 64}")
    print(f"Summary: {len(failures)} issue(s) across {len(fn_set)} function(s)\n")
    by_fn: dict = {}
    for f in failures:
        by_fn.setdefault(f["name"], []).append(f)
    for fn_name, fn_failures in sorted(by_fn.items()):
        print(f"  {fn_name}")
        for f in fn_failures:
            label = "FAIL" if f["kind"] == "failure" else "ERROR"
            print(f"    [{label}] {f['name']}")
            longrepr = f.get("longrepr", "")
            if longrepr:
                first = longrepr.strip().splitlines()[0]
                print(f"      {first}")
        print()
    print(f"{'=' * 64}")
    print(f"Total: {len(failures)} issue(s)\n")


# ── Single-function CLI ───────────────────────────────────────────────────────

def _run_single(args):
    result = run_pipeline(
        repo_url=args.repo_url,
        fn_name=args.function_name,
        description=args.desc,
        provider=args.provider,
        model=args.model,
        preset=args.preset,
        output_dir=args.output_dir,
        install_deps=not args.no_install,
    )
    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        sys.exit(1)
    print_bug_report(result["failures"], args.repo_url)
    print(f"\nDone. Output: {result['output_dir']}")


# ── Whole-project mode ────────────────────────────────────────────────────────

def _fn_test_dir(base_out_dir, file_path):
    """Mirror source directory structure under the output dir."""
    module_dir = os.path.dirname(file_path.replace("\\", "/"))
    return os.path.join(base_out_dir, module_dir) if module_dir else base_out_dir


def _write_fn_tests(test_dir, fn_name, tests):
    """Write per-function whitebox and blackbox test files."""
    os.makedirs(test_dir, exist_ok=True)
    for kind, code in tests.items():
        if code and code.strip():
            path = os.path.join(test_dir, f"test_{fn_name}_{kind}.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)


def _write_project_conftest(out_dir, repo_dir):
    path = os.path.join(out_dir, "conftest.py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"import sys\nsys.path.insert(0, {repr(os.path.abspath(repo_dir))})\n")


def _write_github_actions(out_dir, project_name):
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
        run: pytest test_output/{project_name}/ -v --tb=short
"""
    with open(os.path.join(out_dir, "run_tests.yml"), "w", encoding="utf-8") as f:
        f.write(yml)


def _run_project(args):
    cfg = build_config(args.provider, args.model)
    is_url = args.project.startswith(("http://", "https://", "git@"))
    tmp = None
    try:
        if is_url:
            tmp = tempfile.mkdtemp()
            print(f"Cloning {args.project}...")
            clone_repo(args.project, tmp)
            repo_dir = tmp
            project_name = args.project.rstrip("/").split("/")[-1].replace(".git", "")
        else:
            repo_dir = os.path.abspath(args.project)
            project_name = os.path.basename(repo_dir)

        # Spec: explicit file > repo README
        if args.spec:
            with open(args.spec, encoding="utf-8", errors="replace") as fh:
                spec = fh.read()
        else:
            spec = read_readme(repo_dir)

        print(f"Extracting functions from '{project_name}'...")
        all_fns = extract_functions(repo_dir)
        # Skip existing test files — don't generate tests for tests
        functions = [
            f for f in all_fns
            if not os.path.basename(f["file_path"]).startswith("test_")
            and "/test" not in f["file_path"].replace("\\", "/")
        ]
        skipped = len(all_fns) - len(functions)
        print(f"  {len(functions)} functions found  ({skipped} skipped in test files)")

        out_dir = os.path.join(args.output_dir, project_name)
        os.makedirs(out_dir, exist_ok=True)
        _write_project_conftest(out_dir, repo_dir)

        results = []
        for i, fn in enumerate(functions, 1):
            fn["spec"] = spec
            label = f"{fn['file_path']}::{fn['name']}"
            print(f"\n[{i}/{len(functions)}] {label}")
            try:
                tests = generate_tests([fn], cfg)
                fn_dir = _fn_test_dir(out_dir, fn["file_path"])
                _write_fn_tests(fn_dir, fn["name"], tests)
                results.append({"function": fn["name"], "file": fn["file_path"], "status": "ok"})
            except Exception as e:
                print(f"  ERROR: {e}")
                results.append({"function": fn["name"], "file": fn["file_path"],
                                "status": "error", "error": str(e)})

        _write_github_actions(out_dir, project_name)

        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"\n{'=' * 55}")
        print(f"Done.  {ok}/{len(results)} functions  →  {out_dir}")
        print(f"Automation file: {os.path.join(out_dir, 'run_tests.yml')}")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


# ── BugsInPy batch mode ───────────────────────────────────────────────────────

def _run_batch():
    provider = os.environ.get("LLM_PROVIDER", "deepseek")
    cfg = build_config(provider, os.environ.get("LLM_MODEL"))
    timeout = PRESETS.get("default")["timeout"]

    bugsinpy_tmp = None
    bugsinpy_dir = BUGSINPY_PATH
    if not bugsinpy_dir:
        bugsinpy_tmp = tempfile.mkdtemp()
        print("Cloning BugsInPy metadata...")
        clone_repo("https://github.com/soarsmu/BugsInPy", bugsinpy_tmp)
        bugsinpy_dir = bugsinpy_tmp

    try:
        bugs = _load_bugs(bugsinpy_dir, BUGSINPY_PROJECTS, BUGS_PER_PROJECT)
        print(f"Loaded {len(bugs)} bug(s)  LLM: {cfg['provider']}/{cfg['model']}\n")
        run_dir = os.path.join(OUTPUT_DIR, f"bugsinpy_{datetime.now().strftime('%d-%m-%Y_%H-%M')}")
        os.makedirs(run_dir, exist_ok=True)
        results = [_run_one_bug(bug, run_dir, cfg, timeout) for bug in bugs]
        results_path = os.path.join(run_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        _print_bugsinpy_summary(results, cfg)
        print(f"\nResults: {results_path}")
    finally:
        if bugsinpy_tmp:
            shutil.rmtree(bugsinpy_tmp, ignore_errors=True)


def _run_one_bug(bug, run_dir, cfg, timeout):
    instance_id = f"{bug['project']}-{bug['bug_id']}"
    base = {"instance_id": instance_id, "project": bug["project"], "bug_id": bug["bug_id"]}
    instance_output = os.path.join(run_dir, instance_id)
    print(f"\n{'─' * 55}\n  {instance_id}")

    if not bug["bug_patch"]:
        print("  No patch — skipping")
        return {**base, "status": "no_patch"}

    tmp = tempfile.mkdtemp()
    try:
        print(f"  Cloning @ {bug['buggy_commit'][:8]}...")
        clone_repo_at_commit(bug["github_url"], tmp, bug["buggy_commit"])
        if INSTALL_DEPS:
            _install_bug_deps(bug["requirements_path"], tmp)
        all_functions = extract_functions(tmp)
        functions = _functions_from_patch(bug["bug_patch"], tmp, all_functions=all_functions)
        if not functions:
            print("  No target functions found in patch")
            return {**base, "status": "no_targets"}
        spec = get_issue_description(tmp, bug["github_url"])
        if spec:
            spec_src = "issue"
        else:
            spec = read_readme(tmp)
            spec_src = "readme"
            print("  [spec] no issue ref in commit — falling back to README")
        fn_names = {fn["name"] for fn in functions}
        test_examples = extract_test_examples(tmp, fn_names)
        for fn in functions:
            fn["spec"] = spec
            fn["test_examples"] = test_examples.get(fn["name"], [])
            fn["callees"] = extract_callees(fn["source"], all_functions)
        print(f"  {len(functions)} target(s): {[f['name'] for f in functions]}  spec: {len(spec)} chars ({spec_src})")
        t0 = time.time()
        run_result = run_for_repo(functions, instance_output, tmp, cfg, timeout)
        elapsed = round(time.time() - t0, 1)
        failures = run_result["failures"]
        initial_passed = set(run_result["passed_names"])
        tests_run = run_result["tests_run"]
        tests_passed_buggy = run_result["tests_passed"]
        tests_errored = run_result["tests_errored"]
        tests_failed_buggy = len([f for f in failures if f["kind"] == "failure"])
        detected = tests_failed_buggy > 0

        # SWT-bench oracle: apply ground-truth patch and compute F→P, F→F, P→F transitions
        patch_applied = False
        f_to_p = f_to_f = p_to_f = 0
        if bug["bug_patch"] and detected:
            # Write as binary to avoid CRLF conversion on Windows breaking the patch
            patch_tmp = tempfile.NamedTemporaryFile(suffix=".patch", delete=False, mode="wb")
            patch_tmp.write(bug["bug_patch"].encode("utf-8"))
            patch_tmp.close()
            r = subprocess.run(
                ["git", "apply", "--ignore-whitespace", patch_tmp.name],
                cwd=tmp, capture_output=True,
            )
            os.unlink(patch_tmp.name)
            if r.returncode != 0:
                print(f"  [oracle] git apply failed: {r.stderr.decode(errors='replace').strip()[:200]}")
            else:
                patch_applied = True
                from test_runner import run_tests as _run_tests
                # Compare by function name only (strip path prefix) to avoid rootdir-relative path mismatches
                failed_names = {f["name"].split("::")[-1] for f in failures if f["kind"] == "failure"}
                test_dir = os.path.join(instance_output, "tests")
                for tfile in ("test_whitebox.py", "test_blackbox.py"):
                    tpath = os.path.join(test_dir, tfile)
                    if os.path.isfile(tpath):
                        res = _run_tests(tpath, tmp, timeout)
                        fixed_passed = {n.split("::")[-1] for n in res["passed"]}
                        fixed_failed = {n.split("::")[-1] for n in res["failed"]}
                        f_to_p += len(fixed_passed & failed_names)    # F→P: correctly catches bug
                        f_to_f += len(fixed_failed & failed_names)    # F→F: spurious (false positive)
                        p_to_f += len(fixed_failed & initial_passed)  # P→F: regression introduced

        # S (success): at least one F→P, no spurious F→F, no regressions P→F
        resolved = patch_applied and f_to_p > 0 and f_to_f == 0 and p_to_f == 0
        p_to_p = (tests_passed_buggy - p_to_f) if patch_applied else None

        print(f"  → tests={tests_run}  detected={detected}  F→P={f_to_p}  F→F={f_to_f}  P→F={p_to_f}  resolved={resolved}  {elapsed}s")
        return {
            **base,
            "status": "ok",
            # Test counts on buggy code
            "tests_run":     tests_run,
            "tests_passed":  tests_passed_buggy,
            "tests_failed":  tests_failed_buggy,
            "tests_errored": tests_errored,
            # SWT-bench transitions (oracle run after applying ground-truth fix)
            "patch_applied": patch_applied,   # W — applicability
            "f2p":           f_to_p,          # F→P count
            "f2f":           f_to_f,          # F→F count (spurious)
            "p2f":           p_to_f,          # P→F count (regressions)
            "p2p":           p_to_p,          # P→P count (approx)
            # Summary
            "detected":      detected,
            "resolved":      resolved,        # S — primary SWT-bench metric
            "elapsed_seconds": elapsed,
        }
    except Exception as e:
        print(f"  ERROR: {e}")
        return {**base, "status": "error", "error": str(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _parse_info_file(path):
    result = {}
    with open(path, encoding="utf-8") as f:
        for line in f:
            m = re.match(r'^(\w+)="([^"]*)"', line.strip())
            if m:
                result[m.group(1)] = m.group(2)
    return result


def _load_bugs(bugsinpy_dir, projects, limit_per_project):
    bugs = []
    projects_dir = os.path.join(bugsinpy_dir, "projects")
    for project in sorted(os.listdir(projects_dir)):
        if projects and project not in projects:
            continue
        info_path = os.path.join(projects_dir, project, "project.info")
        github_url = _parse_info_file(info_path).get("github_url", "") if os.path.isfile(info_path) else ""
        if not github_url:
            continue
        bugs_dir = os.path.join(projects_dir, project, "bugs")
        if not os.path.isdir(bugs_dir):
            continue
        count = 0
        for bug_id in sorted(os.listdir(bugs_dir), key=lambda x: int(x) if x.isdigit() else 0):
            bug_dir = os.path.join(bugs_dir, bug_id)
            bug_info_path = os.path.join(bug_dir, "bug.info")
            if not os.path.isfile(bug_info_path):
                continue
            buggy_commit = _parse_info_file(bug_info_path).get("buggy_commit_id", "")
            if not buggy_commit:
                continue
            patch_path = os.path.join(bug_dir, "bug_patch.txt")
            req_path = os.path.join(bug_dir, "requirements.txt")
            bug_patch = open(patch_path, encoding="utf-8").read() if os.path.isfile(patch_path) else ""
            bugs.append({
                "project": project, "bug_id": bug_id, "github_url": github_url,
                "buggy_commit": buggy_commit, "bug_patch": bug_patch,
                "requirements_path": req_path if os.path.isfile(req_path) else None,
            })
            count += 1
            if limit_per_project > 0 and count >= limit_per_project:
                break
    return bugs


def _functions_from_patch(patch_text, repo_path, all_functions=None):
    files: dict = {}
    current_file = None
    for line in patch_text.splitlines():
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            current_file = m.group(1)
            files.setdefault(current_file, [])
            continue
        m = re.match(r"^@@ -(\d+),?\d* \+(\d+),?\d* @@\s*(.*)", line)
        if m and current_file:
            nm = re.match(r"def\s+(\w+)", m.group(3).strip())
            files[current_file].append((int(m.group(1)), nm.group(1) if nm else None))
    targets, seen = [], set()
    for fn in (all_functions if all_functions is not None else extract_functions(repo_path)):
        fn_rel = fn["file_path"].replace("\\", "/")
        for patch_file, hunks in files.items():
            patch_norm = patch_file.replace("\\", "/")
            if fn_rel != patch_norm and not fn_rel.endswith("/" + patch_norm):
                continue
            for old_start, fn_hint in hunks:
                if (fn_hint and fn["name"] == fn_hint) or fn["start_line"] <= old_start <= fn["end_line"]:
                    span = (fn["file_path"], fn["start_line"], fn["end_line"])
                    if span not in seen:
                        seen.add(span)
                        targets.append(fn)
                    break
            break
    return targets


_pip_bootstrapped = False

def _ensure_pip():
    """Bootstrap pip via ensurepip if python -m pip is missing."""
    global _pip_bootstrapped
    if _pip_bootstrapped:
        return
    r = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True)
    if r.returncode != 0:
        import ensurepip
        ensurepip.bootstrap(upgrade=True)
        print("  [info] pip bootstrapped via ensurepip")
    _pip_bootstrapped = True


_CONSTRAINTS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "constraints.txt")


def _pip_install(args: list) -> bool:
    """Install packages using python -m pip (bootstrapping pip first if needed)."""
    _ensure_pip()
    constraint_args = ["--constraint", _CONSTRAINTS] if os.path.isfile(_CONSTRAINTS) else []
    r = subprocess.run(
        [sys.executable, "-m", "pip", "install"] + constraint_args + args,
        check=False, capture_output=True,
    )
    if r.returncode != 0:
        print(f"  [warn] install failed: {r.stderr.decode(errors='replace').strip()[:300]}")
        return False
    return True


def _install_bug_deps(requirements_path, repo_dir):
    # Install the repo package + all its transitive dependencies
    has_setup = os.path.isfile(os.path.join(repo_dir, "setup.py"))
    has_pyproject = os.path.isfile(os.path.join(repo_dir, "pyproject.toml"))
    if has_setup or has_pyproject:
        _pip_install(["-e", repo_dir, "-q", "--no-warn-script-location"])

    # Also install the repo's own requirements.txt and the BugsInPy requirements.
    # Filter pkg-resources==0.0.0 — a Debian/Ubuntu pip freeze artefact that doesn't exist on other systems.
    repo_req = os.path.join(repo_dir, "requirements.txt")
    for req in filter(os.path.isfile, [repo_req, requirements_path]):
        with open(req, encoding="utf-8", errors="replace") as fh:
            lines = [l for l in fh if not l.strip().lower().startswith("pkg-resources")]
        if not lines:
            continue
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False, encoding="utf-8") as tmp:
            tmp.writelines(lines)
            tmp_path = tmp.name
        try:
            _pip_install(["-r", tmp_path, "-q", "--no-warn-script-location"])
        finally:
            os.unlink(tmp_path)


def _print_bugsinpy_summary(results, cfg=None):
    W = 68
    ok = [r for r in results if r.get("status") == "ok"]
    n = len(ok)

    resolved   = [r for r in ok if r.get("resolved")]
    detected   = [r for r in ok if r.get("detected")]
    applicable = [r for r in ok if r.get("patch_applied")]
    total_f2p  = sum(r.get("f2p", 0) for r in ok)
    total_f2f  = sum(r.get("f2f", 0) for r in ok)
    total_p2f  = sum(r.get("p2f", 0) for r in ok)
    total_p2p  = sum(r.get("p2p") or 0 for r in ok)
    avg_tests  = (sum(r.get("tests_run", 0) for r in ok) / n) if n else 0
    avg_time   = (sum(r.get("elapsed_seconds", 0) for r in ok) / n) if n else 0

    model_str = ""
    if cfg:
        model_str = f"{cfg.get('provider','?')}/{cfg.get('model','?')}"

    def pct(num, den):
        return f"{num/den:.1%}" if den else "—"

    print("\n" + "=" * W)
    print("SWT-BENCH RESULTS")
    print("=" * W)
    if model_str:
        print(f"  Model : {model_str:<40s}  Evaluated: {n} bugs")
    else:
        print(f"  Evaluated: {n} bugs")

    print()
    print("  OVERALL")
    print(f"    Success (S)       {len(resolved):>3} / {n}  ({pct(len(resolved), n)})   ← F→P>0, no F→F, no P→F")
    print(f"    Detected          {len(detected):>3} / {n}  ({pct(len(detected), n)})   ← ≥1 test fails on buggy code")
    print(f"    Applicability (W) {len(applicable):>3} / {n}  ({pct(len(applicable), n)})   ← patch applied cleanly")
    print(f"    Avg tests/bug     {avg_tests:.1f}")
    print(f"    Avg elapsed       {avg_time:.1f}s")

    print()
    print("  OUTCOME TRANSITIONS  (totals across all bugs)")
    print(f"    F→P  {total_f2p:>5}   correctly reproduced failures")
    print(f"    F→F  {total_f2f:>5}   spurious / false positives")
    print(f"    P→F  {total_p2f:>5}   regressions introduced")
    print(f"    P→P  {total_p2p:>5}   stable passing tests")

    # Per-project breakdown
    by_project: dict = {}
    for r in ok:
        by_project.setdefault(r["project"], []).append(r)
    print()
    print("  PER-PROJECT")
    hdr = f"  {'Project':<16}  Bugs  S      W      F→P  F→F  P→F  Tests  Time"
    print(hdr)
    print("  " + "-" * (len(hdr) - 2))
    for project, proj_results in sorted(by_project.items()):
        pr = proj_results
        nb = len(pr)
        ns = sum(1 for r in pr if r.get("resolved"))
        nw = sum(1 for r in pr if r.get("patch_applied"))
        pf2p = sum(r.get("f2p", 0) for r in pr)
        pf2f = sum(r.get("f2f", 0) for r in pr)
        pp2f = sum(r.get("p2f", 0) for r in pr)
        pt   = sum(r.get("tests_run", 0) for r in pr) / nb if nb else 0
        pe   = sum(r.get("elapsed_seconds", 0) for r in pr) / nb if nb else 0
        print(f"  {project:<16}  {nb:>4}  {ns}/{nb:<4}  {nw}/{nb:<4}  "
              f"{pf2p:>3}  {pf2f:>3}  {pp2f:>3}  {pt:>5.1f}  {pe:.1f}s")

    # Per-instance table
    print()
    print("  PER-INSTANCE")
    ihdr = f"  {'Instance':<22}  Tests  Failed  F→P  F→F  P→F  S    W    Time"
    print(ihdr)
    print("  " + "-" * (len(ihdr) - 2))
    for r in ok:
        s_str = "YES" if r.get("resolved") else "NO "
        w_str = "YES" if r.get("patch_applied") else "NO "
        print(f"  {r['instance_id']:<22}  "
              f"{r.get('tests_run',0):>5}  "
              f"{r.get('tests_failed',0):>6}  "
              f"{r.get('f2p',0):>3}  "
              f"{r.get('f2f',0):>3}  "
              f"{r.get('p2f',0):>3}  "
              f"{s_str}  {w_str}  "
              f"{r.get('elapsed_seconds',0):.1f}s")

    print("=" * W)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    p = argparse.ArgumentParser(description="Generate and run tests for a GitHub repo function.")
    p.add_argument("repo_url", nargs="?", help="GitHub repo URL (omit for --batch mode)")
    p.add_argument("function_name", nargs="?", help="Function name to test")
    p.add_argument("--provider",   default="deepseek")
    p.add_argument("--model",      default=None)
    p.add_argument("--preset",     default="default", choices=["fast", "default", "thorough"])
    p.add_argument("--output-dir", default=OUTPUT_DIR)
    p.add_argument("--desc",       default="")
    p.add_argument("--no-install", action="store_true")
    p.add_argument("--batch",      action="store_true", help="Run BugsInPy batch evaluation")
    p.add_argument("--analyze",    metavar="RESULTS_JSON", help="Re-analyze an existing results.json")
    p.add_argument("--project",    metavar="REPO_URL_OR_PATH", help="Generate tests for every function in a project")
    p.add_argument("--spec",       metavar="SPEC_FILE", default=None, help="Spec file for --project (README.md / context.json). Defaults to repo README.")
    args = p.parse_args()

    if args.analyze:
        with open(args.analyze, encoding="utf-8") as fh:
            results = json.load(fh)
        _print_bugsinpy_summary(results)
        return
    elif args.project:
        _run_project(args)
    elif args.batch:
        _run_batch()
    elif args.repo_url and args.function_name:
        _run_single(args)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
