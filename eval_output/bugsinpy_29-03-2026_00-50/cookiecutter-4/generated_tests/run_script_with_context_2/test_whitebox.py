import os
import sys
import stat
import textwrap
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from cookiecutter.hooks import run_script_with_context

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_script(content, suffix=".py", encoding="utf-8"):
    """Write *content* to a real temp file and return its path."""
    f = tempfile.NamedTemporaryFile(
        delete=False, mode="w", suffix=suffix, encoding=encoding
    )
    f.write(content)
    f.close()
    return f.name


def _make_executable(path):
    """Make a file executable on Unix-like systems."""
    if sys.platform != "win32":
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# ---------------------------------------------------------------------------
# Goal: every executable statement runs at least once.

def test_statement_reads_file_and_calls_run_script():
    """
    Basic happy-path: run_script_with_context reads the file, renders the
    template, writes a temp file, and delegates to run_script.
    A correct implementation should forward run_script's return value.
    """
    script_content = "# plain script, no template tags"
    script_path = _make_script(script_content, suffix=".py")
    cwd = tempfile.gettempdir()

    fake_return = MagicMock()

    try:
        with patch("cookiecutter.hooks.run_script", return_value=fake_return) as mock_run:
            result = run_script_with_context(script_path, cwd, {})

        # A correct implementation must return whatever run_script returns.
        assert result is fake_return
        # run_script must have been called exactly once.
        assert mock_run.call_count == 1
        # The cwd argument must be forwarded unchanged.
        _, called_cwd = mock_run.call_args[0]
        assert called_cwd == cwd
    finally:
        os.unlink(script_path)


def test_statement_extension_extracted_and_propagated():
    """
    os.path.splitext is called so the temp file inherits the extension.
    A correct implementation must pass a temp file whose suffix matches
    the original script's extension.
    """
    script_path = _make_script("# script", suffix=".sh")
    cwd = tempfile.gettempdir()

    captured = {}

    def fake_run_script(temp_name, cwd_arg):
        captured["temp_name"] = temp_name
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {})

        _, temp_ext = os.path.splitext(captured["temp_name"])
        assert temp_ext == ".sh"
    finally:
        os.unlink(script_path)


def test_statement_template_rendered_before_write():
    """
    The Jinja template must be rendered with the supplied context before
    writing.  A correct implementation should produce rendered content in
    the temp file.
    """
    script_path = _make_script("Hello {{ name }}!", suffix=".py")
    cwd = tempfile.gettempdir()
    context = {"name": "World"}
    captured = {}

    def fake_run_script(temp_name, cwd_arg):
        with open(temp_name, "r", encoding="utf-8") as fh:
            captured["content"] = fh.read()
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, context)

        assert captured["content"] == "Hello World!"
    finally:
        os.unlink(script_path)


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# ---------------------------------------------------------------------------
# The function has one main block plus the NamedTemporaryFile context-manager
# block.  We exercise both the "with" block body and the return statement
# outside it.

def test_block_temp_file_written_then_closed_before_run_script():
    """
    The temp file must be fully closed (context-manager exited) before
    run_script is invoked, so the OS can open it on Windows.
    """
    script_path = _make_script("data", suffix=".py")
    cwd = tempfile.gettempdir()
    calls = []

    def fake_run_script(temp_name, cwd_arg):
        # If the file is still open/locked this open() would fail on Windows.
        with open(temp_name, "r") as fh:
            calls.append(fh.read())
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {})

        assert len(calls) == 1
        assert "data" in calls[0]
    finally:
        os.unlink(script_path)


def test_block_with_nonempty_context():
    """
    Exercises the with-block with a non-trivial context dict so every
    branch of Template.render is reached.
    """
    script_path = _make_script(
        "{{ greeting }}, {{ target }}!", suffix=".py"
    )
    cwd = tempfile.gettempdir()
    context = {"greeting": "Hi", "target": "pytest"}
    captured = {}

    def fake_run_script(temp_name, cwd_arg):
        with open(temp_name, "r", encoding="utf-8") as fh:
            captured["rendered"] = fh.read()
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, context)

        assert captured["rendered"] == "Hi, pytest!"
    finally:
        os.unlink(script_path)


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# ---------------------------------------------------------------------------
# os.path.splitext: the extension is either empty ("") or non-empty (".py").
# Template(contents).render(**context): context can be empty or non-empty.
# (No explicit boolean guards in the function body, so we cover the
# implicit conditions inside helpers.)

def test_condition_extension_present():
    """
    # extension != "": True  (script has an extension)
    The suffix passed to NamedTemporaryFile must equal the original extension.
    """
    script_path = _make_script("x", suffix=".py")
    cwd = tempfile.gettempdir()
    captured = {}

    def fake_run_script(name, _cwd):
        captured["name"] = name
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {})
        _, ext = os.path.splitext(captured["name"])
        assert ext == ".py"  # extension is non-empty
    finally:
        os.unlink(script_path)


def test_condition_no_extension():
    """
    # extension != "": False  (script has no extension)
    The temp-file suffix should be empty string when the script has none.
    """
    # Create a script with no extension
    f = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix="")
    f.write("# no extension")
    f.close()
    script_path = f.name

    # Rename to strip any accidental suffix
    no_ext_path = script_path + "_noext"
    os.rename(script_path, no_ext_path)

    cwd = tempfile.gettempdir()
    captured = {}

    def fake_run_script(name, _cwd):
        captured["name"] = name
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(no_ext_path, cwd, {})
        _, ext = os.path.splitext(captured["name"])
        assert ext == ""  # extension is empty
    finally:
        os.unlink(no_ext_path)


def test_condition_context_empty():
    """
    # context is empty: True — template variables left unreplaced produce
    # the Jinja default (empty string for undefined).
    A correct implementation still runs without error.
    """
    script_path = _make_script("static content", suffix=".py")
    cwd = tempfile.gettempdir()
    captured = {}

    def fake_run_script(name, _cwd):
        with open(name, "r") as fh:
            captured["content"] = fh.read()
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {})
        assert captured["content"] == "static content"
    finally:
        os.unlink(script_path)


def test_condition_context_nonempty():
    """
    # context is non-empty: True — Jinja replaces variables.
    A correct implementation must substitute all provided context values.
    """
    script_path = _make_script("{{ a }} + {{ b }}", suffix=".py")
    cwd = tempfile.gettempdir()
    captured = {}

    def fake_run_script(name, _cwd):
        with open(name, "r") as fh:
            captured["content"] = fh.read()
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {"a": "1", "b": "2"})
        assert captured["content"] == "1 + 2"
    finally:
        os.unlink(script_path)


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# ---------------------------------------------------------------------------
# The function has essentially one linear path (no branching if/else):
#   entry → splitext → open+read → NamedTemporaryFile block → run_script → return
# We vary: extension present/absent, context empty/non-empty, run_script
# return value (0 vs non-zero), and propagation of exceptions.

def test_path_no_extension_empty_context_returns_zero():
    """
    # path: entry → splitext(no-ext) → read → temp(suffix="") → render(empty ctx) → run_script → return 0
    """
    f = tempfile.NamedTemporaryFile(delete=False, mode="w", suffix="")
    f.write("hello")
    f.close()
    no_ext = f.name + "_p1"
    os.rename(f.name, no_ext)
    cwd = tempfile.gettempdir()

    try:
        with patch("cookiecutter.hooks.run_script", return_value=0) as mock_run:
            result = run_script_with_context(no_ext, cwd, {})
        assert result == 0
        assert mock_run.call_count == 1
    finally:
        os.unlink(no_ext)


def test_path_with_extension_nonempty_context_returns_nonzero():
    """
    # path: entry → splitext(".sh") → read → temp(suffix=".sh") → render(ctx) → run_script → return 1
    A correct implementation must propagate any non-zero exit code.
    """
    script_path = _make_script("echo {{ msg }}", suffix=".sh")
    cwd = tempfile.gettempdir()

    try:
        with patch("cookiecutter.hooks.run_script", return_value=1) as mock_run:
            result = run_script_with_context(script_path, cwd, {"msg": "hi"})
        assert result == 1
    finally:
        os.unlink(script_path)


def test_path_run_script_receives_correct_args():
    """
    # path: all statements → run_script called with (temp_file_path, original_cwd)
    A correct implementation must forward cwd unchanged and pass a path
    whose extension matches the original script.
    """
    script_path = _make_script("content", suffix=".py")
    cwd = "/some/working/dir"
    captured = {}

    def fake_run_script(name, passed_cwd):
        captured["name"] = name
        captured["cwd"] = passed_cwd
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, {})

        assert captured["cwd"] == cwd
        _, ext = os.path.splitext(captured["name"])
        assert ext == ".py"
        # The temp file must actually exist when run_script is invoked.
        # (It may be cleaned up afterwards, so we only check during the call.)
    finally:
        os.unlink(script_path)


def test_path_exception_from_run_script_propagates():
    """
    # path: entry → ... → run_script raises → exception propagates to caller
    A correct implementation should not swallow exceptions from run_script.
    """
    script_path = _make_script("x", suffix=".py")
    cwd = tempfile.gettempdir()

    try:
        with patch(
            "cookiecutter.hooks.run_script",
            side_effect=OSError("script failed"),
        ):
            with pytest.raises(OSError, match="script failed"):
                run_script_with_context(script_path, cwd, {})
    finally:
        os.unlink(script_path)


def test_path_return_value_none():
    """
    # path: run_script returns None → function returns None
    A correct implementation must transparently forward None as well.
    """
    script_path = _make_script("# noop", suffix=".py")
    cwd = tempfile.gettempdir()

    try:
        with patch("cookiecutter.hooks.run_script", return_value=None):
            result = run_script_with_context(script_path, cwd, {})
        assert result is None
    finally:
        os.unlink(script_path)


def test_path_multiline_template_with_multiple_variables():
    """
    # path: entry → read multiline file → render with multiple vars → write → run_script
    A correct implementation must handle multiline scripts and multiple
    template substitutions.
    """
    content = textwrap.dedent(
        """\
        #!/usr/bin/env python
        print("{{ greeting }}")
        print("{{ farewell }}")
        """
    )
    script_path = _make_script(content, suffix=".py")
    cwd = tempfile.gettempdir()
    context = {"greeting": "Hello", "farewell": "Goodbye"}
    captured = {}

    def fake_run_script(name, _cwd):
        with open(name, "r") as fh:
            captured["rendered"] = fh.read()
        return 0

    try:
        with patch("cookiecutter.hooks.run_script", side_effect=fake_run_script):
            run_script_with_context(script_path, cwd, context)

        assert 'print("Hello")' in captured["rendered"]
        assert 'print("Goodbye")' in captured["rendered"]
    finally:
        os.unlink(script_path)