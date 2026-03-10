#!/usr/bin/env bash
set -e

OUTPUT_DIR="./outputs/algorithms"

# Parse args
while [[ $# -gt 0 ]]; do
    case "$1" in
        --output) OUTPUT_DIR="$2"; shift 2 ;;
        --output=*) OUTPUT_DIR="${1#*=}"; shift ;;
        *) echo "Usage: bash run_tests.sh [--output <path>]"; exit 1 ;;
    esac
done

# Check Python
if ! command -v python &>/dev/null; then
    echo "Error: python not found. Install Python 3.11+ first."
    exit 1
fi

# Install dependencies if missing
python -c "import pytest" 2>/dev/null || pip install pytest
python -c "import pytest_jsonreport" 2>/dev/null || pip install pytest-json-report

echo "============================================"
echo "  Running generated tests"
echo "  Output dir: $OUTPUT_DIR"
echo "============================================"

python -m src.runner --output "$OUTPUT_DIR"

echo ""
echo "Results saved to: $OUTPUT_DIR/results.json"
