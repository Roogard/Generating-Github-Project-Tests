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
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "1"], prog_name="black")
        # A correct implementation should not crash with exit code 123
        assert result.exit_code != 123, result.output

    def test_line_length_typical_88(self):
        """Default line length 88 should format correctly."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "88"], prog_name="black")
        assert result.exit_code == 0
        assert "x = 1" in result.output

    def test_line_length_large_value(self):
        """Very large line length should be accepted without error."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "-l", "99999"], prog_name="black")
        assert result.exit_code == 0

    def test_code_empty_string(self):
        """Empty string passed via --code: a correct formatter should handle it."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", ""], prog_name="black")
        # Should not internal-error
        assert result.exit_code != 123, result.output

    def test_code_single_newline(self):
        """Single newline via --code."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "\n"], prog_name="black")
        assert result.exit_code != 123, result.output

    def test_src_empty_tuple(self):
        """No src arguments at all: should exit 0 with 'Nothing to do' message."""
        runner = CliRunner()
        result = runner.invoke(main, [], prog_name="black")
        assert result.exit_code == 0

    def test_single_python_file(self):
        """Exactly one .py source file (boundary: len(sources)==1 triggers reformat_one)."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
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
            result = runner.invoke(main, ["--check", f1.name, f2.name], prog_name="black")
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
            result = runner.invoke(main, ["--include", "", "--check", f.name], prog_name="black")
            assert result.exit_code != 123, result.output
        finally:
            os.unlink(f.name)

    def test_exclude_empty_string(self):
        """Empty exclude excludes nothing; should not crash."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--exclude", "", "--check", f.name], prog_name="black")
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
        result = runner.invoke(main, ["--code", ALREADY_FORMATTED], prog_name="black")
        assert result.exit_code == 0
        assert result.output.strip() == ALREADY_FORMATTED.strip()

    def test_valid_unformatted_code(self):
        """Code that needs formatting: output should differ from input."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", SIMPLE_UNFORMATTED], prog_name="black")
        assert result.exit_code == 0
        assert "x = 1" in result.output

    def test_invalid_syntax_code(self):
        """Syntactically invalid code should not exit 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "def foo(\n"], prog_name="black")
        assert result.exit_code != 0

    def test_code_exits_0_always(self):
        """When --code is used and formatting succeeds, exit code must be 0."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "a = 1\n"], prog_name="black")
        assert result.exit_code == 0


class TestECPCheckAndDiff:
    """ECP: --check and --diff flag combinations."""

    def test_check_already_formatted_exits_0(self):
        """File already formatted + --check → exit 0."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
            assert result.exit_code == 0
        finally:
            os.unlink(f.name)

    def test_check_unformatted_exits_1(self):
        """File not formatted + --check → exit 1 (would reformat)."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
            assert result.exit_code == 1
        finally:
            os.unlink(f.name)

    def test_diff_does_not_modify_file(self):
        """--diff should NOT modify the source file."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        original_content = Path(f.name).read_text()
        try:
            runner = CliRunner()
            runner.invoke(main, ["--diff", f.name], prog_name="black")
            assert Path(f.name).read_text() == original_content
        finally:
            os.unlink(f.name)

    def test_no_check_no_diff_writes_file(self):
        """Without --check/--diff, a correct formatter must reformat the file in place."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, [f.name], prog_name="black")
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
        result = runner.invoke(main, ["--code", "x=1\n", "--target-version", "py36"], prog_name="black")
        assert result.exit_code == 0

    def test_py36_deprecated_warning(self, capsys):
        """--py36 alone should still work (deprecated path)."""
        runner = CliRunner()
        result = runner.invoke(main, ["--code", "x=1\n", "--py36"], prog_name="black")
        # Should not hard-error; py36 deprecated path still formats
        assert result.exit_code == 0

    def test_target_version_and_py36_conflict(self):
        """Combining --target-version and --py36 must exit with code 2."""
        runner = CliRunner()
        result = runner.invoke(
            main, ["--code", "x=1\n", "--target-version", "py36", "--py36"],
            prog_name="black"
        )
        assert result.exit_code == 2

    def test_multiple_target_versions(self):
        """Multiple --target-version flags should be accepted."""
        runner = CliRunner()
        result = runner.invoke(
            main,
            ["--code", "x=1\n", "--target-version", "py36", "--target-version", "py37"],
            prog_name="black"
        )
        assert result.exit_code == 0


class TestECPInvalidRegex:
    """ECP: invalid regex for --include / --exclude."""

    def test_invalid_include_regex_exits_2(self):
        """Invalid --include regex → exit 2."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--include", "[invalid", f.name], prog_name="black")
            assert result.exit_code == 2
        finally:
            os.unlink(f.name)

    def test_invalid_exclude_regex_exits_2(self):
        """Invalid --exclude regex → exit 2."""
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--exclude", "[invalid", f.name], prog_name="black")
            assert result.exit_code == 2
        finally:
            os.unlink(f.name)


class TestECPQuietVerbose:
    """ECP: --quiet and --verbose flags."""

    def test_quiet_suppresses_summary(self):
        """--quiet should suppress the summary line on stdout/stderr."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--quiet", f.name], prog_name="black")
            # Under quiet mode, no 'All done' / 'Oh no' messages
            assert "All done" not in (result.output or "")
        finally:
            os.unlink(f.name)

    def test_verbose_does_not_crash(self):
        """--verbose should not cause a crash."""
        f = make_py_file(ALREADY_FORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--verbose", f.name], prog_name="black")
            assert result.exit_code != 123, result.output
        finally:
            os.unlink(f.name)


class TestECPPyiFlag:
    """ECP: --pyi flag."""

    def test_pyi_flag_with_code(self):
        """--pyi + --code should not crash."""
        runner = CliRunner()
        result = runner.invoke(main, ["--pyi", "--code", "x: int = 1\n"], prog_name="black")
        assert result.exit_code == 0

    def test_pyi_flag_with_file(self):
        """--pyi flag with a .py file should work as if it were a stub."""
        f = make_py_file("x: int = 1\n")
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--pyi", f.name], prog_name="black")
            assert result.exit_code == 0
        finally:
            os.unlink(f.name)


class TestECPSkipStringNormalization:
    """ECP: --skip-string-normalization."""

    def test_skip_string_normalization_preserves_single_quotes(self):
        """With -S, single-quoted strings should not be changed to double-quoted."""
        code = "x = 'hello'\n"
        runner = CliRunner()
        result = runner.invoke(main, ["-S", "--code", code], prog_name="black")
        assert result.exit_code == 0
        assert "'" in result.output

    def test_without_skip_string_normalization_uses_double_quotes(self):
        """Without -S, single-quoted strings should be converted to double-quoted."""
        code = "x = 'hello'\n"
        runner = CliRunner()
        result = runner.invoke(main, ["--code", code], prog_name="black")
        assert result.exit_code == 0
        assert '"hello"' in result.output


class TestECPNoSrc:
    """ECP: no src provided, no --code."""

    def test_no_src_no_code_exits_0_nothing_to_do(self):
        """No files, no --code: a correct implementation exits 0 with nothing-to-do."""
        runner = CliRunner()
        result = runner.invoke(main, [], prog_name="black")
        assert result.exit_code == 0


class TestECPDirectory:
    """ECP: src is a directory."""

    def test_directory_with_no_python_files(self):
        """Directory containing no .py files: exit 0, nothing to do."""
        with tempfile.TemporaryDirectory() as d:
            # create a non-python file
            Path(d, "readme.txt").write_text("hello")
            runner = CliRunner()
            result = runner.invoke(main, [d], prog_name="black")
            assert result.exit_code == 0

    def test_directory_with_python_file(self):
        """Directory containing a .py file: should process it."""
        with tempfile.TemporaryDirectory() as d:
            Path(d, "sample.py").write_text(ALREADY_FORMATTED)
            runner = CliRunner()
            result = runner.invoke(main, ["--check", d], prog_name="black")
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
            result = runner.invoke(main, [f.name], prog_name="black")
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
            runner.invoke(main, ["--check", f.name], prog_name="black")
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
        result = runner.invoke(main, [], prog_name="black")
        assert result.exit_code == 0

    def test_exit_code_1_source_unformatted_check(self):
        """
        Mutation: wrong constant — return_code 1 vs 0 when file would be reformatted.
        Correct behavior: exit 1 when --check finds a file to reformat.
        """
        f = make_py_file(SIMPLE_UNFORMATTED)
        try:
            runner = CliRunner()
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
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
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
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
            main, ["--code", "x=1\n", "--target-version", "py36", "--py36"],
            prog_name="black"
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
        result = runner.invoke(main, ["--code", "x=1\n"], prog_name="black")
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
            result = runner.invoke(main, [f.name], prog_name="black")
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
        result = runner.invoke(main, ["-S", "--code", code], prog_name="black")
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
            result = runner.invoke(main, ["--include", "[bad", f.name], prog_name="black")
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
            result = runner.invoke(main, ["--exclude", "[bad", f.name], prog_name="black")
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
            result = runner.invoke(main, ["--check", f.name], prog_name="black")
            # If mutation present, would exit 0 instead of 1
            assert result.exit_code != 0
        finally:
            os.unlink(f.name)