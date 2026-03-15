import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ast
import asyncio
import shutil
import tempfile

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.agents import build_graph, TEST_TYPES
from src.writer import write_function, write_tests, write_meta
from src.mutator import run_mutmut, compute_unique_kills


def parse_args():
    args = sys.argv[1:]
    config = {
        "repo": "https://github.com/keon/algorithms",
        "output": "./outputs",
        "concurrency": 1,
        "limit": 3,
        "min_lines": 0,
    }

    i = 0
    while i < len(args):
        if args[i] == "--repo" and i + 1 < len(args):
            config["repo"] = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            config["output"] = args[i + 1]
            i += 2
        elif args[i] == "--concurrency" and i + 1 < len(args):
            config["concurrency"] = int(args[i + 1])
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            config["limit"] = int(args[i + 1])
            i += 2
        elif args[i] == "--min-lines" and i + 1 < len(args):
            config["min_lines"] = int(args[i + 1])
            i += 2
        else:
            i += 1

    return config


def _fn_complexity(source):
    lines = len(source.strip().splitlines())
    try:
        tree = ast.parse(source)
        branches = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, (ast.If, ast.For, ast.While, ast.ExceptHandler))
        )
    except SyntaxError:
        branches = 0
    return lines, branches


def main():
    load_dotenv()
    config = parse_args()

    repo = config["repo"]
    output_base = config["output"]
    concurrency = config["concurrency"]
    limit = config["limit"]
    min_lines = config["min_lines"]

    repo_name = repo.rstrip("/").split("/")[-1].replace(".git", "")
    output_dir = os.path.join(output_base, repo_name)
    write_meta(repo, output_dir)

    tmp = tempfile.mkdtemp()
    print(f"Cloning {repo}...")
    clone_repo(repo, tmp)

    print("Extracting functions...")
    all_functions = extract_functions(tmp)
    print(f"Found {len(all_functions)} function(s)")

    if not all_functions:
        shutil.rmtree(tmp, ignore_errors=True)
        return

    # Apply min-lines filter, then take limit
    if min_lines > 0:
        all_functions = [fn for fn in all_functions if len(fn["source"].strip().splitlines()) >= min_lines]
        print(f"After --min-lines {min_lines} filter: {len(all_functions)} function(s)")

    functions = all_functions[:limit]
    print(f"Using first {limit} function(s)")

    print(f"Writing function files to {output_dir}...")
    for i, fn in enumerate(functions):
        write_function(fn, output_dir, i)

    # --- Step 2: Generate tests via LLM agents ---

    async def process(fn, index, sem):
        async with sem:
            try:
                graph = build_graph()
                state = {
                    "function_info": fn,
                    "statement_tests": "",
                    "block_tests": "",
                    "condition_tests": "",
                    "path_tests": "",
                    "bva_tests": "",
                    "ecp_tests": "",
                    "mutation_tests": "",
                }
                result = await graph.ainvoke(state)
                write_tests(fn, result, output_dir, index)
                print(f"  Done: {fn['name']}")
            except Exception as e:
                print(f"  Failed: {fn['name']} — {e}")

    async def run():
        sem = asyncio.Semaphore(concurrency)
        tasks = [process(fn, i, sem) for i, fn in enumerate(functions)]
        await asyncio.gather(*tasks)

    print(f"\nGenerating tests (concurrency={concurrency})...")
    asyncio.run(run())

    # --- Step 3: Mutation testing ---

    print("\n=== Mutation Testing ===")
    print("Mutants are generated from the original function source.")
    print("Each agent's tests are run against every mutant.\n")

    total_killed_all = 0
    total_mutants_all = 0

    for i, fn in enumerate(functions):
        func_name = fn["name"]
        func_file = os.path.join(output_dir, "functions", f"{func_name}_{i}", "function.py")
        lines, branches = _fn_complexity(fn["source"])

        if not os.path.exists(func_file):
            print(f"  Skipping {func_name} — function file not found")
            continue

        # Run mutation testing with each agent's test file
        agent_kills = {}   # test_type -> set of killed mutant IDs
        agent_totals = {}  # test_type -> total mutant count
        mutant_count = None

        for test_type in TEST_TYPES:
            test_file = os.path.join(output_dir, "test_cases", f"{func_name}_{i}", f"test_{test_type}.py")

            if not os.path.exists(test_file):
                agent_kills[test_type] = set()
                agent_totals[test_type] = 0
                continue

            print(f"  {func_name}/{test_type}...", end=" ", flush=True)
            result = run_mutmut(func_file, test_file, tmp, fn["file_path"])
            agent_kills[test_type] = result["killed"]
            agent_totals[test_type] = result["total_mutants"]

            if mutant_count is None:
                mutant_count = result["total_mutants"]

            print(f"{len(result['killed'])}/{result['total_mutants']} killed")

        if mutant_count is None or mutant_count == 0:
            print(f"\n  {func_name}: no mutants generated\n")
            continue

        unique_kills = compute_unique_kills(agent_kills)

        # Print per-function summary
        print(f"\n  Function: {func_name}  ({lines} lines, {branches} branches, {mutant_count} mutants)")
        print(f"  {'agent':>10s}  {'killed':>6s}  {'unique':>6s}  {'rate':>6s}  coverage")
        print(f"  {'-'*10}  {'-'*6}  {'-'*6}  {'-'*6}  {'-'*20}")
        for test_type in TEST_TYPES:
            killed = len(agent_kills[test_type])
            total = agent_totals[test_type]
            unique = unique_kills.get(test_type, 0)
            rate = (killed / total * 100) if total > 0 else 0
            bar = "#" * int(rate / 5) + "." * (20 - int(rate / 5))
            print(f"  {test_type:>10s}  {killed:>3d}/{total:<3d}  {unique:>6d}  {rate:5.1f}%  [{bar}]")

        func_killed = sum(len(k) for k in agent_kills.values())
        func_total = sum(agent_totals.values())
        total_killed_all += func_killed
        total_mutants_all += func_total
        print()

    # --- Overall summary ---
    print("=" * 60)
    if total_mutants_all > 0:
        overall_rate = total_killed_all / total_mutants_all * 100
        print(f"Overall: {total_killed_all}/{total_mutants_all} killed ({overall_rate:.1f}%) across all agents")
    else:
        print("No mutants were generated.")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone. Output: {output_dir}")


if __name__ == "__main__":
    main()
