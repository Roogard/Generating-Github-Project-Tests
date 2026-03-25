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


def write_fixed_function(fn, fixed_code, output_dir, index, iteration=None):
    ext = LANG_EXT.get(fn["language"], "txt")
    base = os.path.join(output_dir, "fixed_functions", f"{fn['name']}_{index}")
    if iteration is not None:
        folder = os.path.join(base, f"iteration_{iteration}")
    else:
        folder = base
    os.makedirs(folder, exist_ok=True)
    with open(os.path.join(folder, f"fixed_function.{ext}"), "w", encoding="utf-8") as f:
        f.write(fixed_code)


def replace_function_in_repo(fn, fixed_code, repo_clone_dir):
    file_path = os.path.join(repo_clone_dir, fn["file_path"])
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start = fn["start_line"] - 1
    end = fn["end_line"]

    # detect original indentation from the first line of the function
    if start < len(lines):
        original_first = lines[start]
        indent = len(original_first) - len(original_first.lstrip())
        indent_str = original_first[:indent]
    else:
        indent_str = ""

    # re-indent the fixed code to match the original
    fixed_lines = fixed_code.splitlines(True)
    if fixed_lines:
        # detect indentation of the fixed code's first line
        first_fixed = fixed_lines[0]
        fixed_indent = len(first_fixed) - len(first_fixed.lstrip())
        reindented = []
        for line in fixed_lines:
            if line.strip() == "":
                reindented.append("\n")
            else:
                stripped = line[min(fixed_indent, len(line) - len(line.lstrip())):]
                reindented.append(indent_str + stripped)
        fixed_lines = reindented

    # ensure last line ends with newline
    if fixed_lines and not fixed_lines[-1].endswith("\n"):
        fixed_lines[-1] += "\n"

    new_lines = lines[:start] + fixed_lines + lines[end:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    new_end = start + len(fixed_lines)
    return new_end


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
