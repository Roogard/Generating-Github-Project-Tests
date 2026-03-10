import json
import os

LANG_EXT = {"python": "py"}


def write_meta(repo_url, output_dir):
    repo_name = repo_url.rstrip("/").split("/")[-1].replace(".git", "")
    os.makedirs(output_dir, exist_ok=True)
    with open(os.path.join(output_dir, "meta.json"), "w", encoding="utf-8") as f:
        json.dump({"repo_url": repo_url, "repo_name": repo_name}, f, indent=2)


def write_function(fn, output_dir, index):
    ext = LANG_EXT.get(fn["language"], "txt")
    folder = os.path.join(output_dir, "functions", f"{fn['name']}_{index}")
    os.makedirs(folder, exist_ok=True)

    with open(os.path.join(folder, f"function.{ext}"), "w", encoding="utf-8") as f:
        f.write(fn["source"])


def write_tests(fn, test_results, output_dir, index):
    ext = LANG_EXT.get(fn["language"], "txt")
    folder = os.path.join(output_dir, "test_cases", f"{fn['name']}_{index}")
    os.makedirs(folder, exist_ok=True)

    for test_type in ["statement", "block", "condition", "path", "bva", "ecp", "mutation"]:
        with open(os.path.join(folder, f"test_{test_type}.{ext}"), "w", encoding="utf-8") as f:
            f.write(test_results.get(f"{test_type}_tests", ""))
