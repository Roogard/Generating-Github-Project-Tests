import os
import tempfile
import pytest
from unittest.mock import patch
from cookiecutter.hooks import find_hook


# --- Statement Coverage ---

def test_statement_hooks_dir_does_not_exist():
    # Hooks directory does not exist -> returns None immediately
    # path: hooks_dir not a dir -> return None
    result = find_hook('pre_gen_project', hooks_dir='/nonexistent/path/that/does/not/exist')
    assert result is None


def test_statement_hooks_dir_exists_matching_hook():
    # hooks_dir exists, a matching hook file is found -> returns absolute path
    # path: hooks_dir is dir -> loop finds valid_hook -> return abspath
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'pre_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)

        assert result is not None
        assert os.path.isabs(result)
        assert result == os.path.abspath(hook_file)


def test_statement_hooks_dir_exists_no_matching_hook():
    # hooks_dir exists but no file matches hook_name -> returns None at end
    # path: hooks_dir is dir -> loop exhausted without match -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'post_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)

        assert result is None


def test_statement_hooks_dir_empty_no_match():
    # hooks_dir exists but is empty -> loop body never executed -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)

        assert result is None


# --- Block Coverage ---

# Block 1: function entry / debug log call - covered by all tests above
# Block 2: if not os.path.isdir -> return None (covered by test_statement_hooks_dir_does_not_exist)
# Block 3: for loop body when valid_hook is True -> return abspath (covered by test_statement_hooks_dir_exists_matching_hook)
# Block 4: final return None after loop exhaustion (covered by test_statement_hooks_dir_exists_no_matching_hook)

def test_block_multiple_files_first_matches():
    # Loop body executes and returns on first matching file
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'pre_gen_project.py'), 'w').close()
        open(os.path.join(hooks_dir, 'post_gen_project.py'), 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)

        assert result is not None
        assert os.path.isabs(result)
        # Must point to pre_gen_project, not post_gen_project
        assert 'pre_gen_project' in os.path.basename(result)


def test_block_non_python_hook_file():
    # Loop body with a .sh hook file for the matching hook name
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'pre_gen_project.sh')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)

        assert result is not None
        assert os.path.isabs(result)
        assert 'pre_gen_project' in os.path.basename(result)


# --- Condition Coverage ---

# The key conditions in find_hook are:
#   C1: not os.path.isdir(hooks_dir)   -> True / False
#   C2: valid_hook(hook_file, hook_name) -> True / False

def test_condition_isdir_false():
    # C1: not os.path.isdir -> True (dir does not exist)
    # isdir(hooks_dir): False -> not isdir: True -> return None
    result = find_hook('pre_gen_project', hooks_dir='/no/such/dir')
    assert result is None  # C1 True


def test_condition_isdir_true_valid_hook_false():
    # C1: not os.path.isdir -> False (dir exists)
    # C2: valid_hook -> False (no matching file)
    # isdir: True, valid_hook: False
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'post_gen_project.py'), 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None  # C1 False, C2 False


def test_condition_isdir_true_valid_hook_true():
    # C1: not os.path.isdir -> False (dir exists)
    # C2: valid_hook -> True (matching file present)
    # isdir: True, valid_hook: True
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'pre_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None  # C1 False, C2 True
        assert result == os.path.abspath(hook_file)


# --- Path Coverage ---

# Distinct paths in find_hook:
# Path A: hooks_dir not a dir -> return None
# Path B: hooks_dir is a dir, empty -> loop zero iters -> return None
# Path C: hooks_dir is a dir, one file, valid_hook=False -> return None
# Path D: hooks_dir is a dir, one file, valid_hook=True -> return abspath
# Path E: hooks_dir is a dir, multiple files, first invalid then valid -> return abspath
# Path F: hooks_dir is a dir, multiple files, all invalid -> return None

def test_path_A_no_hooks_dir():
    # Path A: not os.path.isdir -> return None
    result = find_hook('pre_gen_project', hooks_dir='/absolutely/does/not/exist')
    assert result is None  # path: entry -> isdir False -> return None


def test_path_B_empty_hooks_dir():
    # Path B: dir exists, zero iterations of loop -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None  # path: entry -> isdir True -> loop 0 iters -> return None


def test_path_C_one_file_no_match():
    # Path C: dir exists, one file, valid_hook=False, loop exhausted -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'post_gen_project.py'), 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None  # path: entry -> isdir True -> loop 1 iter, no match -> return None


def test_path_D_one_file_match():
    # Path D: dir exists, one file, valid_hook=True -> return abspath
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'pre_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None  # path: entry -> isdir True -> loop 1 iter, match -> return abspath
        assert result == os.path.abspath(hook_file)
        assert os.path.isabs(result)


def test_path_E_multiple_files_match_found():
    # Path E: dir exists, multiple files, one matches -> return abspath of matching file
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'post_gen_project.py'), 'w').close()
        hook_file = os.path.join(hooks_dir, 'pre_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None  # path: entry -> isdir True -> loop multi iters -> match -> return abspath
        assert os.path.isabs(result)
        assert 'pre_gen_project' in os.path.basename(result)


def test_path_F_multiple_files_no_match():
    # Path F: dir exists, multiple files, none match -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'post_gen_project.py'), 'w').close()
        open(os.path.join(hooks_dir, 'another_hook.py'), 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is None  # path: entry -> isdir True -> loop multi iters, no match -> return None


def test_return_value_is_absolute_path():
    # Property: a correct find_hook SHOULD always return an absolute path when a hook is found
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        open(os.path.join(hooks_dir, 'pre_gen_project.py'), 'w').close()

        result = find_hook('pre_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.isabs(result)
        # The returned path must actually exist on disk
        assert os.path.exists(result)


def test_post_gen_project_hook_found():
    # Verify find_hook works for post_gen_project hook name too
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_dir = os.path.join(tmpdir, 'hooks')
        os.makedirs(hooks_dir)
        hook_file = os.path.join(hooks_dir, 'post_gen_project.py')
        open(hook_file, 'w').close()

        result = find_hook('post_gen_project', hooks_dir=hooks_dir)
        assert result is not None
        assert os.path.isabs(result)
        assert 'post_gen_project' in os.path.basename(result)


def test_hooks_dir_is_file_not_dir():
    # Edge: hooks_dir path exists but is a file, not a directory -> return None
    with tempfile.TemporaryDirectory() as tmpdir:
        hooks_path = os.path.join(tmpdir, 'hooks')
        open(hooks_path, 'w').close()  # Create a file named 'hooks', not a dir

        result = find_hook('pre_gen_project', hooks_dir=hooks_path)
        assert result is None  # C1 True (not a dir)