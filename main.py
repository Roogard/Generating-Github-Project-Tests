"""
Entry point for GHTest.

Whole-project mode (primary deliverable):
  python main.py --project <repo_url_or_path> [--spec spec.md] [options]
  Generates test_<fn>_whitebox.py + test_<fn>_blackbox.py for every function,
  plus conftest.py, run_tests.yml, and run_tests.sh.

Single-function mode:
  python main.py <repo_url> <function_name> [options]

Multi-function mode (batch multiple functions in one LLM context):
  python main.py <repo_url> [fn1 fn2 ...] [--limit N] [options]

Options:
  --provider    deepseek (default), anthropic, openai, ollama
  --model       Override model name
  --preset      fast | default (default) | thorough
  --output-dir  Where to write output (default: eval_output)
  --spec        Spec file for --project mode
  --desc        Plain-English description (single-function mode)
  --no-install  Skip pip-installing the repo
  --fix-pass    Run diagnose + code-gen agents after tests
  --limit N     Limit to first N functions
"""
import argparse
import os
import shutil
import sys
import tempfile

from dotenv import load_dotenv

from src.repo_utils import clone_repo, extract_functions, read_readme, extract_test_examples, extract_callees
from src.pipeline import run_pipeline, run_for_repo, PRESETS, _install_deps
from src.llm import build_config, generate_tests

load_dotenv()

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

OUTPUT_DIR = "./eval_output"


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
        fix_pass=args.fix_pass,
    )
    if result["status"] == "error":
        print(f"\nERROR: {result['error']}")
        sys.exit(1)
    print_bug_report(result["failures"], args.repo_url)
    print(f"\nDone. Output: {result['output_dir']}")


def _run_multi(args):
    cfg = build_config(args.provider, args.model)
    timeout = PRESETS.get(args.preset, PRESETS["default"])["timeout"]
    run_dir = os.path.join(args.output_dir, args.repo_url.rstrip("/").split("/")[-1].replace(".git", ""))
    requested = set(getattr(args, "function_names", []))

    tmp = tempfile.mkdtemp()
    try:
        print(f"\nCloning {args.repo_url}...")
        clone_repo(args.repo_url, tmp)

        if not args.no_install:
            print("Installing deps...")
            _install_deps(tmp)

        all_functions = extract_functions(tmp)
        all_functions = [
            f for f in all_functions
            if not os.path.basename(f["file_path"]).startswith("test_")
            and os.path.basename(f["file_path"]) != "conftest.py"
            and "/test" not in f["file_path"].replace("\\", "/")
            and not (f["name"].startswith("__") and f["name"].endswith("__"))
        ]

        if requested:
            functions = [f for f in all_functions if f["name"] in requested]
            not_found = requested - {f["name"] for f in functions}
            if not_found:
                print(f"Warning: not found: {sorted(not_found)}")
        else:
            functions = all_functions

        if args.limit:
            functions = functions[:args.limit]

        if not functions:
            print("No target functions found.")
            sys.exit(1)

        fn_label = ", ".join(fn["name"] for fn in functions) if len(functions) <= 8 else f"{len(functions)} functions"
        print(f"\nGenerating tests for: {fn_label}")

        spec = read_readme(tmp)
        fn_names = {fn["name"] for fn in functions}
        test_examples = extract_test_examples(tmp, fn_names)
        for fn in functions:
            fn["spec"] = spec
            fn["test_examples"] = test_examples.get(fn["name"], [])
            fn["callees"] = extract_callees(fn["source"], all_functions)

        result = run_for_repo(functions, run_dir, tmp, cfg, timeout, fix_pass=args.fix_pass)
        print(f"\nTests run: {result['tests_run']}  passed: {result['tests_passed']}  errored: {result['tests_errored']}")
        print_bug_report(result["failures"], args.repo_url)
        print(f"\nDone. Output: {run_dir}")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def _fn_test_dir(base_out_dir, file_path):
    module_dir = os.path.dirname(file_path.replace("\\", "/"))
    return os.path.join(base_out_dir, module_dir) if module_dir else base_out_dir


def _write_fn_tests(test_dir, fn_name, tests):
    os.makedirs(test_dir, exist_ok=True)
    for kind, code in tests.items():
        if code and code.strip():
            path = os.path.join(test_dir, f"test_{fn_name}_{kind}.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)


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

        spec = open(args.spec, encoding="utf-8").read() if args.spec else read_readme(repo_dir)

        print(f"Extracting functions from '{project_name}'...")
        all_fns = extract_functions(repo_dir)
        functions = [
            f for f in all_fns
            if not os.path.basename(f["file_path"]).startswith("test_")
            and "/test" not in f["file_path"].replace("\\", "/")
        ]
        if args.limit:
            functions = functions[:args.limit]
        print(f"  {len(functions)} functions found")

        out_dir = os.path.join(args.output_dir, project_name)
        os.makedirs(out_dir, exist_ok=True)
        with open(os.path.join(out_dir, "conftest.py"), "w", encoding="utf-8") as fh:
            fh.write(f"import sys\nsys.path.insert(0, {repr(os.path.abspath(repo_dir))})\n")

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
                results.append({"function": fn["name"], "file": fn["file_path"], "status": "error", "error": str(e)})

        from src.pipeline import _write_project_run_scripts
        _write_project_run_scripts(out_dir, project_name)

        ok = sum(1 for r in results if r["status"] == "ok")
        print(f"\n{'=' * 55}")
        print(f"Done.  {ok}/{len(results)} functions  →  {out_dir}")
    finally:
        if tmp:
            shutil.rmtree(tmp, ignore_errors=True)


def main():
    p = argparse.ArgumentParser(description="Generate and run tests for a GitHub repo function.")
    p.add_argument("repo_url", nargs="?", help="GitHub repo URL")
    p.add_argument("function_name", nargs="*", help="One or more function names to test")
    p.add_argument("--provider",   default="deepseek")
    p.add_argument("--model",      default=None)
    p.add_argument("--preset",     default="default", choices=["fast", "default", "thorough"])
    p.add_argument("--output-dir", default=OUTPUT_DIR)
    p.add_argument("--desc",       default="")
    p.add_argument("--no-install", action="store_true")
    p.add_argument("--fix-pass",   action="store_true", dest="fix_pass")
    p.add_argument("--limit",      type=int, default=0, metavar="N")
    p.add_argument("--project",    metavar="REPO_URL_OR_PATH", help="Generate tests for every function in a project")
    p.add_argument("--spec",       metavar="SPEC_FILE", default=None)
    args = p.parse_args()

    if args.project:
        _run_project(args)
    elif args.repo_url and len(args.function_name) == 1 and not args.limit:
        args.function_name = args.function_name[0]
        _run_single(args)
    elif args.repo_url:
        args.function_names = args.function_name
        _run_multi(args)
    else:
        p.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
