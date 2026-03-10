import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import json
import shutil
import tempfile

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.features import extract_features
from src.agents import build_graph, TEST_TYPES
from src.writer import write_function, write_tests
from src.runner import run_single_test
from src.mutator import run_mutmut


def process_function(fn, repo_clone_dir, result_state, tmp_output, index):
    features = extract_features(fn)

    # write test files to temp output dir
    write_tests(fn, result_state, tmp_output, index)

    # run each agent's tests and collect pass/fail + kill vectors
    test_dir = os.path.join(tmp_output, "test_cases", f"{fn['name']}_{index}")
    func_dir = os.path.join(tmp_output, "functions", f"{fn['name']}_{index}")

    # write function source for mutation testing
    write_function(fn, tmp_output, index)
    func_file = os.path.join(func_dir, "function.py")

    kill_vectors = {}
    tests_passed = {}
    any_mutmut_ran = False

    for tt in TEST_TYPES:
        test_file = os.path.join(test_dir, f"test_{tt}.py")
        test_content = result_state.get(f"{tt}_tests", "")

        if not test_content or not test_content.strip() or not os.path.exists(test_file):
            kill_vectors[tt] = []
            tests_passed[tt] = 0
            continue

        # run tests first to check pass/fail
        test_result = run_single_test(test_file, repo_clone_dir)
        num_passed = len(test_result["passed"])
        tests_passed[tt] = num_passed

        if num_passed == 0:
            kill_vectors[tt] = []
            print(f"      {tt}: all tests failed, skipping mutation testing")
            continue

        # run mutation testing only for passing tests
        mut_result = run_mutmut(func_file, test_file, repo_clone_dir)

        if mut_result["stderr"] == "mutmut timed out":
            print(f"      {tt}: mutmut timed out, skipping")
            kill_vectors[tt] = []
            continue

        kill_vectors[tt] = sorted(list(mut_result["killed"]))
        any_mutmut_ran = True

    if not any_mutmut_ran:
        return None

    # total mutants = union of all killed + survived from any run
    all_killed = set()
    for kv in kill_vectors.values():
        all_killed |= set(kv)
    total_mutants = len(all_killed) if all_killed else 0

    if total_mutants == 0:
        return None

    return {
        "function_name": fn["name"],
        "file_path": fn["file_path"],
        "features": features,
        "kill_vectors": kill_vectors,
        "total_mutants": total_mutants,
        "tests_passed": tests_passed,
    }


async def generate_dataset(repos_path, output_path, concurrency=1):
    load_dotenv()

    with open(repos_path, encoding="utf-8") as f:
        repos = json.load(f)

    dataset = []

    for repo_info in repos:
        url = repo_info["url"]
        name = repo_info["name"]
        print(f"\n{'='*60}")
        print(f"Processing repo: {name} ({url})")
        print(f"{'='*60}")

        tmp_clone = tempfile.mkdtemp()
        tmp_output = tempfile.mkdtemp()

        try:
            clone_repo(url, tmp_clone)
            functions = extract_functions(tmp_clone)
            print(f"  Found {len(functions)} function(s)")

            if not functions:
                continue

            graph = build_graph()
            sem = asyncio.Semaphore(concurrency)

            async def process(fn, index):
                async with sem:
                    try:
                        print(f"  [{index+1}/{len(functions)}] {fn['name']}...")

                        # generate tests with all 7 agents
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

                        # process: run tests + mutation testing
                        record = process_function(
                            fn, tmp_clone, result, tmp_output, index
                        )
                        if record:
                            record["repo"] = name
                        return record

                    except Exception as e:
                        print(f"    SKIP {fn['name']}: {e}")
                        return None

            tasks = [process(fn, i) for i, fn in enumerate(functions)]
            results = await asyncio.gather(*tasks)

            for record in results:
                if record is not None:
                    dataset.append(record)
                    kills_summary = {
                        tt: len(kv) for tt, kv in record["kill_vectors"].items() if kv
                    }
                    print(f"    Added: {record['function_name']} "
                          f"(kills: {kills_summary}, total_mutants: {record['total_mutants']})")

        finally:
            shutil.rmtree(tmp_clone, ignore_errors=True)
            shutil.rmtree(tmp_output, ignore_errors=True)

    # write dataset
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"\nDataset written to {output_path}")
    print(f"Total records: {len(dataset)}")
    return dataset


if __name__ == "__main__":
    repos_path = "data/repos.json"
    output_path = "data/dataset.json"
    concurrency = 1

    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--repos" and i + 1 < len(args):
            repos_path = args[i + 1]
            i += 2
        elif args[i] == "--output" and i + 1 < len(args):
            output_path = args[i + 1]
            i += 2
        elif args[i] == "--concurrency" and i + 1 < len(args):
            concurrency = int(args[i + 1])
            i += 2
        else:
            i += 1

    asyncio.run(generate_dataset(repos_path, output_path, concurrency))
