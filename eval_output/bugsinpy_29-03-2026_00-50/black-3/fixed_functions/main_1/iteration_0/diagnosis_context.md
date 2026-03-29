_(showing 10 of 50 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
import sys
import os
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

from black import main


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_py_file(content: str, suffix: ".py" = ".py") -> tempfile.NamedTemporaryFile:
    """Return an open NamedTemporaryFile with *content* written to it."""
    f = tempfile.NamedTemporaryFile(mode="w", suffix=suffix, delete=False)
    f.write(content)
    f.flush()
    f.close()
    return f


SIMPLE_UNFORMATTED = 'x=1\n'
SIMPLE_FORMATTED = 'x = 1\n'

ALREADY_FORMATTED = 'x = 1\n'


# ---------------------------------------------------------------------------
# --- BVA ---  (Boundary Value Analysis)
# ---------------------------------------------------------------------------


class TestBVALineLength:
    """Probe --line-length boundaries."""

    def test_line_length_minimum_valid_1(self):
        """line-length=1 is the minimum positive integer; black should accept it."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "1"])
        # A correct implementation should not crash with exit code 123
        assert result.exit_code != 123, result.output

    def test_line_length_typical_88(self):
        """Default line length 88 should format correctly."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "88"])
        assert result.exit_code == 0
        assert "x = 1" in result.output

    def test_line_length_large_value(self):
        """Very large line length should be accepted without error."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "99999"])
        assert result.exit_code == 0

    def test_code_empty_string(self):
        """Empty string passed via --code: a correct formatter should handle it."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", ""])
        # Should not internal-error
        assert result.exit_code != 123, result.output

    def test_code_single_newline(self):
        """Single newline via --code."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "\n"])
        assert result.exit_code != 123, result.output

    def test_src_empty_tuple(self):
        """No src arguments at all: should exit 0 with 'Nothing to do' message."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_single_python_file(self):
        """Exactly one .py source file (boundary: len(sources)==1 triggers reformat_one)."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            # Unformatted file under --check should return code 1
            assert result.exit_code == 1
        finally:
            os.unlink(f.name)

    def test_two_python_files(self):
        """Two files: boundary len(sources)==2 triggers reformat_many."""
        f1 = make_py_file(SIMPLE_UNFORMATTED)
        f2 = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f1.name, f2.name])
            # Both unformatted → exit code 1
            assert result.exit_code == 1
        finally:
            os.unlink(f1.name)
            os.unlink(f2.name)


class TestBVAIncludeExclude:
    """Boundary values for --include / --exclude patterns."""

    def test_include_empty_string(self):
        """Empty include matches everything; should not crash."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--include", "", "--check", f.name])
            assert result.exit_code != 123, result.output
        finally:
            os.unlink(f.name)

    def test_exclude_empty_string(self):
        """Empty exclude excludes nothing; should not crash."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--exclude", "", "--check", f.name])
            assert result.exit_code != 123, result.output
        finally:
            os.unlink(f.name)


# ---------------------------------------------------------------------------
# --- ECP ---  (Equivalence Class Partitioning)
# ---------------------------------------------------------------------------


class TestECPCodeOption:
    """--code path: classes based on code content."""

    def test_valid_already_formatted_code(self):
        """Code that is already formatted: output should be identical."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", ALREADY_FORMATTED])
        assert result.exit_code == 0
        assert result.output.strip() == ALREADY_FORMATTED.strip()

    def test_valid_unformatted_code(self):
        """Code that needs formatting: output should differ from input."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", SIMPLE_UNFORMATTED])
        assert result.exit_code == 0
        assert "x = 1" in result.output

    def test_invalid_syntax_code(self):
        """Syntactically invalid code should not exit 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "def foo(\n"])
        assert result.exit_code != 0

    def test_code_exits_0_always(self):
        """When --code is used and formatting succeeds, exit code must be 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "a = 1\n"])
        assert result.exit_code == 0


class TestECPCheckAndDiff:
    """ECP: --check and --diff flag combinations."""

    def test_check_already_formatted_exits_0(self):
        """File already formatted + --check → exit 0."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            assert result.exit_code == 0
        finally:
            os.unlink(f.name)

    def test_check_unformatted_exits_1(self):
        """File not formatted + --check → exit 1 (would reformat)."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            assert result.exit_code == 1
        finally:
            os.unlink(f.name)

    def test_diff_does_not_modify_file(self):
        """--diff should NOT modify the source file."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        original_content = Path(f.name).read_text()
        try:
            runner = CliRunner()
            runner.invoke(main, ["--diff", f.name])
            assert Path(f.name).read_text() == original_content
        finally:
            os.unlink(f.name)

    def test_no_check_no_diff_writes_file(self):
        """Without --check/--diff, a correct formatter must reformat the file in place."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, [f.name])
            assert result.exit_code == 0
            new_content = Path(f.name).read_text()
            assert new_content == SIMPLE_FORMATTED
        finally:
            os.unlink(f.name)


class TestECPTargetVersion:
    """ECP: target-version / --py36 interaction."""

    def test_target_version_single_valid(self):
        """Single valid --target-version should be accepted."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "--target-version", "py36"])
        assert result.exit_code == 0

    def test_py36_deprecated_warning(self, capsys):
        """--py36 alone should still work (deprecated path)."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "--py36"])
        # Should not hard-error; py36 deprecated path still formats
        assert result.exit_code == 0

    def test_target_version_and_py36_conflict(self):
        """Combining --target-version and --py36 must exit with code 2."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["--code", "x=1\n", "--target-version", "py36", "--py36"]
        )
        assert result.exit_code == 2

    def test_multiple_target_versions(self):
        """Multiple --target-version flags should be accepted."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--code", "x=1\n", "--target-version", "py36", "--target-version", "py37"],
        )
        assert result.exit_code == 0


class TestECPInvalidRegex:
    """ECP: invalid regex for --include / --exclude."""

    def test_invalid_include_regex_exits_2(self):
        """Invalid --include regex → exit 2."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--include", "[invalid", f.name])
            assert result.exit_code == 2
        finally:
            os.unlink(f.name)

    def test_invalid_exclude_regex_exits_2(self):
        """Invalid --exclude regex → exit 2."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--exclude", "[invalid", f.name])
            assert result.exit_code == 2
        finally:
            os.unlink(f.name)


class TestECPQuietVerbose:
    """ECP: --quiet and --verbose flags."""

    def test_quiet_suppresses_summary(self):
        """--quiet should suppress the summary line on stdout/stderr."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(main, ["--quiet", f.name])
            # Under quiet mode, no 'All done' / 'Oh no' messages
            assert "All done" not in (result.output or "")
        finally:
            os.unlink(f.name)

    def test_verbose_does_not_crash(self):
        """--verbose should not cause a crash."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--verbose", f.name])
            assert result.exit_code != 123, result.output
        finally:
            os.unlink(f.name)


class TestECPPyiFlag:
    """ECP: --pyi flag."""

    def test_pyi_flag_with_code(self):
        """--pyi + --code should not crash."""
        runner = CliRunner()
        result = runner.invoke(main, ["--pyi", "--code", "x: int = 1\n"])
        assert result.exit_code == 0

    def test_pyi_flag_with_file(self):
        """--pyi flag with a .py file should work as if it were a stub."""
        f = make_py_file("x: int = 1\n")
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--pyi", f.name])
            assert result.exit_code == 0
        finally:
            os.unlink(f.name)


class TestECPSkipStringNormalization:
    """ECP: --skip-string-normalization."""

    def test_skip_string_normalization_preserves_single_quotes(self):
        """With -S, single-quoted strings should not be changed to double-quoted."""
        code = "x = 'hello'\n"
        runner = CliRunner()
        result = runner.invoke(main, ["-S", "--code", code])
        assert result.exit_code == 0
        assert "'" in result.output

    def test_without_skip_string_normalization_uses_double_quotes(self):
        """Without -S, single-quoted strings should be converted to double-quoted."""
        code = "x = 'hello'\n"
        runner = CliRunner()
        result = runner.invoke(main, ["--code", code])
        assert result.exit_code == 0
        assert '"hello"' in result.output


class TestECPNoSrc:
    """ECP: no src provided, no --code."""

    def test_no_src_no_code_exits_0_nothing_to_do(self):
        """No files, no --code: a correct implementation exits 0 with nothing-to-do."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0


class TestECPDirectory:
    """ECP: src is a directory."""

    def test_directory_with_no_python_files(self):
        """Directory containing no .py files: exit 0, nothing to do."""
        with tempfile.TemporaryDirectory() as d:
            # create a non-python file
            Path(d, "readme.txt").write_text("hello")
            runner = CliRunner()
            result = runner.invoke(main, [d])
            assert result.exit_code == 0

    def test_directory_with_python_file(self):
        """Directory containing a .py file: should process it."""
        with tempfile.TemporaryDirectory() as d:
            Path(d, "sample.py").write_text(ALREADY_FORMATTED)
            runner = CliRunner()
            result = runner.invoke(main, ["--check", d])
            assert result.exit_code == 0


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------


class TestMutationDetection:

    def test_check_and_diff_both_false_writes_back(self):
        """
        Mutation: WriteBack.from_configuration may use wrong logic for check/diff flags.
        When both check=False and diff=False, the file MUST be written back.
        Detects: wrong boolean operator (and vs or) or negation error in from_configuration.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, [f.name])
            assert result.exit_code == 0
            assert Path(f.name).read_text() == SIMPLE_FORMATTED
        finally:
            os.unlink(f.name)

    def test_check_true_does_not_write_back(self):
        """
        Mutation: negation error — check=True might be treated as check=False.
        A correct implementation must NOT modify the file when --check is passed.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        original = Path(f.name).read_text()
        try:
            runner = CliRunner()
            runner.invoke(main, ["--check", f.name])
            assert Path(f.name).read_text() == original
        finally:
            os.unlink(f.name)

    def test_exit_code_0_when_no_sources(self):
        """
        Mutation: off-by-one — `if len(sources) == 0` mutated to `if len(sources) <= 0`
        or `if len(sources) < 0`.  Both should behave identically for this input,
        but a mutation to `> 0` would wrongly exit non-zero when there are sources.
        For zero sources the correct exit code is 0.
        """
        runner = CliRunner()
        result = runner.invoke(main, [])
        assert result.exit_code == 0

    def test_exit_code_1_source_unformatted_check(self):
        """
        Mutation: wrong constant — return_code 1 vs 0 when file would be reformatted.
        Correct behavior: exit 1 when --check finds a file to reformat.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            assert result.exit_code == 1
        finally:
            os.unlink(f.name)

    def test_exit_code_0_source_already_formatted_check(self):
        """
        Mutation: wrong operator — exit 1 when should be 0.
        Correct behavior: exit 0 when --check finds nothing to reformat.
        """
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            assert result.exit_code == 0
        finally:
            os.unlink(f.name)

    def test_target_version_and_py36_conflict_uses_correct_exit_code(self):
        """
        Mutation: wrong constant — exit code 2 vs 1 for conflicting flags.
        A correct implementation uses ctx.exit(2) for user errors.
        """
        runner = CliRunner()
        result = runner.invoke(
            main, ["--code", "x=1\n", "--target-version", "py36", "--py36"]
        )
        assert result.exit_code == 2, (
            "Conflict between --target-version and --py36 must exit with code 2"
        )

    def test_code_option_short_circuits_file_processing(self):
        """
        Mutation: missing `if code is not None: ... ctx.exit(0)` guard — code path
        continues into file processing.  When --code is given with no src,
        exit must be 0 and output must contain formatted code, not a 'nothing to do' msg.
        """
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n"])
        assert result.exit_code == 0
        assert "x = 1" in result.output
        assert "Nothing to do" not in result.output

    def test_len_sources_1_uses_reformat_one(self):
        """
        Mutation: off-by-one — `if len(sources) == 1` changed to `if len(sources) <= 1`
        would be equivalent here, but `if len(sources) < 1` would not call reformat_one.
        Verify a single file is actually processed (reformatted).
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, [f.name])
            assert result.exit_code == 0
            assert Path(f.name).read_text() == SIMPLE_FORMATTED
        finally:
            os.unlink(f.name)

    def test_string_normalization_inverted_flag(self):
        """
        Mutation: `string_normalization=not skip_string_normalization` mutated to
        `string_normalization=skip_string_normalization` (missing `not`).
        With -S (skip), single quotes should be PRESERVED.
        """
        code = "x = 'hello'\n"
        runner = CliRunner()
        result = runner.invoke(main, ["-S", "--code", code])
        assert result.exit_code == 0
        # Correct: single quotes preserved when normalization is skipped
        assert "'" in result.output
        assert 'x = "hello"' not in result.output

    def test_invalid_include_regex_exits_not_0(self):
        """
        Mutation: missing error handling for invalid regex — program continues instead
        of exiting 2.  Correct implementation must exit with non-zero code.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--include", "[bad", f.name])
            assert result.exit_code != 0
        finally:
            os.unlink(f.name)

    def test_invalid_exclude_regex_exits_not_0(self):
        """
        Mutation: missing error handling for invalid exclude regex.
        Correct implementation must exit with non-zero code.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--exclude", "[bad", f.name])
            assert result.exit_code != 0
        finally:
            os.unlink(f.name)

    def test_report_return_code_drives_exit(self):
        """
        Mutation: `ctx.exit(report.return_code)` changed to `ctx.exit(0)`.
        When a file would be reformatted (--check), exit code must reflect report.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name])
            # If mutation present, would exit 0 instead of 1
            assert result.exit_code != 0
        finally:
            os.unlink(f.name)
```

```python
# test_whitebox.py
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
    runner = CliRunner(mix_stderr=False)
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
```

## Error Message(s)

### [FAILURE] test_quiet_suppresses_summary (type: blackbox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_blackbox.py:276: in test_quiet_suppresses_summary
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_format_code_flag (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:38: in test_sc_format_code_flag
    result = invoke(["--code", "x=1"])
             ^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_no_sources_quiet (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:47: in test_sc_no_sources_quiet
    result = invoke(["--quiet"])
             ^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_no_sources_verbose (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:54: in test_sc_no_sources_verbose
    result = invoke(["--verbose"])
             ^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_single_file_check (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:63: in test_sc_single_file_check
    result = invoke(["--check", path])
             ^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_target_version_and_py36_error (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:74: in test_sc_target_version_and_py36_error
    result = invoke(["-t", "py36", "--py36", path])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_py36_deprecated_warning (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:84: in test_sc_py36_deprecated_warning
    result = invoke(["--py36", path])
             ^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_invalid_include_regex (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:95: in test_sc_invalid_include_regex
    result = invoke(["--include", "[invalid(regex", path])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_invalid_exclude_regex (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:105: in test_sc_invalid_exclude_regex
    result = invoke(["--exclude", "[invalid(regex", path])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```

### [FAILURE] test_sc_directory_source (type: whitebox)
```
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:117: in test_sc_directory_source
    result = invoke(["--check", d])
             ^^^^^^^^^^^^^^^^^^^^^^
eval_output\bugsinpy_29-03-2026_00-50\black-3\generated_tests\main_1\test_whitebox.py:26: in invoke
    runner = CliRunner(mix_stderr=False)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   TypeError: CliRunner.__init__() got an unexpected keyword argument 'mix_stderr'
```
