import argparse
import json
import os
import shutil
import sys
import tempfile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from src.config import load_config
from src.extractor import clone_repo, extract_functions
from src.agents import call_agent
from src.runner import run_single_test
from src.writer import write_meta, write_function, write_generated_tests
from src.reporter import parse_failures
from src.main import WHITEBOX_TYPES, BLACKBOX_TYPES, run_harness_loop


def load_benchmark(path="data/benchmark_functions.json"):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def run_benchmark(benchmark_path=None, output_dir="eval_output", limit=0):
    load_dotenv()
    config = load_config()

    entries = load_benchmark(benchmark_path or "data/benchmark_functions.json")
    if limit > 0:
        entries = entries[:limit]

    # group by repo to avoid cloning the same repo multiple times
    by_repo = {}
    for entry in entries:
        repo = entry["repo"]
        if repo not in by_repo:
            by_repo[repo] = []
        by_repo[repo].append(entry)

    # timestamped run directory so runs accumulate
    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    run_dir = os.path.join(output_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)

    all_types = WHITEBOX_TYPES + BLACKBOX_TYPES
    results = []

    for repo_url, repo_entries in by_repo.items():
        repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
        repo_output = os.path.join(run_dir, repo_name)
        write_meta(repo_url, repo_output)

        tmp = tempfile.mkdtemp()
        print(f"\nCloning {repo_url}...")
        try:
            clone_repo(repo_url, tmp)
        except Exception as e:
            print(f"  Failed to clone: {e}")
            shutil.rmtree(tmp, ignore_errors=True)
            continue

        print("Extracting functions...")
        all_functions = extract_functions(tmp)
        fn_by_name = {}
        for fn in all_functions:
            fn_by_name.setdefault(fn["name"], []).append(fn)

        for entry in repo_entries:
            target_name = entry["function_name"]
            difficulty = entry.get("difficulty", "unknown")

            target_file = entry.get("file")
            candidates = fn_by_name.get(target_name, [])
            if target_file:
                norm = target_file.replace("\\", "/")
                candidates = [c for c in candidates if
                    c["file_path"].replace("\\", "/") == norm or
                    c["file_path"].replace("\\", "/").endswith("/" + norm)]
            if not candidates:
                print(f"\n  SKIP: {target_name} not found in {repo_name}")
                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
                    "has_bug": entry.get("has_bug"),
                    "status": "not_found",
                })
                continue

            fn = candidates[0]
            idx = len(results)

            print(f"\n--- Benchmark {idx + 1}: {target_name} ({difficulty}) from {repo_name} ---")
            t0 = time.time()
            try:
                write_function(fn, repo_output, idx)

                # generate tests
                generated = {}
                for test_type in all_types:
                    code = call_agent(test_type, fn, config)
                    if code and code.strip():
                        generated[test_type] = code
                write_generated_tests(fn, generated, repo_output, idx)

                # run all test files
                test_outcomes = {}
                fn_dir_name = f"{fn['name']}_{idx}"
                test_dir = os.path.join(repo_output, "generated_tests", fn_dir_name)
                if os.path.isdir(test_dir):
                    for fname in sorted(os.listdir(test_dir)):
                        if fname.startswith("test_") and fname.endswith(".py"):
                            test_file = os.path.join(test_dir, fname)
                            result = run_single_test(
                                test_file, tmp, timeout=config["timeouts"]["test"]
                            )
                            test_outcomes[(fn_dir_name, fname)] = result

                failures = parse_failures(test_outcomes)

                fix_iterations = 0
                converged = False
                if failures:
                    fn_dir_name_loop = f"{fn['name']}_{idx}"
                    final_outcomes, history = run_harness_loop(
                        fn, fn_dir_name_loop, test_outcomes, tmp, repo_output, idx, config,
                        max_iterations=3,
                    )
                    test_outcomes.update(final_outcomes)
                    failures = parse_failures(test_outcomes)
                    fix_iterations = len(history)
                    converged = bool(history) and history[-1]["failures_count"] == 0

                elapsed = time.time() - t0

                tests_passed = sum(len(r["passed"]) for r in test_outcomes.values())
                tests_failed = sum(len(r["failed"]) for r in test_outcomes.values())
                tests_errored = sum(len(r["errors"]) for r in test_outcomes.values())

                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
                    "has_bug": entry.get("has_bug"),
                    "status": "ok",
                    "tests_generated": len(generated),
                    "tests_passed": tests_passed,
                    "tests_failed": tests_failed,
                    "tests_errored": tests_errored,
                    "failures_count": len(failures),
                    "fix_iterations": fix_iterations,
                    "converged": converged,
                    "elapsed_seconds": round(elapsed, 1),
                })

                print(f"  generated={len(generated)}, passed={tests_passed}, "
                      f"failed={tests_failed}, errors={tests_errored}, "
                      f"bugs={len(failures)}, time={elapsed:.1f}s")

            except Exception as e:
                elapsed = time.time() - t0
                print(f"  ERROR: {e}")
                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
                    "has_bug": entry.get("has_bug"),
                    "status": "error",
                    "error": str(e),
                    "elapsed_seconds": round(elapsed, 1),
                })

        shutil.rmtree(tmp, ignore_errors=True)

    # write results
    results_path = os.path.join(run_dir, "benchmark_results.json")
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    # print summary
    ok_results = [r for r in results if r["status"] == "ok"]
    if ok_results:
        total_tests = sum(r["tests_passed"] + r["tests_failed"] + r["tests_errored"] for r in ok_results)
        total_failures = sum(r["failures_count"] for r in ok_results)

        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)
        print(f"  Functions tested: {len(ok_results)}/{len(results)}")
        print(f"  Total tests run:  {total_tests}")
        print(f"  Total failures:   {total_failures} (potential bugs detected)")

        buggy = [r for r in ok_results if r.get("has_bug") is True]
        clean = [r for r in ok_results if r.get("has_bug") is False]
        bugs_detected = sum(1 for r in buggy if r["failures_count"] > 0 or r["tests_failed"] > 0)
        clean_passed = sum(1 for r in clean if r["tests_failed"] == 0 and r["tests_errored"] == 0)
        print(f"\n  Bug detection rate: {bugs_detected}/{len(buggy)} buggy functions caught")
        print(f"  Clean control:      {clean_passed}/{len(clean)} clean functions passed")

        for tier in ["simple", "moderate", "complex"]:
            tier_results = [r for r in ok_results if r["difficulty"] == tier]
            if tier_results:
                avg_failures = sum(r["failures_count"] for r in tier_results) / len(tier_results)
                avg_tests = sum(
                    r["tests_passed"] + r["tests_failed"] + r["tests_errored"]
                    for r in tier_results
                ) / len(tier_results)
                print(f"\n  {tier} ({len(tier_results)} functions):")
                print(f"    avg {avg_failures:.1f} failures, avg {avg_tests:.1f} tests run")

    print(f"\nResults written to {results_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run benchmark suite")
    p.add_argument("--benchmark", default="data/benchmark_functions.json", help="Benchmark functions file")
    p.add_argument("--output", default="eval_output", help="Output directory")
    p.add_argument("--limit", type=int, default=0, help="Limit number of functions (0 = all)")
    args = p.parse_args()
    run_benchmark(args.benchmark, args.output, args.limit)
