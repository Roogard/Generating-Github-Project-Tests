import os
import stat
import tempfile
import shutil
import pytest

from cookiecutter.hooks import find_hook

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_hooks_dir(tmp_path, files=None):
    """Create a hooks directory under tmp_path, optionally with named files."""
    hooks_dir = os.path.join(str(tmp_path), 'hooks')
    os.makedirs(hooks_dir, exist_ok=True)
    for fname in (files or []):
        full = os.path.join(hooks_dir, fname)
        with open(full, 'w') as f:
            f.write('#!/bin/sh\n')
        os.chmod(full, os.stat(full).st_mode | stat.S_IEXEC)
    return hooks_dir


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def change_to_tmpdir(tmp_path, monkeypatch):
    """Each test runs with tmp_path as cwd so relative hooks_dir paths work."""
    monkeypatch.chdir(tmp_path)
    yield


# ===========================================================================
# --- BVA ---
# ===========================================================================

class TestBVA:

    def test_hooks_dir_does_not_exist_returns_none(self, tmp_path):
        """BVA: hooks_dir absent (empty/missing directory boundary)."""
        result = find_hook('pre_gen_project', hooks_dir='hooks')
        assert result is None

    def test_hooks_dir_empty_returns_none(self, tmp_path):
        """BVA: hooks_dir exists but contains zero files (empty collection)."""
        hooks_dir = make_hooks_dir(tmp_path, files=[])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None

    def test_hooks_dir_single_matching_file(self, tmp_path):
        """BVA: single file that matches hook_name."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.isabs(result)
        assert os.path.basename(result) == 'pre_gen_project.sh'

    def test_hooks_dir_single_non_matching_file(self, tmp_path):
        """BVA: single file present but does not match hook_name."""
        hooks_dir = make_hooks_dir(tmp_path, files=['post_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None

    def test_hooks_dir_many_files_only_one_matches(self, tmp_path):
        """BVA: large collection, exactly one file matches."""
        files = ['post_gen_project.sh'] + [f'other_{i}.sh' for i in range(10)]
        files.append('pre_gen_project.py')
        hooks_dir = make_hooks_dir(tmp_path, files=files)
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'pre_gen_project' in os.path.basename(result)

    def test_hook_name_single_char(self, tmp_path):
        """BVA: minimal hook_name length (single character)."""
        hooks_dir = make_hooks_dir(tmp_path, files=['x.sh'])
        result = find_hook('x', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.basename(result) == 'x.sh'

    def test_hook_name_empty_string_no_match(self, tmp_path):
        """BVA: empty hook_name string should not accidentally match real files."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        # A correct find_hook with an empty name should either return None or
        # only match a file with no stem; it must NOT return a real hook script.
        result = find_hook('', hooks_dir=hooks_dir)
        # The file stem 'pre_gen_project' != '' so no match expected.
        assert result is None

    def test_returns_absolute_path(self, tmp_path):
        """BVA: return value must always be an absolute path when found."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.isabs(result)


# ===========================================================================
# --- ECP ---
# ===========================================================================

class TestECP:

    # Valid classes

    def test_valid_sh_extension(self, tmp_path):
        """ECP valid: .sh extension hook file."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert result.endswith('pre_gen_project.sh')

    def test_valid_py_extension(self, tmp_path):
        """ECP valid: .py extension hook file."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.py'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert result.endswith('pre_gen_project.py')

    def test_valid_post_gen_hook(self, tmp_path):
        """ECP valid: post_gen_project hook name."""
        hooks_dir = make_hooks_dir(tmp_path, files=['post_gen_project.sh'])
        result = find_hook('post_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'post_gen_project' in os.path.basename(result)

    def test_valid_pre_gen_hook(self, tmp_path):
        """ECP valid: pre_gen_project hook name."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'pre_gen_project' in os.path.basename(result)

    # Invalid classes

    def test_invalid_hooks_dir_path(self, tmp_path):
        """ECP invalid: hooks_dir path points to a non-existent directory."""
        result = find_hook('pre_gen_project', hooks_dir='/nonexistent/path/hooks')
        assert result is None

    def test_invalid_hook_name_not_present(self, tmp_path):
        """ECP invalid: hook_name not matching any file in hooks_dir."""
        hooks_dir = make_hooks_dir(tmp_path, files=['post_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None

    def test_invalid_hooks_dir_is_file_not_dir(self, tmp_path):
        """ECP invalid: hooks_dir path exists but is a file, not a directory."""
        hooks_file = os.path.join(str(tmp_path), 'hooks')
        with open(hooks_file, 'w') as f:
            f.write('not a directory')
        result = find_hook('pre_gen_project', hooks_dir=hooks_file)
        assert result is None

    def test_invalid_file_with_only_extension_no_stem(self, tmp_path):
        """ECP invalid: file named '.sh' (empty stem) should not match hook_name."""
        hooks_dir = make_hooks_dir(tmp_path, files=['.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None

    def test_valid_multiple_hooks_only_requested_returned(self, tmp_path):
        """ECP valid: multiple hooks present; only requested one returned."""
        hooks_dir = make_hooks_dir(
            tmp_path,
            files=['pre_gen_project.sh', 'post_gen_project.sh']
        )
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'pre_gen_project' in os.path.basename(result)
        assert 'post_gen_project' not in os.path.basename(result)

    def test_default_hooks_dir_no_hooks_present(self, tmp_path):
        """ECP valid: default hooks_dir param used; no hooks directory exists."""
        result = find_hook('pre_gen_project')
        assert result is None

    def test_default_hooks_dir_with_hook_present(self, tmp_path):
        """ECP valid: default hooks_dir used; matching hook exists."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        # hooks_dir was created as tmp_path/hooks, and cwd == tmp_path
        result = find_hook('pre_gen_project')  # default hooks_dir='hooks'
        assert result is not None
        assert 'pre_gen_project' in os.path.basename(result)


# ===========================================================================
# --- Mutation Detection ---
# ===========================================================================

class TestMutationDetection:

    def test_returns_none_not_false_when_dir_missing(self, tmp_path):
        """Mutation: negation error — correct impl returns None (falsy),
        NOT False; distinguishes 'not os.path.isdir' inversion."""
        result = find_hook('pre_gen_project', hooks_dir='no_such_dir')
        assert result is None  # must be exactly None, not False or empty string

    def test_returns_none_not_empty_string_when_no_match(self, tmp_path):
        """Mutation: wrong constant — result must be None, not ''."""
        hooks_dir = make_hooks_dir(tmp_path, files=['post_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None

    def test_path_join_uses_hooks_dir_not_cwd(self, tmp_path):
        """Mutation: wrong variable — path must include hooks_dir component,
        not just the filename joined to cwd."""
        subdir = os.path.join(str(tmp_path), 'myhooks')
        os.makedirs(subdir)
        hook_file = os.path.join(subdir, 'pre_gen_project.sh')
        with open(hook_file, 'w') as f:
            f.write('#!/bin/sh\n')
        result = find_hook('pre_gen_project', hooks_dir=subdir)
        assert result is not None
        # The returned path must contain the custom hooks_dir, not just tmp_path
        assert subdir in result

    def test_abspath_is_applied_to_result(self, tmp_path):
        """Mutation: missing os.path.abspath call — result must be absolute."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result == os.path.abspath(result)

    def test_does_not_return_wrong_hook_file(self, tmp_path):
        """Mutation: off-by-one / wrong variable — must NOT return
        post_gen_project when pre_gen_project was requested."""
        hooks_dir = make_hooks_dir(
            tmp_path,
            files=['post_gen_project.sh', 'pre_gen_project.py']
        )
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'post_gen_project' not in os.path.basename(result)

    def test_only_valid_hook_extensions_returned(self, tmp_path):
        """Mutation: boundary — a file with irrelevant extension like .txt
        should not be returned for a hook_name match if valid_hook rejects it."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.txt'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        # A correct implementation delegates to valid_hook which checks
        # extensions; .txt is not a valid hook extension so must return None.
        assert result is None

    def test_no_partial_name_match(self, tmp_path):
        """Mutation: wrong operator / substring check — 'pre_gen' must NOT
        match a file named 'pre_gen_project.sh'."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen', hooks_dir=hooks_dir)
        # 'pre_gen' is only a prefix; a correct impl must not match
        assert result is None

    def test_iterates_all_files_not_just_first(self, tmp_path):
        """Mutation: off-by-one loop termination — must find the matching hook
        even if it is not the first file listed."""
        # Create many files so the target is unlikely to be iterated first
        files = [f'zzz_other_{i}.sh' for i in range(20)]
        files.append('pre_gen_project.sh')
        hooks_dir = make_hooks_dir(tmp_path, files=files)
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert 'pre_gen_project' in os.path.basename(result)

    def test_result_path_exists_on_filesystem(self, tmp_path):
        """Mutation: path construction error — returned path must actually
        exist; detects wrong join arguments."""
        hooks_dir = make_hooks_dir(tmp_path, files=['pre_gen_project.sh'])
        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.exists(result)