import argparse
import difflib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from src.config import load_config
from src.extractor import clone_repo_at_commit, extract_functions
from src.agents import call_agent
from src.runner import run_single_test
from src.writer import write_meta, write_function, write_generated_tests
from src.reporter import parse_failures
from src.main import WHITEBOX_TYPES, BLACKBOX_TYPES, run_one_shot_fix


def load_swebench_instances(split="test", limit=0):
    from datasets import load_dataset
    ds = load_dataset("princeton-nlp/SWE-bench_Lite", split=split)
    instances = list(ds)
    if limit > 0:
        instances = instances[:limit]
    return instances


def parse_patch_files(patch_text):
    """Extract (file_path, changed_line_ranges) from a unified diff."""
    files = {}
    current_file = None
    for line in patch_text.splitlines():
        # match diff header like: +++ b/path/to/file.py
        m = re.match(r"^\+\+\+ b/(.+)$", line)
        if m:
            current_file = m.group(1)
            if current_file not in files:
                files[current_file] = []
            continue
        # match hunk header like: @@ -10,5 +10,7 @@
        m = re.match(r"^@@ -(\d+),?\d* \+(\d+),?\d* @@", line)
        if m and current_file:
            old_start = int(m.group(1))
            new_start = int(m.group(2))
            files[current_file].append((old_start, new_start))
    return files


def functions_from_patch(patch_text, repo_path):
    """Find functions that overlap with the gold patch changes."""
    patch_files = parse_patch_files(patch_text)
    if not patch_files:
        return []

    all_functions = extract_functions(repo_path)

    targets = []
    for fn in all_functions:
        fn_rel = fn["file_path"].replace("\\", "/")
        for patch_file, hunks in patch_files.items():
            patch_file_norm = patch_file.replace("\\", "/")
            if fn_rel != patch_file_norm and not fn_rel.endswith("/" + patch_file_norm):
                continue
            # check if any hunk overlaps with this function's line range
            for old_start, _ in hunks:
                if fn["start_line"] <= old_start <= fn["end_line"]:
                    targets.append(fn)
                    break
            else:
                continue
            break

    return targets


def generate_patch(original_content, fixed_content, file_path):
    """Produce a unified diff string."""
    orig_lines = original_content.splitlines(True)
    fixed_lines = fixed_content.splitlines(True)
    diff = difflib.unified_diff(
        orig_lines, fixed_lines,
        fromfile="a/" + file_path, tofile="b/" + file_path,
    )
    return "".join(diff)


def run_swebench_instance(instance, config, output_dir):
    instance_id = instance["instance_id"]
    repo_url = "https://github.com/" + instance["repo"]
    base_commit = instance["base_commit"]
    patch_text = instance["patch"]

    tmp = tempfile.mkdtemp()
    try:
        print(f"  Cloning {instance['repo']} @ {base_commit[:8]}...")
        clone_repo_at_commit(repo_url, tmp, base_commit)

        targets = functions_from_patch(patch_text, tmp)
        if not targets:
            print("  No target functions found in patch")
            return {"instance_id": instance_id, "model_patch": "", "status": "no_targets"}

        # check if multi-function
        if len(targets) > 1:
            print(f"  Multi-function patch ({len(targets)} functions) — processing all")

        all_types = WHITEBOX_TYPES + BLACKBOX_TYPES
        patches = []

        # save original file contents for diff generation
        original_files = {}
        for fn in targets:
            fpath = os.path.join(tmp, fn["file_path"])
            if fpath not in original_files:
                with open(fpath, "r", encoding="utf-8") as f:
                    original_files[fpath] = f.read()

        write_meta(repo_url, output_dir)

        for idx, fn in enumerate(targets):
            fn_key = f"{fn['name']}_{idx}"
            print(f"  Function {idx + 1}/{len(targets)}: {fn['name']}")

            write_function(fn, output_dir, idx)

            # generate tests
            generated = {}
            for test_type in all_types:
                code = call_agent(test_type, fn, config)
                if code and code.strip():
                    generated[test_type] = code
            write_generated_tests(fn, generated, output_dir, idx)
            print(f"    generated {len(generated)} test file(s)")

            # run tests
            test_outcomes = {}
            test_dir = os.path.join(output_dir, "generated_tests", fn_key)
            if os.path.isdir(test_dir):
                for fname in sorted(os.listdir(test_dir)):
                    if fname.startswith("test_") and fname.endswith(".py"):
                        test_file = os.path.join(test_dir, fname)
                        result = run_single_test(test_file, tmp, timeout=config["timeouts"]["test"])
                        test_outcomes[(fn_key, fname)] = result

            # one-shot fix
            failures = parse_failures(test_outcomes)
            fn_failures = [f for f in failures if f["function"] == fn_key]
            if fn_failures:
                print(f"    {len(fn_failures)} failure(s), running one-shot fix...")
                final_outcomes, attempted = run_one_shot_fix(
                    fn, fn_key, test_outcomes, tmp, output_dir, idx, config,
                )
                if attempted:
                    test_outcomes.update(final_outcomes)
                remaining = [f for f in parse_failures(test_outcomes) if f["function"] == fn_key and f["kind"] == "failure"]
                converged = attempted and not remaining
                print(f"    {'converged' if converged else 'did not converge'}")

        # generate patches by comparing original vs current file contents
        for fpath, original_content in original_files.items():
            with open(fpath, "r", encoding="utf-8") as f:
                current_content = f.read()
            if current_content != original_content:
                rel_path = os.path.relpath(fpath, tmp).replace("\\", "/")
                patch = generate_patch(original_content, current_content, rel_path)
                if patch:
                    patches.append(patch)

        model_patch = "\n".join(patches)
        status = "patched" if model_patch else "no_change"
        return {"instance_id": instance_id, "model_patch": model_patch, "status": status}

    except Exception as e:
        print(f"  ERROR: {e}")
        return {"instance_id": instance_id, "model_patch": "", "status": "error", "error": str(e)}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    load_dotenv()
    p = argparse.ArgumentParser(description="Run SWE-bench Lite evaluation")
    p.add_argument("--limit", type=int, default=5, help="Number of instances to evaluate (0 = all)")
    p.add_argument("--split", default="test", help="Dataset split")
    p.add_argument("--output", default="eval_output", help="Output directory")

    p.add_argument("--provider", default=None, help="LLM provider")
    p.add_argument("--model", default=None, help="LLM model name")
    args = p.parse_args()

    overrides = {}
    if args.provider:
        overrides.setdefault("llm", {})["provider"] = args.provider
    if args.model:
        overrides.setdefault("llm", {})["model"] = args.model
    config = load_config(overrides or None)

    print(f"Loading SWE-bench Lite ({args.split})...")
    instances = load_swebench_instances(args.split, args.limit)
    print(f"Loaded {len(instances)} instance(s)")

    timestamp = datetime.now().strftime("%d-%m-%Y_%H-%M")
    run_dir = os.path.join(args.output, f"swebench_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)

    predictions = []
    stats = {"total": len(instances), "attempted": 0, "patched": 0, "no_targets": 0, "errors": 0}

    for i, instance in enumerate(instances):
        instance_id = instance["instance_id"]
        print(f"\n--- Instance {i + 1}/{len(instances)}: {instance_id} ---")

        instance_output = os.path.join(run_dir, instance_id.replace("/", "__"))
        t0 = time.time()

        result = run_swebench_instance(instance, config, instance_output)
        elapsed = time.time() - t0

        predictions.append({
            "instance_id": result["instance_id"],
            "model_patch": result["model_patch"],
            "model_name_or_path": "ghtest",
        })

        status = result["status"]
        stats["attempted"] += 1
        if status == "patched":
            stats["patched"] += 1
        elif status == "no_targets":
            stats["no_targets"] += 1
        elif status == "error":
            stats["errors"] += 1

        print(f"  status={status}, time={elapsed:.1f}s")

    # write predictions jsonl
    predictions_path = os.path.join(run_dir, "predictions.jsonl")
    with open(predictions_path, "w", encoding="utf-8") as f:
        for pred in predictions:
            f.write(json.dumps(pred) + "\n")

    # write summary
    summary_path = os.path.join(run_dir, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(stats, f, indent=2)

    print("\n" + "=" * 60)
    print("SWE-BENCH EVALUATION SUMMARY")
    print("=" * 60)
    print(f"  Instances:   {stats['total']}")
    print(f"  Attempted:   {stats['attempted']}")
    print(f"  Patched:     {stats['patched']}")
    print(f"  No targets:  {stats['no_targets']}")
    print(f"  Errors:      {stats['errors']}")
    print(f"\nPredictions: {predictions_path}")
    print(f"Summary:     {summary_path}")


if __name__ == "__main__":
    main()
