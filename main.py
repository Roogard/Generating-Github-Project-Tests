"""
Batch driver for BugsInPy evaluation and freeform repo lists.

This is the legacy entry point kept for the benchmark workflow. For the
single-function CLI see `run.py`; the core pipeline lives in `src/pipeline.py`.
"""
import os
import re
import json
import shutil
import subprocess
import sys
import tempfile
import time
from datetime import datetime

from dotenv import load_dotenv

from src.extractor import clone_repo, clone_repo_at_commit, extract_functions
from src.writer import write_meta
from src.reporter import print_bug_report, write_bug_report
from src.pipeline import run_for_functions, repo_name_from_url, _build_config

# ── Settings ──────────────────────────────────────────────────────────────────

load_dotenv()
# Provider/model picked from env; override by editing these two lines
config = _build_config(
    provider=os.environ.get("LLM_PROVIDER", "deepseek"),
    model=os.environ.get("LLM_MODEL"),
)

# Regular repos — add URLs, leave empty to skip
REPOS: list[str] = []
LIMIT = 3
OUTPUT_DIR = "./eval_output"

# BugsInPy — leave BUGSINPY_PROJECTS empty to skip
BUGSINPY_PROJECTS = ["black", "tqdm", "thefuck", "cookiecutter", "tornado"]
BUGS_PER_PROJECT = 5
BUGSINPY_PATH = None    # local BugsInPy clone, if already on disk
INSTALL_DEPS = False    # pip install per-bug deps into current env


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    for repo in REPOS:
        output_dir = os.path.join(OUTPUT_DIR, repo_name_from_url(repo))
        write_meta(repo, output_dir)

        tmp = tempfile.mkdtemp()
        try:
            print(f"\nCloning {repo}...")
            clone_repo(repo, tmp)
            print("Extracting functions...")
            functions = extract_functions(tmp)[:LIMIT]
            print(f"Using {len(functions)} function(s)")
            if not functions:
                continue
            _, failures, _ = run_for_functions(functions, output_dir, tmp, config)
            print_bug_report(failures, repo)
            write_bug_report(failures, repo, output_dir)
            print(f"\nDone. Output: {output_dir}")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    if BUGSINPY_PROJECTS:
        _run_bugsinpy()


def _run_bugsinpy():
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

        run_dir = os.path.join(OUTPUT_DIR, f"bugsinpy_{datetime.now().strftime('%d-%m-%Y_%H-%M')}")
        os.makedirs(run_dir, exist_ok=True)
        all_results = [_run_one_bug(bug, run_dir) for bug in bugs]

        results_path = os.path.join(run_dir, "results.json")
        with open(results_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2)

        _print_bugsinpy_summary(all_results)
        print(f"\nResults: {results_path}")
    finally:
        if bugsinpy_tmp:
            shutil.rmtree(bugsinpy_tmp, ignore_errors=True)


def _run_one_bug(bug, run_dir):
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
            print("  Installing deps...")
            _install_deps(bug["requirements_path"], tmp)

        functions = _functions_from_patch(bug["bug_patch"], tmp)
        if not functions:
            print("  No target functions found in patch")
            return {**base, "status": "no_targets"}

        print(f"  {len(functions)} target(s): {[f['name'] for f in functions]}")
        write_meta(bug["github_url"], instance_output)

        t0 = time.time()
        test_outcomes, failures, fix_attempted = run_for_functions(functions, instance_output, tmp, config)
        elapsed = round(time.time() - t0, 1)

        passed  = sum(len(r["passed"])  for r in test_outcomes.values())
        failed  = sum(len(r["failed"])  for r in test_outcomes.values())
        errored = sum(len(r["errors"])  for r in test_outcomes.values())
        converged = fix_attempted and not failures
        print(f"  → {passed}p/{failed}f/{errored}e  fix={'✓' if converged else ('~' if fix_attempted else '-')}  {elapsed}s")
        return {**base, "status": "ok", "tests_passed": passed, "tests_failed": failed,
                "tests_errored": errored, "fix_attempted": fix_attempted,
                "converged": converged, "elapsed_seconds": elapsed}

    except Exception as e:
        print(f"  ERROR: {e}")
        return {**base, "status": "error", "error": str(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


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
        github_url = _parse_info_file(
            os.path.join(projects_dir, project, "project.info")
        ).get("github_url", "") if os.path.isfile(
            os.path.join(projects_dir, project, "project.info")
        ) else ""
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
            requirements_path = os.path.join(bug_dir, "requirements.txt")
            bug_patch = ""
            if os.path.isfile(patch_path):
                with open(patch_path, encoding="utf-8") as pf:
                    bug_patch = pf.read()
            bugs.append({
                "project": project, "bug_id": bug_id, "github_url": github_url,
                "buggy_commit": buggy_commit, "bug_patch": bug_patch,
                "requirements_path": requirements_path if os.path.isfile(requirements_path) else None,
            })
            count += 1
            if limit_per_project > 0 and count >= limit_per_project:
                break
    return bugs


def _functions_from_patch(patch_text, repo_path):
    files: dict[str, list] = {}
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
    by_project: dict[str, list] = {}
    for r in results:
        by_project.setdefault(r["project"], []).append(r)
    for project, proj_results in sorted(by_project.items()):
        proj_ok = [r for r in proj_results if r.get("status") == "ok"]
        print(f"  {project:20s}  tested={len(proj_ok)}  "
              f"detected={sum(1 for r in proj_ok if r.get('fix_attempted'))}  "
              f"converged={sum(1 for r in proj_ok if r.get('converged'))}")


if __name__ == "__main__":
    main()
