import os
import ast
import json
import re
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

from dotenv import load_dotenv

from src.config import load_config
from src.extractor import clone_repo, clone_repo_at_commit, extract_functions
from src.agents import call_agent, call_fix_agent, call_oracle_revision_agent, strip_code_fences, _extract_code
from src.runner import run_single_test
from src.writer import write_meta, write_function, write_generated_tests, generate_automation, write_fixed_function, write_fix_artifacts, replace_function_in_repo
from src.reporter import parse_failures, print_bug_report, write_bug_report

# ── Settings ──────────────────────────────────────────────────────────────────

load_dotenv()
config = load_config()

# Regular repos — add/remove URLs freely, leave empty to skip
REPOS = [
    # "https://github.com/keon/algorithms",
]
LIMIT = 3           # max functions per repo
OUTPUT_DIR = "./eval_output"

# BugsInPy — leave BUGSINPY_PROJECTS empty to skip
BUGSINPY_PROJECTS = ["black", "tqdm", "thefuck", "cookiecutter", "tornado"]
BUGS_PER_PROJECT = 5
BUGSINPY_PATH = None    # set to a local BugsInPy clone to skip re-downloading
INSTALL_DEPS = False    # pip install deps per bug (modifies your environment)

# ── Shared helpers ────────────────────────────────────────────────────────────

def _is_valid_fix(code, fn_name):
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


def _run_fn_tests(fn_key, output_dir, repo_dir):
    outcomes = {}
    test_dir = os.path.join(output_dir, "generated_tests", fn_key)
    if not os.path.isdir(test_dir):
        return outcomes
    for fname in sorted(os.listdir(test_dir)):
        if fname.startswith("test_") and fname.endswith(".py"):
            outcomes[(fn_key, fname)] = run_single_test(
                os.path.join(test_dir, fname), repo_dir, timeout=config["timeouts"]["test"]
            )
    return outcomes


def _one_shot_fix(fn, fn_key, test_outcomes, repo_dir, output_dir, idx):
    fn_failures = [f for f in parse_failures(test_outcomes) if f["function"] == fn_key]
    if not fn_failures or all(f["kind"] == "error" for f in fn_failures):
        return test_outcomes, False

    print(f"  fixing ({len(fn_failures)} failure(s))...", end=" ", flush=True)
    fix = call_fix_agent(fn, fn_failures, config)
    if not fix["code"] or not fix["code"].strip():
        print("no output")
        return test_outcomes, False

    fixed_code = strip_code_fences(fix["code"])
    if not _is_valid_fix(fixed_code, fn["name"]):
        print("invalid fix, skipping")
        return test_outcomes, False

    write_fix_artifacts(fn, output_dir, idx, 0,
                        diagnosis=fix["diagnosis"],
                        diagnosis_context=fix["diagnosis_context"],
                        fix_context=fix["fix_context"])
    fn["end_line"] = replace_function_in_repo(fn, fixed_code, repo_dir)
    fn["source"] = fixed_code
    write_fixed_function(fn, fixed_code, output_dir, idx, iteration=0)

    outcomes = _run_fn_tests(fn_key, output_dir, repo_dir)
    remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

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
            revised_code = _extract_code(revised_raw)
            try:
                ast.parse(revised_code)
                with open(test_path, "w", encoding="utf-8") as fh:
                    fh.write(revised_code)
            except SyntaxError as e:
                print(f"oracle revision invalid ({e}), skipping")
        outcomes = _run_fn_tests(fn_key, output_dir, repo_dir)
        remaining = [f for f in parse_failures(outcomes) if f["function"] == fn_key and f["kind"] == "failure"]

    print("converged" if not remaining else f"{len(remaining)} failure(s) remain")
    return outcomes, True


def run_for_functions(functions, output_dir, repo_dir):
    """Generate tests, run them, attempt fixes. Returns (test_outcomes, failures, fix_attempted)."""
    # Generate
    print("\nGenerating tests...")
    for i, fn in enumerate(functions):
        print(f"\n[{i+1}/{len(functions)}] {fn['name']}")
        write_function(fn, output_dir, i)
        generated = {}
        for test_type in ["whitebox", "blackbox"]:
            print(f"  {test_type}...", end=" ", flush=True)
            code = call_agent(test_type, fn, config)
            if code and code.strip():
                generated[test_type] = code
                print(f"ok ({len(code)} chars)")
            else:
                print("empty")
        write_generated_tests(fn, generated, output_dir, i)

    generate_automation(output_dir, repo_dir)

    # Run
    print("\nRunning tests...")
    test_outcomes = {}
    for fn_dir in sorted(os.listdir(os.path.join(output_dir, "generated_tests"))):
        fn_path = os.path.join(output_dir, "generated_tests", fn_dir)
        if not os.path.isdir(fn_path):
            continue
        for fname in sorted(os.listdir(fn_path)):
            if fname.startswith("test_") and fname.endswith(".py"):
                test_file = os.path.join(fn_path, fname)
                print(f"  {fn_dir}/{fname}...", end=" ", flush=True)
                result = run_single_test(test_file, repo_dir, timeout=config["timeouts"]["test"])
                p, f_count, e = len(result["passed"]), len(result["failed"]), len(result["errors"])
                print(f"{p} passed, {f_count} failed, {e} errors")
                test_outcomes[(fn_dir, fname)] = result

    # Fix
    failures = parse_failures(test_outcomes)
    any_fix_attempted = False
    if failures:
        print("\nFix pass...")
        fn_by_key = {f"{fn['name']}_{i}": (fn, i) for i, fn in enumerate(functions)}
        outcomes_by_fn = {}
        for (fn_dir, fname), result in test_outcomes.items():
            outcomes_by_fn.setdefault(fn_dir, {})[(fn_dir, fname)] = result
        for fn_key, fn_outcomes in outcomes_by_fn.items():
            if fn_key not in fn_by_key:
                continue
            fn, idx = fn_by_key[fn_key]
            if not any(f["function"] == fn_key for f in failures):
                continue
            print(f"  {fn_key}:")
            updated, attempted = _one_shot_fix(fn, fn_key, fn_outcomes, repo_dir, output_dir, idx)
            if attempted:
                any_fix_attempted = True
            test_outcomes.update(updated)

    failures = parse_failures(test_outcomes)
    return test_outcomes, failures, any_fix_attempted


# ── BugsInPy helpers ─────────────────────────────────────────────────────────

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
        project_info_path = os.path.join(projects_dir, project, "project.info")
        if not os.path.isfile(project_info_path):
            continue
        github_url = _parse_info_file(project_info_path).get("github_url", "")
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
            bug_info = _parse_info_file(bug_info_path)
            buggy_commit = bug_info.get("buggy_commit_id", "")
            if not buggy_commit:
                continue
            patch_path = os.path.join(bug_dir, "bug_patch.txt")
            requirements_path = os.path.join(bug_dir, "requirements.txt")
            if os.path.isfile(patch_path):
                with open(patch_path, encoding="utf-8") as pf:
                    bug_patch = pf.read()
            else:
                bug_patch = ""
            bugs.append({
                "project": project,
                "bug_id": bug_id,
                "github_url": github_url,
                "buggy_commit": buggy_commit,
                "bug_patch": bug_patch,
                "requirements_path": requirements_path if os.path.isfile(requirements_path) else None,
            })
            count += 1
            if limit_per_project > 0 and count >= limit_per_project:
                break
    return bugs


def _functions_from_patch(patch_text, repo_path):
    files = {}
    current_file = None
    for line in patch_text.splitlines():
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            current_file = m.group(1)
            files.setdefault(current_file, [])
            continue
        m = re.match(r"^@@ -(\d+),?\d* \+(\d+),?\d* @@\s*(.*)", line)
        if m and current_file:
            fn_hint = None
            nm = re.match(r"def\s+(\w+)", m.group(3).strip())
            if nm:
                fn_hint = nm.group(1)
            files[current_file].append((int(m.group(1)), fn_hint))

    targets, seen = [], set()
    for fn in extract_functions(repo_path):
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


def _install_deps(requirements_path, repo_dir):
    if requirements_path and os.path.isfile(requirements_path):
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-r", requirements_path, "-q", "--no-warn-script-location"],
            check=False, capture_output=True,
        )
        if r.returncode != 0:
            print(f"  [warn] pip install -r failed: {r.stderr.decode(errors='replace').strip()[:200]}")
    if os.path.isfile(os.path.join(repo_dir, "setup.py")) or os.path.isfile(os.path.join(repo_dir, "pyproject.toml")):
        r = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", repo_dir, "-q", "--no-warn-script-location"],
            check=False, capture_output=True,
        )
        if r.returncode != 0:
            print(f"  [warn] pip install -e . failed: {r.stderr.decode(errors='replace').strip()[:200]}")


def _print_bugsinpy_summary(results):
    print("\n" + "=" * 55)
    print("BUGSINPY SUMMARY")
    print("=" * 55)
    ok = [r for r in results if r.get("status") == "ok"]
    detected = [r for r in ok if r.get("fix_attempted")]
    converged = [r for r in ok if r.get("converged")]
    print(f"  Tested:          {len(ok)}")
    print(f"  Bugs detected:   {len(detected)}/{len(ok)}  ({len(detected)/len(ok):.0%})" if ok else "  Bugs detected:   —")
    print(f"  Fixes converged: {len(converged)}/{len(detected)}  ({len(converged)/len(detected):.0%})" if detected else "  Fixes converged: —")
    print()
    by_project = {}
    for r in results:
        by_project.setdefault(r["project"], []).append(r)
    for project, proj_results in sorted(by_project.items()):
        proj_ok = [r for r in proj_results if r.get("status") == "ok"]
        print(f"  {project:20s}  tested={len(proj_ok)}  detected={sum(1 for r in proj_ok if r.get('fix_attempted'))}  converged={sum(1 for r in proj_ok if r.get('converged'))}")


# ── Regular repos ─────────────────────────────────────────────────────────────

for repo in REPOS:
    repo_name = repo.rstrip("/").split("/")[-1].replace(".git", "")
    output_dir = os.path.join(OUTPUT_DIR, repo_name)
    write_meta(repo, output_dir)

    tmp = tempfile.mkdtemp()
    print(f"\nCloning {repo}...")
    clone_repo(repo, tmp)

    print("Extracting functions...")
    functions = extract_functions(tmp)[:LIMIT]
    print(f"Using {len(functions)} function(s)")

    if not functions:
        shutil.rmtree(tmp, ignore_errors=True)
        continue

    _, failures, _ = run_for_functions(functions, output_dir, tmp)
    print_bug_report(failures, repo)
    write_bug_report(failures, repo, output_dir)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone. Output: {output_dir}")


# ── BugsInPy ──────────────────────────────────────────────────────────────────

if BUGSINPY_PROJECTS:
    bugsinpy_tmp = None
    bugsinpy_dir = BUGSINPY_PATH
    if not bugsinpy_dir:
        bugsinpy_tmp = tempfile.mkdtemp()
        print("Cloning BugsInPy metadata...")
        clone_repo("https://github.com/soarsmu/BugsInPy", bugsinpy_tmp)
        bugsinpy_dir = bugsinpy_tmp

    try:
        bugs = _load_bugs(bugsinpy_dir, BUGSINPY_PROJECTS, BUGS_PER_PROJECT)
        print(f"Loaded {len(bugs)} bug(s)  LLM: {config['llm']['provider']}/{config['llm']['model']}\n")

        timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
        run_dir = os.path.join(OUTPUT_DIR, f"bugsinpy_{timestamp}")
        os.makedirs(run_dir, exist_ok=True)

        all_results = []
        for bug in bugs:
            instance_id = f"{bug['project']}-{bug['bug_id']}"
            instance_output = os.path.join(run_dir, instance_id)
            print(f"\n{'─' * 55}\n  {instance_id}")

            if not bug["bug_patch"]:
                print("  No patch — skipping")
                all_results.append({"instance_id": instance_id, "status": "no_patch", "project": bug["project"], "bug_id": bug["bug_id"]})
                continue

            tmp = tempfile.mkdtemp()
            try:
                print(f"  Cloning @ {bug['buggy_commit'][:8]}...")
                clone_repo_at_commit(bug["github_url"], tmp, bug["buggy_commit"])

                if INSTALL_DEPS:
                    print("  Installing deps...")
                    _install_deps(bug["requirements_path"], tmp)

                functions = _functions_from_patch(bug["bug_patch"], tmp)
                if not functions:
                    print("  No target functions found in patch")
                    all_results.append({"instance_id": instance_id, "status": "no_targets", "project": bug["project"], "bug_id": bug["bug_id"]})
                    continue

                print(f"  {len(functions)} target(s): {[f['name'] for f in functions]}")
                write_meta(bug["github_url"], instance_output)

                t0 = time.time()
                test_outcomes, failures, fix_attempted = run_for_functions(functions, instance_output, tmp)
                elapsed = round(time.time() - t0, 1)

                passed = sum(len(r["passed"]) for r in test_outcomes.values())
                failed = sum(len(r["failed"]) for r in test_outcomes.values())
                errored = sum(len(r["errors"]) for r in test_outcomes.values())
                converged = fix_attempted and not failures
                print(f"  → {passed}p/{failed}f/{errored}e  fix={'✓' if converged else ('~' if fix_attempted else '-')}  {elapsed}s")

                all_results.append({
                    "instance_id": instance_id, "project": bug["project"], "bug_id": bug["bug_id"],
                    "status": "ok", "tests_passed": passed, "tests_failed": failed, "tests_errored": errored,
                    "fix_attempted": fix_attempted, "converged": converged, "elapsed_seconds": elapsed,
                })

            except Exception as e:
                print(f"  ERROR: {e}")
                all_results.append({"instance_id": instance_id, "status": "error", "error": str(e), "project": bug["project"], "bug_id": bug["bug_id"]})
            finally:
                shutil.rmtree(tmp, ignore_errors=True)

        results_path = os.path.join(run_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        _print_bugsinpy_summary(all_results)
        print(f"\nResults: {results_path}")

    finally:
        if bugsinpy_tmp:
            shutil.rmtree(bugsinpy_tmp, ignore_errors=True)
