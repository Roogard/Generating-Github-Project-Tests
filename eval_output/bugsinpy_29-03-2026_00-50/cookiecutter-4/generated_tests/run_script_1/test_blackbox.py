import os
import sys
import stat
import tempfile
import subprocess
import pytest
from unittest.mock import patch, MagicMock

from cookiecutter.hooks import run_script

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write_script(directory, filename, content, make_exec=True):
    """Write a script file to *directory* and optionally make it executable."""
    path = os.path.join(directory, filename)
    with open(path, 'w') as fh:
        fh.write(content)
    if make_exec:
        current = os.stat(path).st_mode
        os.chmod(path, current | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


# ---------------------------------------------------------------------------
# --- BVA ---
# Boundary Value Analysis: script_path extension boundaries, cwd values
# ---------------------------------------------------------------------------

class TestBVA:

    def test_python_script_returns_zero_on_success(self, tmp_path):
        """BVA: .py extension boundary — script exits with 0."""
        script = _write_script(
            str(tmp_path),
            'hook.py',
            'import sys\nsys.exit(0)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 0

    def test_python_script_returns_nonzero_on_failure(self, tmp_path):
        """BVA: .py extension boundary — script exits with non-zero."""
        script = _write_script(
            str(tmp_path),
            'hook.py',
            'import sys\nsys.exit(1)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 1

    def test_python_script_returns_exit_code_255(self, tmp_path):
        """BVA: large exit code boundary (near max typical exit code)."""
        script = _write_script(
            str(tmp_path),
            'hook.py',
            'import sys\nsys.exit(255)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        # Exit codes are platform-specific; just assert it is non-zero
        assert result != 0

    def test_non_python_script_returns_zero_on_success(self, tmp_path):
        """BVA: no .py extension — treated as a direct executable."""
        if sys.platform.startswith('win'):
            pytest.skip('Non-.py shell script tests skipped on Windows')
        script = _write_script(
            str(tmp_path),
            'hook.sh',
            '#!/bin/sh\nexit 0\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 0

    def test_non_python_script_returns_nonzero_on_failure(self, tmp_path):
        """BVA: no .py extension — script exits with 1."""
        if sys.platform.startswith('win'):
            pytest.skip('Non-.py shell script tests skipped on Windows')
        script = _write_script(
            str(tmp_path),
            'hook.sh',
            '#!/bin/sh\nexit 1\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 1

    def test_cwd_default_dot(self, tmp_path):
        """BVA: cwd defaults to '.' — function should accept the default."""
        script = _write_script(
            str(tmp_path),
            'hook.py',
            'import sys\nsys.exit(0)\n'
        )
        # Pass explicit '.' to exercise that branch without changing real cwd
        with patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            with patch('cookiecutter.utils.make_executable'):
                result = run_script(script, cwd='.')
        assert result == 0

    def test_cwd_explicit_tmp_path(self, tmp_path):
        """BVA: explicit cwd passed to Popen."""
        script = _write_script(
            str(tmp_path),
            'hook.py',
            'import sys\nsys.exit(0)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 0

    def test_script_path_ends_with_py_uppercase_not_treated_as_python(self, tmp_path):
        """BVA: '.PY' (uppercase) is NOT '.py' — must NOT be treated as Python.
        A correct implementation SHOULD do a case-sensitive endswith('.py') check."""
        if sys.platform.startswith('win'):
            pytest.skip('Case-sensitivity test not applicable on Windows')
        # We only verify the command construction via mocking
        script_path = str(tmp_path / 'hook.PY')
        # Write a dummy file so make_executable doesn't fail
        with open(script_path, 'w') as fh:
            fh.write('#!/bin/sh\nexit 0\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            call_args = mock_popen.call_args
            cmd = call_args[0][0]
            # A correct implementation SHOULD NOT prepend sys.executable for .PY
            assert cmd[0] != sys.executable, (
                "Correct run_script SHOULD treat .PY as non-Python (case-sensitive)"
            )


# ---------------------------------------------------------------------------
# --- ECP ---
# Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECP:

    # --- Valid classes ---

    def test_valid_python_script_class(self, tmp_path):
        """ECP valid class: .py script that exits 0 → return value 0."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(0)\n'
        )
        assert run_script(script, cwd=str(tmp_path)) == 0

    def test_valid_python_script_nonzero_exit_class(self, tmp_path):
        """ECP valid class: .py script that exits non-zero → propagated exit code."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(42)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result != 0

    def test_valid_non_python_executable_class(self, tmp_path):
        """ECP valid class: non-.py executable → runs without sys.executable prefix."""
        if sys.platform.startswith('win'):
            pytest.skip('Shell script ECP skipped on Windows')
        script = _write_script(
            str(tmp_path), 'hook.sh', '#!/bin/sh\nexit 0\n'
        )
        assert run_script(script, cwd=str(tmp_path)) == 0

    def test_valid_cwd_is_existing_directory(self, tmp_path):
        """ECP valid class: cwd is a real existing directory."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(0)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 0

    def test_script_makes_itself_executable_via_make_executable(self, tmp_path):
        """ECP: make_executable is always called regardless of extension."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(0)\n',
            make_exec=False
        )
        with patch('cookiecutter.utils.make_executable') as mock_make_exec, \
             patch('subprocess.Popen') as mock_popen:
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script, cwd=str(tmp_path))
            mock_make_exec.assert_called_once_with(script)

    # --- Invalid / error classes ---

    def test_invalid_cwd_raises_or_propagates_error(self, tmp_path):
        """ECP invalid class: cwd that does not exist → OSError/FileNotFoundError."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(0)\n'
        )
        non_existent = str(tmp_path / 'does_not_exist')
        with pytest.raises((OSError, FileNotFoundError, NotADirectoryError)):
            run_script(script, cwd=non_existent)

    def test_invalid_script_path_not_found(self, tmp_path):
        """ECP invalid class: script_path does not exist → subprocess error."""
        non_existent_script = str(tmp_path / 'ghost.py')
        with patch('cookiecutter.utils.make_executable'):
            # FileNotFoundError or CalledProcessError or OSError are all acceptable
            try:
                result = run_script(non_existent_script, cwd=str(tmp_path))
                # If it doesn't raise, it must return non-zero (process failed)
                assert result != 0
            except (OSError, FileNotFoundError, subprocess.SubprocessError):
                pass  # expected


# ---------------------------------------------------------------------------
# --- Mutation Detection ---
# ---------------------------------------------------------------------------

class TestMutationDetection:

    def test_py_extension_check_uses_endswith_not_in(self, tmp_path):
        """Mutation: 'in' instead of 'endswith' would match 'file.py.bak'.
        A correct run_script SHOULD NOT treat 'file.py.bak' as a Python script."""
        if sys.platform.startswith('win'):
            pytest.skip('Shell script mutation test skipped on Windows')
        script_path = str(tmp_path / 'hook.py.bak')
        with open(script_path, 'w') as fh:
            fh.write('#!/bin/sh\nexit 0\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            cmd = mock_popen.call_args[0][0]
            # Correct: should NOT prepend sys.executable for '.py.bak'
            assert cmd[0] != sys.executable, (
                "Mutation detected: 'in .py' would wrongly match '.py.bak'"
            )

    def test_python_script_command_contains_sys_executable(self, tmp_path):
        """Mutation: missing sys.executable in command for .py scripts.
        A correct run_script SHOULD prepend sys.executable for .py scripts."""
        script_path = str(tmp_path / 'hook.py')
        with open(script_path, 'w') as fh:
            fh.write('import sys\nsys.exit(0)\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            cmd = mock_popen.call_args[0][0]
            assert cmd[0] == sys.executable, (
                "Correct run_script SHOULD use sys.executable for .py scripts"
            )
            assert cmd[1] == script_path

    def test_non_python_script_command_does_not_contain_sys_executable(self, tmp_path):
        """Mutation: always prepending sys.executable would break non-.py scripts."""
        if sys.platform.startswith('win'):
            pytest.skip('Shell script mutation test skipped on Windows')
        script_path = str(tmp_path / 'hook.sh')
        with open(script_path, 'w') as fh:
            fh.write('#!/bin/sh\nexit 0\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            cmd = mock_popen.call_args[0][0]
            assert cmd == [script_path], (
                "Correct run_script SHOULD NOT prepend sys.executable for non-.py"
            )

    def test_popen_receives_correct_cwd(self, tmp_path):
        """Mutation: cwd argument swapped or omitted in Popen call."""
        script_path = str(tmp_path / 'hook.py')
        with open(script_path, 'w') as fh:
            fh.write('import sys\nsys.exit(0)\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            _, kwargs = mock_popen.call_args
            assert kwargs.get('cwd') == str(tmp_path), (
                "Correct run_script SHOULD pass the given cwd to Popen"
            )

    def test_proc_wait_return_value_is_returned(self, tmp_path):
        """Mutation: returning proc instead of proc.wait() — return value must be int."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(7)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert isinstance(result, int), (
            "Correct run_script SHOULD return the integer exit code from proc.wait()"
        )
        assert result == 7

    def test_shell_flag_on_windows_only(self, tmp_path):
        """Mutation: shell=True on all platforms vs shell=False on non-Windows.
        A correct run_script SHOULD pass shell=True only on Windows."""
        script_path = str(tmp_path / 'hook.py')
        with open(script_path, 'w') as fh:
            fh.write('import sys\nsys.exit(0)\n')
        with patch('subprocess.Popen') as mock_popen, \
             patch('cookiecutter.utils.make_executable'):
            mock_proc = MagicMock()
            mock_proc.wait.return_value = 0
            mock_popen.return_value = mock_proc
            run_script(script_path, cwd=str(tmp_path))
            _, kwargs = mock_popen.call_args
            expected_shell = sys.platform.startswith('win')
            assert kwargs.get('shell') == expected_shell, (
                f"Correct run_script SHOULD set shell={expected_shell} "
                f"on platform {sys.platform!r}"
            )

    def test_make_executable_called_before_popen(self, tmp_path):
        """Mutation: make_executable called after Popen — order matters for permissions."""
        script_path = str(tmp_path / 'hook.py')
        with open(script_path, 'w') as fh:
            fh.write('import sys\nsys.exit(0)\n')
        call_order = []
        with patch('cookiecutter.utils.make_executable',
                   side_effect=lambda p: call_order.append('make_executable')), \
             patch('subprocess.Popen',
                   side_effect=lambda *a, **kw: call_order.append('popen') or
                   _make_mock_proc()) as _mock_popen:
            run_script(script_path, cwd=str(tmp_path))
        assert call_order.index('make_executable') < call_order.index('popen'), (
            "Correct run_script SHOULD call make_executable before Popen"
        )

    def test_return_value_is_wait_not_pid_or_proc(self, tmp_path):
        """Mutation: returning proc.pid or the Popen object instead of proc.wait()."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(0)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        # proc.wait() returns int; Popen object or pid are also int but semantically wrong
        # We verify it equals 0 (the actual exit code), not a pid (which would be > 1000 typically)
        assert result == 0, (
            "Correct run_script SHOULD return proc.wait() (exit code 0), "
            "not proc.pid or some other value"
        )

    def test_python_script_exit_code_2_propagated(self, tmp_path):
        """Mutation: off-by-one or hardcoded return 0 — checks real exit code propagation."""
        script = _write_script(
            str(tmp_path), 'hook.py', 'import sys\nsys.exit(2)\n'
        )
        result = run_script(script, cwd=str(tmp_path))
        assert result == 2, (
            "Correct run_script SHOULD propagate exit code 2 unchanged"
        )


# ---------------------------------------------------------------------------
# Helper used in mutation test
# ---------------------------------------------------------------------------

def _make_mock_proc():
    mock_proc = MagicMock()
    mock_proc.wait.return_value = 0
    return mock_proc