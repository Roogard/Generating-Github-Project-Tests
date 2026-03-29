import pytest
from unittest.mock import patch, MagicMock

from cookiecutter.hooks import run_hook

# ---------------------------------------------------------------------------
# Constants used by the implementation
# ---------------------------------------------------------------------------
EXIT_SUCCESS = 0  # cookiecutter.hooks.EXIT_SUCCESS

# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# Statement: find_hooks().get(hook_name) returns None → log and return EXIT_SUCCESS
def test_statement_no_hook_found_returns_exit_success():
    """
    A correct run_hook SHOULD return EXIT_SUCCESS (0) when no hook is registered
    for the requested hook_name.
    # script is None → early return EXIT_SUCCESS
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={}):
        result = run_hook('pre_prompt', '/some/project', {'cookiecutter': {}})
    assert result == EXIT_SUCCESS

# Statement: find_hooks().get(hook_name) returns a path → run_script_with_context called
def test_statement_hook_found_delegates_to_run_script():
    """
    A correct run_hook SHOULD delegate to run_script_with_context when a
    matching hook script is found, and return whatever that function returns.
    # script is not None → run_script_with_context
    """
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}):
        with patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
            result = run_hook('pre_gen_project', '/my/project', {'cookiecutter': {'key': 'val'}})
    mock_run.assert_called_once_with(fake_script, '/my/project', {'cookiecutter': {'key': 'val'}})
    assert result == 0


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# Block: the `if script is None` branch (True) → already covered above in statement section.
# Note: see test_statement_no_hook_found_returns_exit_success

# Block: the `if script is None` branch (False) → else-path executing run_script_with_context
def test_block_hook_found_non_zero_return():
    """
    A correct run_hook SHOULD propagate any non-zero return code from
    run_script_with_context so the caller knows the hook failed.
    # script is not None → run_script_with_context → returns non-zero
    """
    fake_script = '/hooks/post_gen_project.sh'
    with patch('cookiecutter.hooks.find_hooks', return_value={'post_gen_project': fake_script}):
        with patch('cookiecutter.hooks.run_script_with_context', return_value=1):
            result = run_hook('post_gen_project', '/my/project', {})
    assert result == 1

# Block: hook_name not present in the dict returned by find_hooks
def test_block_different_hook_name_not_in_dict():
    """
    A correct run_hook SHOULD return EXIT_SUCCESS when find_hooks has entries
    but none matches the requested hook_name.
    # find_hooks returns a dict but .get(hook_name) evaluates to None
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': '/some/script.py'}):
        result = run_hook('post_gen_project', '/project', {})
    assert result == EXIT_SUCCESS


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# The sole condition is: `script is None`
# We need it to be True in at least one test and False in at least one test.

def test_condition_script_is_none_true():
    """
    Condition: `script is None` → True
    # script is None: True  → return EXIT_SUCCESS
    A correct run_hook SHOULD return EXIT_SUCCESS for this branch.
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={}):
        result = run_hook('pre_gen_project', '/project', {})
    # script is None: True
    assert result == EXIT_SUCCESS

def test_condition_script_is_none_false():
    """
    Condition: `script is None` → False
    # script is None: False → run_script_with_context is reached
    A correct run_hook SHOULD call run_script_with_context and return its result.
    """
    fake_script = '/hooks/pre_gen_project.py'
    sentinel = object()
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}):
        with patch('cookiecutter.hooks.run_script_with_context', return_value=sentinel):
            result = run_hook('pre_gen_project', '/project', {})
    # script is None: False
    assert result is sentinel


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------
# run_hook has exactly two paths:
#   Path A: find_hooks → script is None → log → return EXIT_SUCCESS
#   Path B: find_hooks → script not None → run_script_with_context → return result

def test_path_A_no_script_early_return():
    """
    Path A: find_hooks() → .get() → None → logging.debug → return EXIT_SUCCESS
    # path: find_hooks → script is None (True) → log → return EXIT_SUCCESS
    A correct run_hook SHOULD take this path and return EXIT_SUCCESS when no
    hook is registered.
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={}) as mock_find:
        with patch('cookiecutter.hooks.run_script_with_context') as mock_run:
            with patch('cookiecutter.hooks.logging') as mock_log:
                result = run_hook('pre_prompt', '/project/dir', {'cookiecutter': {}})
    # Correct behaviour: EXIT_SUCCESS returned, run_script_with_context NOT called
    assert result == EXIT_SUCCESS
    mock_run.assert_not_called()

def test_path_B_script_found_run_script_called():
    """
    Path B: find_hooks() → .get() → script path → run_script_with_context → return result
    # path: find_hooks → script is None (False) → run_script_with_context → return
    A correct run_hook SHOULD take this path, call run_script_with_context exactly
    once with the right arguments, and return its result.
    """
    fake_script = '/hooks/post_gen_project.py'
    context = {'cookiecutter': {'project_name': 'demo'}}
    project_dir = '/output/demo'
    with patch('cookiecutter.hooks.find_hooks', return_value={'post_gen_project': fake_script}):
        with patch('cookiecutter.hooks.run_script_with_context', return_value=EXIT_SUCCESS) as mock_run:
            result = run_hook('post_gen_project', project_dir, context)
    mock_run.assert_called_once_with(fake_script, project_dir, context)
    assert result == EXIT_SUCCESS

def test_path_B_script_found_propagates_failure_code():
    """
    Path B variant: run_script_with_context returns a non-zero exit code.
    # path: find_hooks → script is None (False) → run_script_with_context → return non-zero
    A correct run_hook SHOULD propagate non-zero exit codes from the hook
    script so callers can detect failures.
    """
    fake_script = '/hooks/pre_gen_project.sh'
    context = {'cookiecutter': {}}
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}):
        with patch('cookiecutter.hooks.run_script_with_context', return_value=2):
            result = run_hook('pre_gen_project', '/project', context)
    assert result == 2