#!/usr/bin/env bash
set -e

REPO_DIR="C:\Users\roota\AppData\Local\Temp\tmp71qptlcs"
TEST_DIR="C:\Users\roota\OneDrive\Desktop\Projects\Generating-Github-Project-Tests\eval_output\algorithms\generated_tests"

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
