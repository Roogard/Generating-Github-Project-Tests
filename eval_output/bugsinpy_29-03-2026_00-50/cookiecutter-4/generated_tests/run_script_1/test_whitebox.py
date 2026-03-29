import sys
import os
import stat
import tempfile
import subprocess
from unittest.mock import patch, MagicMock

import pytest

from cookiecutter.hooks import run_script

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_script(content, suffix, executable=True):
    """Write a temp script file and return its path."""
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w') as f:
            f.write(content)
    except Exception:
        os.close(fd)
        raise
    if executable:
        st = os.stat(path)
        os.chmod(path, st.st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    return path


# ---------------------------------------------------------------------------
# --- Statement Coverage ---
# Each executable statement is hit at least once.
# ---------------------------------------------------------------------------

def test_statement_py_script_success():
    """
    Hit: run_thru_shell assignment, .endswith('.py') True branch,
    script_command = [sys.executable, script_path],
    make_executable, Popen, proc.wait(), return.
    A correct run_script SHOULD return 0 for a Python script that exits cleanly.
    # path: endswith-py-True → Popen → return 0
    # run_thru_shell: True if win else False  (both sub-expressions covered across tests)
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        result = run_script(path, cwd=tempfile.gettempdir())
        assert result == 0
    finally:
        os.unlink(path)


def test_statement_non_py_script():
    """
    Hit: .endswith('.py') False branch → script_command = [script_path].
    On Windows this path is taken but the script type differs; we mock Popen
    to avoid platform-specific shell execution issues, testing the command
    construction logic only.
    # path: endswith-py-False → Popen → return
    """
    path = _write_script('', suffix='.sh')
    try:
        mock_proc = MagicMock()
        mock_proc.wait.return_value = 0
        with patch('subprocess.Popen', return_value=mock_proc) as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            result = run_script(path, cwd=tempfile.gettempdir())
            # A correct run_script SHOULD pass only the script path (no interpreter) for non-.py
            call_args = mock_popen.call_args
            script_command_used = call_args[0][0]
            assert script_command_used == [path]
            assert result == 0
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Block Coverage ---
# Every basic block (contiguous statements between branch points) is executed.
# ---------------------------------------------------------------------------

# Block 1: function entry + run_thru_shell assignment  → covered by test_statement_py_script_success
# Block 2: if script_path.endswith('.py') True body    → covered by test_statement_py_script_success
# Block 3: else body (non-.py)                         → covered by test_statement_non_py_script
# Block 4: make_executable + Popen + proc.wait()       → covered below + above

def test_block_make_executable_called():
    """
    Verify the make_executable block is always executed regardless of script type.
    A correct run_script SHOULD always call make_executable on the script path.
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('cookiecutter.utils.make_executable') as mock_make_exec, \
             patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(path, cwd=tempfile.gettempdir())
            mock_make_exec.assert_called_once_with(path)
    finally:
        os.unlink(path)


def test_block_popen_called_with_cwd():
    """
    Verify the Popen block passes cwd correctly.
    A correct run_script SHOULD forward the cwd argument to Popen.
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    cwd = tempfile.gettempdir()
    try:
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 42
            mock_popen.return_value = mock_proc
            result = run_script(path, cwd=cwd)
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs['cwd'] == cwd
            assert result == 42
    finally:
        os.unlink(path)


def test_block_nonzero_return_code():
    """
    Verify the return block correctly propagates a non-zero exit code.
    A correct run_script SHOULD return the subprocess exit code as-is.
    """
    path = _write_script('import sys\nsys.exit(3)\n', suffix='.py')
    try:
        result = run_script(path, cwd=tempfile.gettempdir())
        assert result == 3
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Condition Coverage ---
# Each boolean sub-expression evaluates to both True and False.
# ---------------------------------------------------------------------------

# Condition A: sys.platform.startswith('win')
#   → True  on Windows, False on non-Windows.
#   We mock sys.platform to force both branches deterministically.

def test_condition_run_thru_shell_true():
    """
    sys.platform.startswith('win'): True → shell=True passed to Popen.
    # run_thru_shell: True
    # endswith('.py'): True  (secondary condition, also True here)
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('sys.platform', 'win32'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(path, cwd=tempfile.gettempdir())
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs['shell'] is True
    finally:
        os.unlink(path)


def test_condition_run_thru_shell_false():
    """
    sys.platform.startswith('win'): False → shell=False passed to Popen.
    # run_thru_shell: False
    # endswith('.py'): True
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('sys.platform', 'linux'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(path, cwd=tempfile.gettempdir())
            call_kwargs = mock_popen.call_args[1]
            assert call_kwargs['shell'] is False
    finally:
        os.unlink(path)


def test_condition_endswith_py_true():
    """
    script_path.endswith('.py'): True → command includes sys.executable.
    # run_thru_shell: False (linux)
    # endswith('.py'): True
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('sys.platform', 'linux'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(path, cwd=tempfile.gettempdir())
            script_command_used = mock_popen.call_args[0][0]
            # A correct run_script SHOULD prepend sys.executable for .py scripts
            assert script_command_used[0] == sys.executable
            assert script_command_used[1] == path
    finally:
        os.unlink(path)


def test_condition_endswith_py_false():
    """
    script_path.endswith('.py'): False → command is just [script_path].
    # run_thru_shell: False (linux)
    # endswith('.py'): False
    """
    path = _write_script('', suffix='.sh')
    try:
        with patch('sys.platform', 'linux'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(path, cwd=tempfile.gettempdir())
            script_command_used = mock_popen.call_args[0][0]
            # A correct run_script SHOULD NOT prepend an interpreter for non-.py scripts
            assert script_command_used == [path]
    finally:
        os.unlink(path)


# ---------------------------------------------------------------------------
# --- Path Coverage ---
# Distinct entry-to-exit paths through the function.
# ---------------------------------------------------------------------------

# The function has 4 distinct paths from the two independent boolean decisions:
#   P1: win=False, endswith('.py')=True   → [sys.executable, path], shell=False
#   P2: win=False, endswith('.py')=False  → [path], shell=False
#   P3: win=True,  endswith('.py')=True   → [sys.executable, path], shell=True
#   P4: win=True,  endswith('.py')=False  → [path], shell=True

def test_path_linux_py_script():
    """
    P1: platform=linux, endswith('.py')=True
    # path: run_thru_shell=False → endswith-py-True → Popen(shell=False) → return
    A correct run_script SHOULD return 0 for clean .py script on linux.
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('sys.platform', 'linux'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            result = run_script(path, cwd=tempfile.gettempdir())
            args, kwargs = mock_popen.call_args
            assert args[0] == [sys.executable, path]
            assert kwargs['shell'] is False
            assert result == 0
    finally:
        os.unlink(path)


def test_path_linux_non_py_script():
    """
    P2: platform=linux, endswith('.py')=False
    # path: run_thru_shell=False → endswith-py-False → Popen(shell=False) → return
    A correct run_script SHOULD pass only the script path for non-.py on linux.
    """
    path = _write_script('', suffix='.sh')
    try:
        with patch('sys.platform', 'linux'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            result = run_script(path, cwd=tempfile.gettempdir())
            args, kwargs = mock_popen.call_args
            assert args[0] == [path]
            assert kwargs['shell'] is False
            assert result == 0
    finally:
        os.unlink(path)


def test_path_windows_py_script():
    """
    P3: platform=win32, endswith('.py')=True
    # path: run_thru_shell=True → endswith-py-True → Popen(shell=True) → return
    A correct run_script SHOULD use sys.executable for .py and shell=True on windows.
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        with patch('sys.platform', 'win32'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            result = run_script(path, cwd=tempfile.gettempdir())
            args, kwargs = mock_popen.call_args
            assert args[0] == [sys.executable, path]
            assert kwargs['shell'] is True
            assert result == 0
    finally:
        os.unlink(path)


def test_path_windows_non_py_script():
    """
    P4: platform=win32, endswith('.py')=False
    # path: run_thru_shell=True → endswith-py-False → Popen(shell=True) → return
    A correct run_script SHOULD pass only the script path with shell=True on windows for non-.py.
    """
    path = _write_script('', suffix='.sh')
    try:
        with patch('sys.platform', 'win32'), \
             patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            result = run_script(path, cwd=tempfile.gettempdir())
            args, kwargs = mock_popen.call_args
            assert args[0] == [path]
            assert kwargs['shell'] is True
            assert result == 0
    finally:
        os.unlink(path)


def test_path_nonzero_exit_propagated():
    """
    Extra path: subprocess exits with non-zero code.
    # path: endswith-py-True → Popen → proc.wait() returns non-zero → return non-zero
    A correct run_script SHOULD propagate arbitrary non-zero exit codes unchanged.
    """
    path = _write_script('import sys\nsys.exit(7)\n', suffix='.py')
    try:
        result = run_script(path, cwd=tempfile.gettempdir())
        assert result == 7
    finally:
        os.unlink(path)


def test_path_default_cwd():
    """
    Path using default cwd='.'.
    A correct run_script SHOULD accept the default cwd without error.
    """
    path = _write_script('import sys\nsys.exit(0)\n', suffix='.py')
    try:
        # No explicit cwd → uses '.' (current directory)
        result = run_script(path)
        assert result == 0
    finally:
        os.unlink(path)