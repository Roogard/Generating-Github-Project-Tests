import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import shutil
import tempfile

from dotenv import load_dotenv

from src.extractor import clone_repo, extract_functions
from src.agents import build_graph
from src.writer import write_function, write_tests, write_meta


def parse_args():
    args = sys.argv[1:]
    config = {
        "repo": "https://github.com/keon/algorithms",
        "output": "./outputs",
        "concurrency": 1,
        "guided": False,
        "model": "data/model.pkl",
        "threshold": 0.05,
        "limit": None,
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
        elif args[i] == "--guided":
            config["guided"] = True
            i += 1
        elif args[i] == "--model" and i + 1 < len(args):
            config["model"] = args[i + 1]
            i += 2
        elif args[i] == "--threshold" and i + 1 < len(args):
            config["threshold"] = float(args[i + 1])
            i += 2
        elif args[i] == "--limit" and i + 1 < len(args):
            config["limit"] = int(args[i + 1])
            i += 2
        else:
            i += 1

    return config


def main():
    load_dotenv()
    config = parse_args()

    repo = config["repo"]
    output_base = config["output"]
    concurrency = config["concurrency"]

    repo_name = repo.rstrip("/").split("/")[-1].replace(".git", "")
    output_dir = os.path.join(output_base, repo_name)
    write_meta(repo, output_dir)

    tmp = tempfile.mkdtemp()
    print(f"Cloning {repo}...")
    clone_repo(repo, tmp)

    print("Extracting functions...")
    functions = extract_functions(tmp)
    print(f"Found {len(functions)} function(s)")

    if not functions:
        shutil.rmtree(tmp, ignore_errors=True)
        return

    if config["limit"]:
        functions = functions[:config["limit"]]
        print(f"Limited to first {config['limit']} function(s)")

    print(f"Writing function files to {output_dir}...")
    for i, fn in enumerate(functions):
        write_function(fn, output_dir, i)

    # guided mode: predict which agents to use per function
    if config["guided"]:
        from src.model import predict_agents
        print(f"Guided mode: model={config['model']}, threshold={config['threshold']}")

    async def process(fn, index, sem):
        async with sem:
            try:
                if config["guided"]:
                    selected = predict_agents(fn, config["model"], threshold=config["threshold"])
                    print(f"  {fn['name']}: selected agents = {selected}")
                    graph = build_graph(selected_agents=selected)
                else:
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

    mode = "guided" if config["guided"] else "standard"
    print(f"Generating tests ({mode}, concurrency={concurrency})...")
    asyncio.run(run())

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"Done. Output: {output_dir}")


if __name__ == "__main__":
    main()
