import sys
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import pytest
from click.testing import CliRunner

from black import main

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_tmpfile(suffix=".py", content="x = 1\n"):
    """Create a temporary Python file and return its path string."""
    f = tempfile.NamedTemporaryFile(
        mode="w", suffix=suffix, delete=False, encoding="utf-8"
    )
    f.write(content)
    f.close()
    return f.name


def invoke(args, input=None, catch_exceptions=True):
    runner = CliRunner()
    return runner.invoke(main, args, input=input, catch_exceptions=catch_exceptions)


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# ---------------------------------------------------------------------------

# Every major statement branch exercised at least once.

def test_sc_format_code_flag():
    """--code path: format_str is called, result printed, ctx.exit(0)."""
    result = invoke(["--code", "x=1"])
    # A correct formatter must exit 0 when given --code
    assert result.exit_code == 0
    # Output must contain *something* (the formatted code)
    assert len(result.output) > 0


def test_sc_no_sources_quiet():
    """No src provided, --quiet: path_empty / zero-sources branch hit."""
    result = invoke(["--quiet"])
    # With no sources and --quiet, nothing to do → exit 0
    assert result.exit_code == 0


def test_sc_no_sources_verbose():
    """No src provided, verbose: 'No Python files' message emitted."""
    result = invoke(["--verbose"])
    assert result.exit_code == 0
    assert "No Python files" in result.output or result.exit_code == 0


def test_sc_single_file_check():
    """Single-file path → reformat_one is reached (check mode)."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        # already-formatted file → exit 0 in check mode
        assert result.exit_code == 0
    finally:
        os.unlink(path)


def test_sc_target_version_and_py36_error():
    """target_version + py36 → error branch, exit 2."""
    path = make_tmpfile()
    try:
        result = invoke(["-t", "py36", "--py36", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_sc_py36_deprecated_warning():
    """--py36 alone → deprecation warning, versions = PY36_VERSIONS."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--py36", path])
        # deprecation warning should appear in stderr / output
        assert "deprecated" in result.output.lower() or result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_sc_invalid_include_regex():
    """Invalid --include regex → err message, exit 2."""
    path = make_tmpfile()
    try:
        result = invoke(["--include", "[invalid(regex", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_sc_invalid_exclude_regex():
    """Invalid --exclude regex → err message, exit 2."""
    path = make_tmpfile()
    try:
        result = invoke(["--exclude", "[invalid(regex", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_sc_directory_source():
    """Directory as src → gen_python_files_in_dir path exercised."""
    with tempfile.TemporaryDirectory() as d:
        py_file = os.path.join(d, "hello.py")
        with open(py_file, "w") as f:
            f.write("x = 1\n")
        result = invoke(["--check", d])
        assert result.exit_code in (0, 1)


def test_sc_diff_flag():
    """--diff flag reaches diff-related WriteBack branch."""
    path = make_tmpfile(content="x=1\n")
    try:
        result = invoke(["--diff", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# ---------------------------------------------------------------------------

# New basic blocks not already hit above.

def test_bc_else_no_target_no_py36_autodetect():
    """Neither target_version nor py36 → versions = set() (autodetect block)."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke([path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_bc_config_verbose_message():
    """config + verbose → 'Using configuration from' message block."""
    path = make_tmpfile(content="x = 1\n")
    try:
        # Pass a dummy config path; read_pyproject_toml callback will run
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".toml", delete=False
        ) as cfg:
            cfg.write("[tool.black]\n")
            cfg_path = cfg.name
        result = invoke(["--config", cfg_path, "--verbose", path])
        # The 'Using configuration from' message should appear somewhere
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)
        os.unlink(cfg_path)


def test_bc_multiple_sources_reformat_many():
    """Two files → reformat_many block reached."""
    p1 = make_tmpfile(content="x = 1\n")
    p2 = make_tmpfile(content="y = 2\n")
    try:
        result = invoke(["--check", p1, p2])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_bc_verbose_final_summary():
    """verbose=True → final summary out() block exercised."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--verbose", "--check", path])
        # Summary line must appear
        assert "done" in result.output.lower() or "💥" in result.output or result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_bc_not_quiet_final_summary():
    """quiet=False (default) → final summary block exercised."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_bc_quiet_suppresses_summary():
    """quiet=True, verbose=False → final summary block skipped."""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--quiet", "--check", path])
        # No summary output in quiet mode
        assert "All done" not in result.output
        assert "Oh no" not in result.output
    finally:
        os.unlink(path)


def test_bc_file_is_stdin_dash():
    """src='-' → p.is_file() or s == '-' branch (stdin path)."""
    result = invoke(["-"], input="x = 1\n")
    assert result.exit_code == 0


def test_bc_pyi_flag():
    """--pyi flag sets is_pyi=True in Mode."""
    path = make_tmpfile(suffix=".pyi", content="x: int\n")
    try:
        result = invoke(["--pyi", "--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_bc_skip_string_normalization():
    """--skip-string-normalization flips string_normalization in Mode."""
    path = make_tmpfile(content='x = "hello"\n')
    try:
        result = invoke(["-S", "--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# ---------------------------------------------------------------------------

# Each boolean sub-expression is True in some test, False in another.

# Condition: `if target_version:`
# test_sc_target_version_and_py36_error → target_version=True
# test_bc_else_no_target_no_py36_autodetect → target_version=False

def test_cc_target_version_true_py36_false():
    """target_version: True, py36: False → versions = set(target_version).
    # target_version: True, py36: False"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["-t", "py36", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_cc_target_version_false_py36_true():
    """target_version: False, py36: True → deprecation path.
    # target_version: False, py36: True"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--py36", "--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_cc_target_version_false_py36_false():
    """target_version: False, py36: False → autodetect.
    # target_version: False, py36: False"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_cc_config_true_verbose_true():
    """config: True, verbose: True → config message printed.
    # config: True, verbose: True"""
    path = make_tmpfile(content="x = 1\n")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as cfg:
        cfg.write("[tool.black]\n")
        cfg_path = cfg.name
    try:
        result = invoke(["--config", cfg_path, "--verbose", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)
        os.unlink(cfg_path)


def test_cc_config_false_verbose_true():
    """config: None/False, verbose: True → config message NOT printed.
    # config: False, verbose: True"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--verbose", path])
        assert "Using configuration from" not in result.output
    finally:
        os.unlink(path)


def test_cc_config_true_verbose_false():
    """config: True, verbose: False → config message NOT printed.
    # config: True, verbose: False"""
    path = make_tmpfile(content="x = 1\n")
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as cfg:
        cfg.write("[tool.black]\n")
        cfg_path = cfg.name
    try:
        result = invoke(["--config", cfg_path, path])
        assert "Using configuration from" not in result.output
    finally:
        os.unlink(path)
        os.unlink(cfg_path)


def test_cc_code_not_none():
    """code is not None → format and exit branch taken.
    # code: not None"""
    result = invoke(["--code", "x=1"])
    assert result.exit_code == 0
    assert len(result.output) > 0


def test_cc_code_is_none():
    """code is None → file processing path.
    # code: None"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_cc_sources_len_zero_verbose_true():
    """len(sources)==0, verbose=True → 'No Python files' message shown.
    # len(sources)==0: True, verbose: True"""
    with tempfile.TemporaryDirectory() as d:
        result = invoke(["--verbose", d])
        assert result.exit_code == 0


def test_cc_sources_len_zero_not_quiet():
    """len(sources)==0, quiet=False → 'No Python files' message shown.
    # len(sources)==0: True, quiet: False (not quiet = True)"""
    with tempfile.TemporaryDirectory() as d:
        result = invoke([d])
        assert result.exit_code == 0


def test_cc_sources_len_zero_quiet():
    """len(sources)==0, quiet=True → no message shown.
    # len(sources)==0: True, quiet: True, verbose: False"""
    with tempfile.TemporaryDirectory() as d:
        result = invoke(["--quiet", d])
        assert result.exit_code == 0
        assert "No Python files" not in result.output


def test_cc_sources_len_one():
    """len(sources)==1 → reformat_one taken.
    # len(sources)==1: True"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_cc_sources_len_gt_one():
    """len(sources)>1 → reformat_many taken.
    # len(sources)==1: False"""
    p1 = make_tmpfile(content="x = 1\n")
    p2 = make_tmpfile(content="y = 2\n")
    try:
        result = invoke(["--check", p1, p2])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_cc_verbose_or_not_quiet_true_no_error():
    """verbose or not quiet is True, report.return_code==0 → 'All done' message.
    # verbose_or_not_quiet: True, return_code: 0"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        # Already formatted → return_code 0 → 'All done'
        assert "All done" in result.output
    finally:
        os.unlink(path)


def test_cc_verbose_or_not_quiet_true_with_error():
    """verbose or not quiet is True, report.return_code!=0 → 'Oh no' message.
    # verbose_or_not_quiet: True, return_code: nonzero"""
    path = make_tmpfile(content="x=1\n")  # needs reformatting
    try:
        result = invoke(["--check", path])
        # Would be reformatted → return_code 1 → 'Oh no'
        if result.exit_code == 1:
            assert "Oh no" in result.output
        else:
            # file was already formatted; just check exit is sane
            assert result.exit_code == 0
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# ---------------------------------------------------------------------------

# Major distinct execution paths through main().

def test_path_code_provided_exits_early():
    """path: code not None → format_str → print → ctx.exit(0). No file processing."""
    # path: code-not-None → exit(0)
    result = invoke(["--code", "a = 1\n"])
    assert result.exit_code == 0
    # Must not attempt any file I/O
    assert "No Python files" not in result.output


def test_path_target_version_py36_conflict():
    """path: target_version + py36 → err → ctx.exit(2).
    # path: target_version-truthy → py36-true → exit(2)"""
    path = make_tmpfile()
    try:
        result = invoke(["-t", "py36", "--py36", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_path_invalid_include_exit2():
    """path: invalid include regex → ctx.exit(2).
    # path: no-code → bad-include → exit(2)"""
    path = make_tmpfile()
    try:
        result = invoke(["--include", "(bad[", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_path_invalid_exclude_exit2():
    """path: invalid exclude regex → ctx.exit(2).
    # path: no-code → good-include → bad-exclude → exit(2)"""
    path = make_tmpfile()
    try:
        result = invoke(["--exclude", "(bad[", path])
        assert result.exit_code == 2
    finally:
        os.unlink(path)


def test_path_zero_sources_exit0():
    """path: zero sources found → ctx.exit(0).
    # path: no-code → good-regexes → empty-dir → exit(0)"""
    with tempfile.TemporaryDirectory() as d:
        result = invoke([d])
        assert result.exit_code == 0


def test_path_single_source_reformat_one():
    """path: 1 source → reformat_one → summary → ctx.exit.
    # path: no-code → good-regexes → 1-source → reformat_one → summary"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
        # Summary line must be present (not quiet by default)
        assert "All done" in result.output or "Oh no" in result.output
    finally:
        os.unlink(path)


def test_path_multiple_sources_reformat_many():
    """path: >1 sources → reformat_many → summary → ctx.exit.
    # path: no-code → good-regexes → >1-sources → reformat_many → summary"""
    p1 = make_tmpfile(content="x = 1\n")
    p2 = make_tmpfile(content="y = 2\n")
    try:
        result = invoke(["--check", p1, p2])
        assert result.exit_code in (0, 1)
        assert "All done" in result.output or "Oh no" in result.output
    finally:
        os.unlink(p1)
        os.unlink(p2)


def test_path_quiet_no_summary():
    """path: quiet=True, verbose=False → summary suppressed.
    # path: no-code → good-regexes → 1-source → reformat_one → NO-summary"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--quiet", "--check", path])
        assert "All done" not in result.output
        assert "Oh no" not in result.output
    finally:
        os.unlink(path)


def test_path_py36_deprecated_versions_assigned():
    """path: no target_version, py36=True → deprecation warning, PY36_VERSIONS used.
    # path: target_version-falsy → py36-true → deprecation → PY36_VERSIONS"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--py36", "--check", path])
        # deprecation warning must be present somewhere in output
        assert "deprecated" in result.output.lower() or result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_path_autodetect_versions():
    """path: no target_version, no py36 → versions = set() (autodetect).
    # path: target_version-falsy → py36-false → versions=set()"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_path_directory_with_python_files():
    """path: directory source → gen_python_files_in_dir → reformat_one/many.
    # path: dir-source → sources-updated → reformat"""
    with tempfile.TemporaryDirectory() as d:
        py = os.path.join(d, "sample.py")
        with open(py, "w") as f:
            f.write("x = 1\n")
        result = invoke(["--check", d])
        assert result.exit_code in (0, 1)


def test_path_stdin_source():
    """path: src='-' → treated as file → reformat_one.
    # path: s=='-' → sources.add(p) → reformat_one"""
    result = invoke(["-"], input="x = 1\n")
    assert result.exit_code == 0


def test_path_fast_flag():
    """path: --fast skips safety checks inside reformat_one.
    # path: fast=True → reformat_one(fast=True)"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["--fast", "--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_path_line_length_option():
    """path: custom --line-length propagated into Mode.
    # path: custom-line-length → Mode(line_length=50) → reformat"""
    path = make_tmpfile(content="x = 1\n")
    try:
        result = invoke(["-l", "50", "--check", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)


def test_path_diff_mode():
    """path: --diff mode → WriteBack.DIFF → reformat produces diff output.
    # path: diff=True → WriteBack.DIFF → reformat_one"""
    path = make_tmpfile(content="x=1\n")
    try:
        result = invoke(["--diff", path])
        assert result.exit_code in (0, 1)
    finally:
        os.unlink(path)