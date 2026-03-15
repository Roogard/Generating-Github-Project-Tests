"""Build a diverse training database from multiple repos.
Usage: uv run python scripts/build_training_db.py --per-repo 10 --dry-run
"""
import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.extractor import clone_repo, extract_functions
from src.main import _fn_complexity, _classify_complexity, _stratified_sample


def parse_args():
    p = argparse.ArgumentParser(description="Build training database from multiple repos")
    p.add_argument("--repos", default="./data/repos.json", help="JSON file listing repos to train on")
    p.add_argument("--per-repo", type=int, default=10, dest="per_repo", help="Functions to sample per repo")
    p.add_argument("--min-lines", type=int, default=5, dest="min_lines", help="Skip functions shorter than N lines")
    p.add_argument("--max-lines", type=int, default=80, dest="max_lines", help="Skip functions longer than N lines")
    p.add_argument("--min-branches", type=int, default=1, dest="min_branches", help="Skip functions with fewer than N branches")
    p.add_argument("--dry-run", action="store_true", dest="dry_run", help="Preview without running training")
    return vars(p.parse_args())


def get_existing_hashes():
    try:
        from src.memory import get_db, get_collection
        db = get_db()
        coll = get_collection(db)
        if coll.count() == 0:
            return set()
        results = coll.get(include=["documents"])
        hashes = set()
        for doc in results["documents"]:
            h = hashlib.sha256(doc.encode("utf-8")).hexdigest()[:16]
            hashes.add(h)
        return hashes
    except Exception:
        return set()


def main():
    config = parse_args()

    with open(config["repos"], "r", encoding="utf-8") as f:
        repos = json.load(f)

    print("=" * 60)
    print("  TRAINING DATABASE BUILDER")
    print("=" * 60)
    print(f"  Repos: {len(repos)}")
    print(f"  Per repo: {config['per_repo']} (stratified)")
    print(f"  Lines filter: {config['min_lines']}-{config['max_lines']}, min branches: {config['min_branches']}")
    print(f"  Dry run: {config['dry_run']}")
    print()

    existing_hashes = get_existing_hashes()
    print(f"  Existing memory records: {len(existing_hashes)}")
    print()

    all_selected = []

    for repo_info in repos:
        url = repo_info["url"]
        name = repo_info["name"]
        print(f"--- {name} ({url}) ---")

        tmp = tempfile.mkdtemp()
        try:
            clone_repo(url, tmp)
            functions = extract_functions(tmp)
            print(f"  Extracted: {len(functions)} functions")

            # Apply filters
            functions = [fn for fn in functions
                         if config["min_lines"] <= len(fn["source"].strip().splitlines()) <= config["max_lines"]]
            if config["min_branches"] > 0:
                functions = [fn for fn in functions if _fn_complexity(fn["source"])[1] >= config["min_branches"]]
            print(f"  After filters: {len(functions)}")

            # Skip already-trained functions
            new_functions = []
            for fn in functions:
                h = hashlib.sha256(fn["source"].encode("utf-8")).hexdigest()[:16]
                if h not in existing_hashes:
                    new_functions.append(fn)
            print(f"  New (not in memory): {len(new_functions)}")

            # Stratified sample
            selected = _stratified_sample(new_functions, config["per_repo"])

            # Print distribution
            buckets = {}
            for fn in selected:
                b = _classify_complexity(fn["source"])
                buckets[b] = buckets.get(b, 0) + 1
            print(f"  Selected: {len(selected)} — {buckets}")

            if selected:
                for fn in selected:
                    lines, branches = _fn_complexity(fn["source"])
                    bucket = _classify_complexity(fn["source"])
                    print(f"    {fn['name']:40s}  {lines:3d} lines  {branches:2d} branches  [{bucket}]")
                    fn["_repo_name"] = name
                    fn["_repo_url"] = url
                    fn["_tmp_dir"] = tmp

            all_selected.extend(selected)
        except Exception as e:
            print(f"  ERROR: {e}")
        finally:
            if not all_selected or config["dry_run"]:
                shutil.rmtree(tmp, ignore_errors=True)

        print()

    # Summary
    print("=" * 60)
    total_buckets = {}
    for fn in all_selected:
        b = _classify_complexity(fn["source"])
        total_buckets[b] = total_buckets.get(b, 0) + 1
    print(f"  Total selected: {len(all_selected)} functions")
    print(f"  Distribution: {total_buckets}")
    print("=" * 60)

    if config["dry_run"]:
        print("\n  DRY RUN — no training performed.")
        return

    if not all_selected:
        print("\n  No new functions to train on.")
        return

    # Run training pipeline on selected functions
    print(f"\n  Running training pipeline on {len(all_selected)} functions...")
    print("  This will take a while.\n")

    import subprocess
    # Group by repo for efficient processing
    by_repo = {}
    for fn in all_selected:
        repo_name = fn["_repo_name"]
        if repo_name not in by_repo:
            by_repo[repo_name] = {"url": fn["_repo_url"], "functions": []}
        by_repo[repo_name]["functions"].append(fn)

    for repo_name, info in by_repo.items():
        count = len(info["functions"])
        print(f"  Training {repo_name}: {count} functions...")
        result = subprocess.run(
            [sys.executable, "-m", "src.main",
             "--repo", info["url"],
             "--output", f"./training_output/{repo_name}",
             "--limit", str(count),
             "--min-lines", str(config["min_lines"]),
             "--max-lines", str(config["max_lines"]),
             "--min-branches", str(config["min_branches"]),
             "--stratify",
             "--mode", "train"],
        )
        if result.returncode != 0:
            print(f"  WARNING: {repo_name} training returned non-zero exit code")

    # Clean up temp dirs
    seen_tmps = set()
    for fn in all_selected:
        tmp = fn.get("_tmp_dir")
        if tmp and tmp not in seen_tmps:
            shutil.rmtree(tmp, ignore_errors=True)
            seen_tmps.add(tmp)

    # Final memory check
    print()
    print("=" * 60)
    try:
        from src.memory import get_db, get_collection, get_reflections
        db = get_db()
        coll = get_collection(db)
        refs = get_reflections(db)
        print(f"  Memory: {coll.count()} function records, {len(refs)} reflections")
    except Exception as e:
        print(f"  Memory check error: {e}")
    print("=" * 60)

    shutil.rmtree("./training_output", ignore_errors=True)
    print("\n  Done.")


if __name__ == "__main__":
    main()
