"""
Pipeline entry point.

Usage:
    uv run python -m src.main --repo <github_url> --mode train   # build memory DB
    uv run python -m src.main --repo <github_url> --mode test    # use memory to select agents

Train mode: runs all 7 agents on every function and stores ground-truth mutation scores in ChromaDB.
Test  mode: retrieves similar past functions from memory, asks the supervisor to pick 2-4 agents,
            then runs only those agents — faster and more focused.
"""
import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ast
import asyncio
import json
import shutil
import tempfile

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.agents import build_graph, TEST_TYPES
from src.supervisor import select_agents
from src.writer import write_function, write_tests, write_meta
from src.mutator import run_all_agents, compute_unique_kills
from src.memory import (
    get_db, get_collection, retrieve_similar, store_result,
    get_reflections, store_reflection, format_memory_context, generate_reflections,
)


def parse_args():
    p = argparse.ArgumentParser(description="Generate unit tests for a GitHub repo")
    p.add_argument("--repo", default="https://github.com/keon/algorithms", help="GitHub repo URL")
    p.add_argument("--output", default="./outputs", help="Output directory")
    p.add_argument("--concurrency", type=int, default=1, help="Number of functions to process in parallel")
    p.add_argument("--limit", type=int, default=3, help="Max functions to process")
    p.add_argument("--min-lines", type=int, default=0, dest="min_lines", help="Skip functions shorter than N lines")
    p.add_argument("--max-lines", type=int, default=0, dest="max_lines", help="Skip functions longer than N lines")
    p.add_argument("--min-branches", type=int, default=0, dest="min_branches", help="Skip functions with fewer than N branches")
    p.add_argument("--max-branches", type=int, default=0, dest="max_branches", help="Skip functions with more than N branches")
    p.add_argument("--stratify", action="store_true", help="Sample evenly across simple/moderate/complex functions")
    p.add_argument("--mode", default="test", choices=["train", "test"],
                   help="train=run all 7 agents and store ground truth; test=use memory to select agents")
    return vars(p.parse_args())


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


def _classify_complexity(source):
    lines, branches = _fn_complexity(source)
    if lines <= 15 and branches <= 2:
        return "simple"
    elif lines <= 40 and branches <= 6:
        return "moderate"
    else:
        return "complex"


def _stratified_sample(functions, limit):
    import random
    buckets = {"simple": [], "moderate": [], "complex": []}
    for fn in functions:
        buckets[_classify_complexity(fn["source"])].append(fn)
    for b in buckets:
        random.shuffle(buckets[b])
    per_bucket = max(1, limit // 3)
    selected = []
    overflow = []
    for bucket_name in ["simple", "moderate", "complex"]:
        pool = buckets[bucket_name]
        selected.extend(pool[:per_bucket])
        overflow.extend(pool[per_bucket:])
    random.shuffle(overflow)
    remaining = limit - len(selected)
    if remaining > 0:
        selected.extend(overflow[:remaining])
    return selected[:limit]


def main():
    load_dotenv()
    config = parse_args()

    repo = config["repo"]
    output_base = config["output"]
    concurrency = config["concurrency"]
    limit = config["limit"]
    min_lines = config["min_lines"]
    max_lines = config["max_lines"]
    min_branches = config["min_branches"]
    max_branches = config["max_branches"]
    stratify = config["stratify"]
    mode = config["mode"]

    # Initialize memory
    db = get_db()
    collection = get_collection(db)

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

    # Apply filters
    if min_lines > 0:
        all_functions = [fn for fn in all_functions if len(fn["source"].strip().splitlines()) >= min_lines]
        print(f"After --min-lines {min_lines}: {len(all_functions)} function(s)")
    if max_lines > 0:
        all_functions = [fn for fn in all_functions if len(fn["source"].strip().splitlines()) <= max_lines]
        print(f"After --max-lines {max_lines}: {len(all_functions)} function(s)")
    if min_branches > 0:
        all_functions = [fn for fn in all_functions if _fn_complexity(fn["source"])[1] >= min_branches]
        print(f"After --min-branches {min_branches}: {len(all_functions)} function(s)")
    if max_branches > 0:
        all_functions = [fn for fn in all_functions if _fn_complexity(fn["source"])[1] <= max_branches]
        print(f"After --max-branches {max_branches}: {len(all_functions)} function(s)")

    if stratify:
        functions = _stratified_sample(all_functions, limit)
        buckets = {}
        for fn in functions:
            b = _classify_complexity(fn["source"])
            buckets[b] = buckets.get(b, 0) + 1
        print(f"Stratified sample: {len(functions)} function(s) — {buckets}")
    else:
        functions = all_functions[:limit]
        print(f"Using first {limit} function(s)")

    print(f"Writing function files to {output_dir}...")
    for i, fn in enumerate(functions):
        write_function(fn, output_dir, i)

    # --- Step 2: Generate tests via LLM agents ---

    fn_meta = {}  # index -> selected agents list

    async def process(fn, index, sem):
        async with sem:
            try:
                if mode == "train":
                    # Training: supervisor picks (logged), but run all 7
                    selected = select_agents(fn)
                    print(f"  {fn['name']}: supervisor selected {selected} (training: running all 7)")
                    fn_meta[index] = selected
                    graph = build_graph()
                else:
                    # Testing: use memory to inform supervisor, run only selected
                    similar = retrieve_similar(collection, fn, k=5)
                    reflections = get_reflections(db, limit=10)
                    ctx = format_memory_context(similar, reflections)
                    selected = select_agents(fn, memory_context=ctx if ctx else None)
                    print(f"  {fn['name']}: supervisor selected {selected}")
                    fn_meta[index] = selected
                    graph = build_graph(selected)

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

    print(f"\nGenerating tests (mode={mode}, concurrency={concurrency})...")
    asyncio.run(run())

    # --- Step 3: Mutation testing ---

    print("\n=== Mutation Testing ===")
    print("Mutants are generated from the original function source.")
    print("Each agent's tests are run against every mutant.\n")

    total_killed_all = 0
    total_mutants_all = 0
    batch_records = []

    for i, fn in enumerate(functions):
        func_name = fn["name"]
        func_file = os.path.join(output_dir, "functions", f"{func_name}_{i}", "function.py")
        lines, branches = _fn_complexity(fn["source"])

        if not os.path.exists(func_file):
            print(f"  Skipping {func_name} — function file not found")
            continue

        # Collect available test files for this function
        test_files_dict = {}
        for test_type in TEST_TYPES:
            test_file = os.path.join(output_dir, "test_cases", f"{func_name}_{i}", f"test_{test_type}.py")
            if os.path.exists(test_file):
                test_files_dict[test_type] = test_file

        if not test_files_dict:
            print(f"  {func_name}: no test files\n")
            continue

        print(f"  {func_name}: running {len(test_files_dict)} agent(s) × mutants in parallel...", flush=True)
        original_file = os.path.join(tmp, fn["file_path"]) if fn.get("file_path") else None
        agent_kills, agent_totals, mutant_count = run_all_agents(
            func_file, test_files_dict, tmp, fn["source"], original_file=original_file
        )

        # Fill zeros for agents with no test file
        for test_type in TEST_TYPES:
            if test_type not in agent_kills:
                agent_kills[test_type] = set()
                agent_totals[test_type] = 0

        if mutant_count == 0:
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

        # Store result in memory
        selected = fn_meta.get(i, list(TEST_TYPES))
        store_result(collection, fn, selected, agent_kills, agent_totals, mutant_count, unique_kills)

        # Build record for reflection generation
        record = {
            "function_name": func_name,
            "agents_selected": json.dumps(selected),
        }
        for test_type in TEST_TYPES:
            record[f"{test_type}_killed"] = len(agent_kills.get(test_type, set()))
            record[f"{test_type}_total"] = agent_totals.get(test_type, 0)
            record[f"{test_type}_unique"] = unique_kills.get(test_type, 0)
        overall_k = func_killed
        overall_t = func_total
        record["overall_kill_rate"] = overall_k / overall_t if overall_t > 0 else 0.0
        batch_records.append(record)

    # --- Overall summary ---
    print("=" * 60)
    if total_mutants_all > 0:
        overall_rate = total_killed_all / total_mutants_all * 100
        print(f"Overall: {total_killed_all}/{total_mutants_all} killed ({overall_rate:.1f}%) across all agents")
    else:
        print("No mutants were generated.")

    # Generate and store reflections
    if batch_records:
        print("\nGenerating reflections from this run...")
        reflection_texts = generate_reflections(batch_records)
        for text in reflection_texts:
            store_reflection(db, text)
        print(f"Memory updated: {collection.count()} function records, "
              f"{len(reflection_texts)} new reflections")

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"\nDone. Output: {output_dir}")


def cli():
    main()


if __name__ == "__main__":
    main()
