import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import subprocess
import tempfile


def measure_coverage(test_file, fn, repo_clone_dir, timeout=60):
    """Run coverage.py on a single test file and return coverage info for the target function.

    Returns a CoverageInfo dict:
        covered_lines    list[int]       lines executed within the function
        uncovered_lines  list[int]       lines NOT executed within the function
        coverage_pct     float           0.0–100.0
        fn_start_line    int
        fn_end_line      int
        fn_source_lines  dict[int, str]  uncovered line_num -> source text
        error            str | None      set if measurement failed
    """
    fn_abs_path = os.path.normpath(os.path.join(repo_clone_dir, fn["file_path"]))

    data_file = tempfile.mktemp(suffix=".coverage")
    json_file = tempfile.mktemp(suffix=".json")

    env = os.environ.copy()
    env["PYTHONPATH"] = repo_clone_dir + os.pathsep + env.get("PYTHONPATH", "")

    try:
        # Step 1: run coverage
        subprocess.run(
            [
                sys.executable, "-m", "coverage", "run",
                f"--data-file={data_file}",
                f"--include={fn_abs_path}",
                "--branch",
                "-m", "pytest", test_file,
                "-q", "--no-header", "--tb=no",
            ],
            capture_output=True, text=True, env=env, timeout=timeout,
        )

        # Step 2: export to JSON
        result = subprocess.run(
            [
                sys.executable, "-m", "coverage", "json",
                f"--data-file={data_file}",
                "-o", json_file,
            ],
            capture_output=True, text=True, env=env, timeout=30,
        )

        if result.returncode != 0 or not os.path.exists(json_file):
            return _error_result(fn, f"coverage json failed: {result.stderr.strip()}")

        with open(json_file, encoding="utf-8") as f:
            data = json.load(f)

        file_entry = _find_file_entry(data, fn_abs_path)
        if file_entry is None:
            return _error_result(fn, f"source file not found in coverage report: {fn_abs_path}")

        start = fn["start_line"]
        end = fn["end_line"]

        covered = [l for l in file_entry.get("executed_lines", []) if start <= l <= end]
        uncovered = [l for l in file_entry.get("missing_lines", []) if start <= l <= end]

        total = len(covered) + len(uncovered)
        pct = (len(covered) / total * 100.0) if total > 0 else 100.0

        source_lines = _build_source_lines(fn, uncovered)

        return {
            "covered_lines": sorted(covered),
            "uncovered_lines": sorted(uncovered),
            "coverage_pct": round(pct, 1),
            "fn_start_line": start,
            "fn_end_line": end,
            "fn_source_lines": source_lines,
            "error": None,
        }

    except subprocess.TimeoutExpired:
        return _error_result(fn, f"coverage timed out after {timeout}s")
    except Exception as e:
        return _error_result(fn, str(e))
    finally:
        for path in (data_file, json_file):
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass


def _find_file_entry(coverage_data, fn_abs_path):
    """Find the coverage file entry matching fn_abs_path, normalizing separators."""
    needle = os.path.normcase(fn_abs_path)
    for key, entry in coverage_data.get("files", {}).items():
        if os.path.normcase(os.path.normpath(key)) == needle:
            return entry
    return None


def _build_source_lines(fn, uncovered_line_nums):
    """Map uncovered line numbers to their source text.

    fn["source"] is the raw function source starting at fn["start_line"].
    """
    if not uncovered_line_nums:
        return {}

    lines = fn["source"].splitlines()
    start = fn["start_line"]
    result = {}
    for lineno in uncovered_line_nums:
        idx = lineno - start
        if 0 <= idx < len(lines):
            result[lineno] = lines[idx]
    return result


def _error_result(fn, message):
    return {
        "covered_lines": [],
        "uncovered_lines": [],
        "coverage_pct": 0.0,
        "fn_start_line": fn.get("start_line", 0),
        "fn_end_line": fn.get("end_line", 0),
        "fn_source_lines": {},
        "error": message,
    }
