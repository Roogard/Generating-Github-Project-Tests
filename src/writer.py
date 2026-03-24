import json
import os
import stat

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
        content = test_results.get(f"{test_type}_tests", "")
        if not content.strip():
            continue
        with open(os.path.join(folder, f"test_{test_type}.{ext}"), "w", encoding="utf-8") as f:
            f.write(content)


WHITEBOX_TYPES = ["statement", "block", "condition", "path"]
BLACKBOX_TYPES = ["bva", "ecp", "mutation"]


def write_generated_tests(fn, generated_tests, output_dir, index):
    ext = LANG_EXT.get(fn["language"], "txt")
    folder = os.path.join(output_dir, "generated_tests", f"{fn['name']}_{index}")
    os.makedirs(folder, exist_ok=True)

    for test_type, code in generated_tests.items():
        if not code.strip():
            continue
        if test_type in WHITEBOX_TYPES:
            fname = f"test_whitebox_{test_type}.{ext}"
        elif test_type in BLACKBOX_TYPES:
            fname = f"test_blackbox_{test_type}.{ext}"
        else:
            fname = f"test_{test_type}.{ext}"
        with open(os.path.join(folder, fname), "w", encoding="utf-8") as f:
            f.write(code)


def generate_automation(output_dir, repo_clone_dir):
    automation_dir = os.path.join(output_dir, "automation")
    os.makedirs(automation_dir, exist_ok=True)

    script_path = os.path.join(automation_dir, "run_tests.sh")
    repo_abs = os.path.abspath(repo_clone_dir)
    test_dir = os.path.join(os.path.abspath(output_dir), "generated_tests")

    content = f"""#!/usr/bin/env bash
set -e

REPO_DIR="{repo_abs}"
TEST_DIR="{test_dir}"

export PYTHONPATH="$REPO_DIR:$PYTHONPATH"

echo "Running all generated tests..."
echo "Repo: $REPO_DIR"
echo ""

for test_file in "$TEST_DIR"/*/test_*.py; do
    if [ ! -f "$test_file" ]; then
        continue
    fi

    fn_dir=$(basename "$(dirname "$test_file")")
    test_name=$(basename "$test_file")
    echo "--- $fn_dir / $test_name ---"

    python -m pytest "$test_file" -q --tb=short --no-header || true
    echo ""
done

echo "Done."
"""
    with open(script_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(content)

    os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)
