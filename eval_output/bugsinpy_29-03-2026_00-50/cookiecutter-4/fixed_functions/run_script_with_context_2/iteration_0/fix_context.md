## Root Cause Diagnosis

Root Cause: The `run_script_with_context` function writes the rendered template content to a `NamedTemporaryFile` opened in mode `'w'` without specifying an encoding. On systems where the default locale encoding is not UTF-8 (e.g., Windows with a non-UTF-8 default), the temporary file write may fail or corrupt Unicode characters, causing the script to receive a garbled string instead of "héllo" and thus exit with code 1.

Suggestion 1: Add `encoding='utf-8'` to the `NamedTemporaryFile` call
Change the `tempfile.NamedTemporaryFile(delete=False, mode='w', suffix=extension)` call to include `encoding='utf-8'`, so that the rendered template content (which may contain Unicode characters) is written correctly to the temporary file regardless of the system's default locale encoding.

Suggestion 2: Encode the rendered content explicitly when writing
Instead of relying on the file's default encoding, write the rendered content as bytes by opening the temp file in binary mode (`mode='wb'`) and encoding the rendered string explicitly with `Template(contents).render(**context).encode('utf-8')`. This ensures Unicode content is always written correctly.

## Trigger Test(s)

```python
# test_blackbox.py
import os
import sys
import stat
import tempfile
import textwrap
import pytest

from cookiecutter.hooks import run_script_with_context

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_script(content, suffix=None, executable=True):
    """Write *content* to a named temp file and return its path."""
    if suffix is None:
        suffix = '.sh' if sys.platform != 'win32' else '.bat'
    fd, path = tempfile.mkstemp(suffix=suffix)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as fh:
            fh.write(content)
    except Exception:
        os.close(fd)
        raise
    if executable and sys.platform != 'win32':
        os.chmod(path, os.stat(path).st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return path


def _python_script(body, suffix='.py'):
    """Wrap *body* in a Python shebang script."""
    shebang = '#!{}\n'.format(sys.executable)
    return _make_script(shebang + textwrap.dedent(body), suffix=suffix)


# ---------------------------------------------------------------------------
# BVA — Boundary Value Analysis
# ---------------------------------------------------------------------------

class TestBVA:

    # -- Empty context (minimum valid context)
    def test_empty_context_runs_without_rendering_error(self, tmp_path):
        """A correct implementation SHOULD render the script with an empty context
        and execute it without raising an exception."""
        script = _python_script('import sys; sys.exit(0)\n')
        try:
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        # A zero return code means success
        assert result == 0 or result is None or result == 0

    # -- Single-key context
    def test_single_key_context_rendered(self, tmp_path):
        """A correct implementation SHOULD substitute a single Jinja variable."""
        script = _python_script(
            '''\
            import sys
            value = "{{ project_name }}"
            sys.exit(0 if value == "myproject" else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'project_name': 'myproject'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # -- Script in a deeply-nested cwd
    def test_cwd_is_respected(self, tmp_path):
        """The cwd parameter SHOULD be passed as the working directory for execution."""
        sub = tmp_path / 'a' / 'b' / 'c'
        sub.mkdir(parents=True)
        script = _python_script(
            '''\
            import os, sys
            # Write a sentinel file into cwd so we can verify it
            open(os.path.join(os.getcwd(), "sentinel.txt"), "w").close()
            sys.exit(0)
            '''
        )
        try:
            result = run_script_with_context(script, str(sub), {})
        finally:
            os.unlink(script)
        assert result == 0
        assert (sub / 'sentinel.txt').exists()

    # -- Script with no Jinja placeholders (typical non-templated script)
    def test_script_with_no_placeholders(self, tmp_path):
        """A correct implementation SHOULD not alter script content that has no
        Jinja placeholders."""
        script = _python_script('import sys; sys.exit(0)\n')
        try:
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        assert result == 0

    # -- .py extension is preserved in the temp file (BVA: extension boundary)
    def test_extension_preserved_for_py_script(self, tmp_path):
        """A correct implementation SHOULD use the same extension so the OS
        interpreter can identify the file type."""
        # We verify indirectly: the script executes successfully, which requires
        # the .py suffix to be intact for Python-based scripts.
        script = _python_script('import sys; sys.exit(0)\n', suffix='.py')
        try:
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        assert result == 0


# ---------------------------------------------------------------------------
# ECP — Equivalence Class Partitioning
# ---------------------------------------------------------------------------

class TestECP:

    # Valid class: context with multiple keys
    def test_valid_multiple_context_keys_rendered(self, tmp_path):
        """A correct implementation SHOULD render all provided Jinja variables."""
        script = _python_script(
            '''\
            import sys
            a = "{{ key_a }}"
            b = "{{ key_b }}"
            sys.exit(0 if (a == "hello" and b == "world") else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'key_a': 'hello', 'key_b': 'world'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Valid class: context values that are integers
    def test_valid_integer_context_value(self, tmp_path):
        """A correct implementation SHOULD render integer context values via Jinja."""
        script = _python_script(
            '''\
            import sys
            v = {{ count }}
            sys.exit(0 if v == 42 else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'count': 42}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Valid class: context values with special characters / unicode
    def test_valid_unicode_context_value(self, tmp_path):
        """A correct implementation SHOULD handle unicode values in the context."""
        script = _python_script(
            '''\
            # -*- coding: utf-8 -*-
            import sys
            v = "{{ label }}"
            sys.exit(0 if v == "héllo" else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'label': 'héllo'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Valid class: script that exits with non-zero (propagated correctly)
    def test_nonzero_exit_code_propagated(self, tmp_path):
        """A correct implementation SHOULD propagate the script's non-zero exit code."""
        script = _python_script('import sys; sys.exit(42)\n')
        try:
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        assert result == 42

    # Invalid class: non-existent script path SHOULD raise an error
    def test_invalid_nonexistent_script_raises(self, tmp_path):
        """A correct implementation SHOULD raise an exception (OSError / FileNotFoundError)
        when the script path does not exist."""
        with pytest.raises((OSError, FileNotFoundError, IOError)):
            run_script_with_context(
                '/nonexistent/path/to/script.py', str(tmp_path), {}
            )

    # Valid class: context key with a list value (Jinja handles it)
    def test_valid_list_context_value_rendered(self, tmp_path):
        """A correct implementation SHOULD pass list values to Jinja without error."""
        script = _python_script(
            '''\
            import sys
            items = {{ items }}
            sys.exit(0 if items == [1, 2, 3] else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'items': [1, 2, 3]}
            )
        finally:
            os.unlink(script)
        assert result == 0


# ---------------------------------------------------------------------------
# Mutation Detection
# ---------------------------------------------------------------------------

class TestMutationDetection:

    # Mutation: wrong extension passed to NamedTemporaryFile
    # If the suffix were hardcoded or ignored, .py scripts might not execute.
    def test_mutation_extension_suffix_used(self, tmp_path):
        """Detects: suffix=extension replaced by suffix='' or suffix=None.
        A correct implementation MUST use the original file's extension so the
        OS/interpreter can run the temp file."""
        # Use an explicit .py suffix; the script must run correctly.
        script = _python_script('import sys; sys.exit(0)\n', suffix='.py')
        try:
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: Template rendering skipped (contents written raw, no render call)
    def test_mutation_template_render_called(self, tmp_path):
        """Detects: Template(contents).render() replaced by just contents (no render).
        If rendering is skipped, the variable placeholder remains literal."""
        script = _python_script(
            '''\
            import sys
            val = "{{ sentinel }}"
            # If placeholder was NOT rendered, val == "{{ sentinel }}", exit 1
            sys.exit(0 if val == "RENDERED" else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'sentinel': 'RENDERED'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: context not unpacked (**context replaced with context or empty)
    def test_mutation_context_unpacked_as_kwargs(self, tmp_path):
        """Detects: render(**context) replaced by render(context) or render().
        Without proper unpacking, Jinja variables are undefined and render to ''."""
        script = _python_script(
            '''\
            import sys
            a = "{{ alpha }}"
            b = "{{ beta }}"
            sys.exit(0 if (a == "AAA" and b == "BBB") else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'alpha': 'AAA', 'beta': 'BBB'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: cwd not forwarded to run_script (cwd hardcoded or ignored)
    def test_mutation_cwd_forwarded_to_run_script(self, tmp_path):
        """Detects: run_script(temp.name, cwd) replaced by run_script(temp.name, '.')
        or run_script(temp.name).  The script verifies its cwd matches tmp_path."""
        expected_cwd = str(tmp_path)
        escaped = expected_cwd.replace('\\', '\\\\')
        script = _python_script(
            '''\
            import os, sys
            cwd = os.getcwd()
            expected = "{expected}"
            sys.exit(0 if os.path.normcase(cwd) == os.path.normcase(expected) else 1)
            '''.replace('{expected}', escaped)
        )
        try:
            result = run_script_with_context(script, expected_cwd, {})
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: delete=True instead of delete=False (temp file deleted before execution)
    def test_mutation_temp_file_not_deleted_before_run(self, tmp_path):
        """Detects: delete=False replaced by delete=True.
        On some platforms the file would be locked/deleted and run_script would fail."""
        script = _python_script('import sys; sys.exit(0)\n')
        try:
            # If the file were deleted before run_script is called, this raises
            # an error or returns a non-zero code on all platforms.
            result = run_script_with_context(script, str(tmp_path), {})
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: script_path extension vs temp file content mismatch
    # Verify that the rendered content (not the raw content) is what runs
    def test_mutation_rendered_content_written_not_raw(self, tmp_path):
        """Detects: temp.write(contents) instead of temp.write(Template(contents).render(...)).
        The script exits 0 only if the variable was substituted."""
        script = _python_script(
            '''\
            import sys
            x = "{{ check_var }}"
            sys.exit(0 if x == "substituted" else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'check_var': 'substituted'}
            )
        finally:
            os.unlink(script)
        assert result == 0

    # Mutation: off-by-one / wrong variable — temp.name vs script_path passed to run_script
    def test_mutation_temp_name_used_not_script_path(self, tmp_path):
        """Detects: run_script(script_path, cwd) instead of run_script(temp.name, cwd).
        If script_path were used, the unrendered original would run.
        We distinguish by checking that the rendered version (not raw) is executed."""
        script = _python_script(
            '''\
            import sys
            rendered = "{{ flag }}"
            # Raw script would still have '{{ flag }}' as the string literal;
            # when executed Python would NOT set rendered="yes".
            sys.exit(0 if rendered == "yes" else 1)
            '''
        )
        try:
            result = run_script_with_context(
                script, str(tmp_path), {'flag': 'yes'}
            )
        finally:
            os.unlink(script)
        assert result == 0
```
