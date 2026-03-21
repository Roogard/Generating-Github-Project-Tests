import argparse
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ast
import json
import shutil
import tempfile

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.harness import run_harness
from src.writer import write_meta
from src.mutator import compute_unique_kills
from src.memory import (
    get_db, get_collection, store_result,
    store_reflection, generate_reflections,
)


def parse_args():
    p = argparse.ArgumentParser(description="Generate unit tests for a GitHub repo")
    p.add_argument("--repo", default="https://github.com/keon/algorithms", help="GitHub repo URL")
    p.add_argument("--output", default="./outputs", help="Output directory")
    p.add_argument("--limit", type=int, default=3, help="Max functions to process")
    p.add_argument("--min-lines", type=int, default=0, dest="min_lines", help="Skip functions shorter than N lines")
    p.add_argument("--max-lines", type=int, default=0, dest="max_lines", help="Skip functions longer than N lines")
    p.add_argument("--min-branches", type=int, default=0, dest="min_branches", help="Skip functions with fewer than N branches")
    p.add_argument("--max-branches", type=int, default=0, dest="max_branches", help="Skip functions with more than N branches")
    p.add_argument("--stratify", action="store_true", help="Sample evenly across simple/moderate/complex functions")
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
    limit = config["limit"]
    min_lines = config["min_lines"]
    max_lines = config["max_lines"]
    min_branches = config["min_branches"]
    max_branches = config["max_branches"]
    stratify = config["stratify"]

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

    # --- Run harness ---

    print("\nRunning harness (iterative refinement)...")
    batch_records = []
    for i, fn in enumerate(functions):
        print(f"\n--- Function {i + 1}/{len(functions)}: {fn['name']} ---")
        final_state = run_harness(fn, i, output_dir, tmp)

        agent_kills = final_state["agent_kills"]
        mutant_count = final_state["mutant_count"]
        selected = final_state["planned_generates"]

        for tt in selected:
            if tt not in agent_kills:
                agent_kills[tt] = set()
        agent_totals = {tt: mutant_count for tt in agent_kills}
        unique_kills = compute_unique_kills(agent_kills) if mutant_count > 0 else {}

        if mutant_count > 0:
            store_result(collection, fn, selected, agent_kills, agent_totals, mutant_count, unique_kills)

            record = {"function_name": fn["name"], "agents_selected": json.dumps(selected)}
            for tt in selected:
                record[f"{tt}_killed"] = len(agent_kills.get(tt, set()))
                record[f"{tt}_total"] = agent_totals.get(tt, 0)
                record[f"{tt}_unique"] = unique_kills.get(tt, 0)
            record["overall_kill_rate"] = final_state["mutation_score"]
            batch_records.append(record)

        print(f"  Final mutation score: {final_state['mutation_score']:.1%}")
        print(f"  Steps taken: {final_state['step_count']}")

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
