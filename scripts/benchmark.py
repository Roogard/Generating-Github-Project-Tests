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
from src.harness import run_harness
from src.writer import write_meta


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

            candidates = fn_by_name.get(target_name, [])
            if not candidates:
                print(f"\n  SKIP: {target_name} not found in {repo_name}")
                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
                    "status": "not_found",
                })
                continue

            # pick the first match
            fn = candidates[0]
            idx = len(results)

            print(f"\n--- Benchmark {idx + 1}: {target_name} ({difficulty}) from {repo_name} ---")
            t0 = time.time()
            try:
                final_state = run_harness(fn, idx, repo_output, tmp, config)
                elapsed = time.time() - t0

                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
                    "status": "ok",
                    "mutation_score": round(final_state["mutation_score"], 4),
                    "llm_mutation_score": round(final_state.get("llm_mutation_score", 0.0), 4),
                    "branch_coverage": round(final_state["branch_coverage"], 4),
                    "line_coverage": round(final_state["line_coverage"], 4),
                    "assertion_density": round(final_state.get("assertion_density", 0.0), 4),
                    "test_diversity": round(final_state.get("test_diversity", 0.0), 4),
                    "quality_score": round(final_state.get("quality_score", 0.0), 4),
                    "steps": final_state["step_count"],
                    "fix_attempts": final_state["fix_attempts"],
                    "mutant_count": final_state["mutant_count"],
                    "elapsed_seconds": round(elapsed, 1),
                })

                print(f"  quality={final_state.get('quality_score', 0):.2f}, "
                      f"mutation={final_state['mutation_score']:.1%}, "
                      f"llm_mutation={final_state.get('llm_mutation_score', 0):.1%}, "
                      f"line={final_state['line_coverage']:.1%}, "
                      f"branch={final_state['branch_coverage']:.1%}, "
                      f"steps={final_state['step_count']}, "
                      f"time={elapsed:.1f}s")
            except Exception as e:
                elapsed = time.time() - t0
                print(f"  ERROR: {e}")
                results.append({
                    "repo": repo_url,
                    "function": target_name,
                    "difficulty": difficulty,
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
        print("\n" + "=" * 60)
        print("BENCHMARK SUMMARY")
        print("=" * 60)

        avg_quality = sum(r["quality_score"] for r in ok_results) / len(ok_results)
        avg_mutation = sum(r["mutation_score"] for r in ok_results) / len(ok_results)
        avg_llm_mutation = sum(r["llm_mutation_score"] for r in ok_results) / len(ok_results)
        avg_line = sum(r["line_coverage"] for r in ok_results) / len(ok_results)
        avg_branch = sum(r["branch_coverage"] for r in ok_results) / len(ok_results)
        avg_steps = sum(r["steps"] for r in ok_results) / len(ok_results)

        print(f"  Functions tested: {len(ok_results)}/{len(results)}")
        print(f"  Avg quality score:      {avg_quality:.3f}")
        print(f"  Avg mutation score:     {avg_mutation:.1%}")
        print(f"  Avg LLM mutation score: {avg_llm_mutation:.1%}")
        print(f"  Avg line coverage:      {avg_line:.1%}")
        print(f"  Avg branch coverage:    {avg_branch:.1%}")
        print(f"  Avg steps:              {avg_steps:.1f}")

        # breakdown by difficulty
        for tier in ["simple", "moderate", "complex"]:
            tier_results = [r for r in ok_results if r["difficulty"] == tier]
            if tier_results:
                t_quality = sum(r["quality_score"] for r in tier_results) / len(tier_results)
                t_mutation = sum(r["mutation_score"] for r in tier_results) / len(tier_results)
                t_llm = sum(r["llm_mutation_score"] for r in tier_results) / len(tier_results)
                t_line = sum(r["line_coverage"] for r in tier_results) / len(tier_results)
                t_branch = sum(r["branch_coverage"] for r in tier_results) / len(tier_results)
                print(f"\n  {tier} ({len(tier_results)} functions):")
                print(f"    quality={t_quality:.3f}, mutation={t_mutation:.1%}, llm_mutation={t_llm:.1%}, "
                      f"line={t_line:.1%}, branch={t_branch:.1%}")

        min_quality = min(r["quality_score"] for r in ok_results)
        max_quality = max(r["quality_score"] for r in ok_results)
        print(f"\n  Quality range: {min_quality:.3f} — {max_quality:.3f}")

    print(f"\nResults written to {results_path}")


if __name__ == "__main__":
    p = argparse.ArgumentParser(description="Run benchmark suite")
    p.add_argument("--benchmark", default="data/benchmark_functions.json", help="Benchmark functions file")
    p.add_argument("--output", default="eval_output", help="Output directory")
    p.add_argument("--limit", type=int, default=0, help="Limit number of functions (0 = all)")
    args = p.parse_args()
    run_benchmark(args.benchmark, args.output, args.limit)
