import pytest
from unittest.mock import patch, MagicMock
from cookiecutter.hooks import run_hook

# --- ECP ---

def test_ecp_no_hook_found_returns_exit_success():
    """ECP: When find_hooks returns no matching hook, a correct run_hook SHOULD return EXIT_SUCCESS (0)."""
    with patch('cookiecutter.hooks.find_hooks', return_value={}):
        result = run_hook('pre_gen_project', '/some/project', {'cookiecutter': {}})
    assert result == 0

def test_ecp_hook_found_delegates_to_run_script_with_context():
    """ECP: When a matching hook is found, a correct run_hook SHOULD call run_script_with_context and return its result."""
    fake_script = '/path/to/pre_gen_project.py'
    fake_context = {'cookiecutter': {'project_name': 'test'}}
    project_dir = '/some/project'

    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        result = run_hook('pre_gen_project', project_dir, fake_context)

    mock_run.assert_called_once_with(fake_script, project_dir, fake_context)
    assert result == 0

def test_ecp_different_hook_name_not_matched():
    """ECP: When find_hooks has a hook but NOT the requested name, run_hook SHOULD return EXIT_SUCCESS."""
    with patch('cookiecutter.hooks.find_hooks', return_value={'post_gen_project': '/path/to/post.py'}):
        result = run_hook('pre_gen_project', '/some/project', {'cookiecutter': {}})
    assert result == 0

def test_ecp_run_script_nonzero_return_propagated():
    """ECP: When run_script_with_context returns nonzero, a correct run_hook SHOULD propagate it."""
    fake_script = '/path/to/post_gen_project.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'post_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=1):
        result = run_hook('post_gen_project', '/some/project', {'cookiecutter': {}})
    assert result == 1

def test_ecp_post_gen_project_hook_dispatched():
    """ECP: post_gen_project hook name is also a valid hook; run_hook SHOULD dispatch it correctly."""
    fake_script = '/hooks/post_gen_project.sh'
    fake_context = {'cookiecutter': {'repo_name': 'myrepo'}}
    project_dir = '/output/myrepo'

    with patch('cookiecutter.hooks.find_hooks', return_value={'post_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        result = run_hook('post_gen_project', project_dir, fake_context)

    mock_run.assert_called_once_with(fake_script, project_dir, fake_context)
    assert result == 0

def test_ecp_empty_context_still_dispatches():
    """ECP: An empty context dict is a valid value; run_hook SHOULD still dispatch the hook."""
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        result = run_hook('pre_gen_project', '/project', {})

    mock_run.assert_called_once_with(fake_script, '/project', {})
    assert result == 0

def test_ecp_empty_hooks_dict_returns_exit_success():
    """ECP: find_hooks returning empty dict means no hooks exist; run_hook SHOULD return EXIT_SUCCESS."""
    with patch('cookiecutter.hooks.find_hooks', return_value={}):
        result = run_hook('post_gen_project', '/project', {'cookiecutter': {}})
    assert result == 0

# --- BVA ---

def test_bva_hook_name_empty_string_not_found():
    """BVA: Empty string as hook_name is a boundary; find_hooks won't have '' key, SHOULD return EXIT_SUCCESS."""
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': '/path/hook.py'}):
        result = run_hook('', '/project', {'cookiecutter': {}})
    assert result == 0

def test_bva_multiple_hooks_only_matching_one_dispatched():
    """BVA: Hooks dict has multiple entries; only the matching hook SHOULD be dispatched."""
    hooks = {
        'pre_gen_project': '/hooks/pre.py',
        'post_gen_project': '/hooks/post.py',
    }
    with patch('cookiecutter.hooks.find_hooks', return_value=hooks), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        result = run_hook('pre_gen_project', '/project', {})

    mock_run.assert_called_once_with('/hooks/pre.py', '/project', {})
    assert result == 0

def test_bva_run_script_returns_large_exit_code():
    """BVA: run_script_with_context returning a large nonzero code; run_hook SHOULD propagate it exactly."""
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=127):
        result = run_hook('pre_gen_project', '/project', {})
    assert result == 127

def test_bva_run_script_returns_negative_exit_code():
    """BVA: Negative exit codes (e.g. -1) are a boundary; a correct run_hook SHOULD propagate them."""
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=-1):
        result = run_hook('pre_gen_project', '/project', {})
    assert result == -1

def test_bva_none_script_value_in_hooks_dict():
    """BVA: If find_hooks returns a dict where the hook maps to None, run_hook SHOULD treat it as missing and return EXIT_SUCCESS."""
    # A correct implementation uses .get() which returns None for missing keys;
    # explicitly mapping to None is equivalent — script is None, so no dispatch.
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': None}):
        result = run_hook('pre_gen_project', '/project', {})
    assert result == 0

# --- Mutation Detection ---

def test_mutation_get_vs_missing_key_not_short_circuited():
    """
    Mutation: Detects if script is checked with 'if script is not None' vs 'if script is None'.
    A correct run_hook with a valid script SHOULD NOT return EXIT_SUCCESS (0) without running.
    It SHOULD call run_script_with_context.
    """
    fake_script = '/hooks/pre.py'
    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        run_hook('pre_gen_project', '/project', {})

    # Mutation: if negation is flipped, run_script_with_context would never be called
    mock_run.assert_called_once()

def test_mutation_return_exit_success_vs_none():
    """
    Mutation: Detects if EXIT_SUCCESS constant was changed or if 'return EXIT_SUCCESS' was replaced with 'return None'.
    A correct run_hook SHOULD return exactly 0 (integer) when no hook is found, not None.
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={}):
        result = run_hook('pre_gen_project', '/project', {})
    assert result == 0
    assert result is not None

def test_mutation_wrong_hook_name_key_lookup():
    """
    Mutation: Detects if .get(hook_name) was changed to .get('pre_gen_project') hardcoded.
    A correct run_hook with hook_name='post_gen_project' SHOULD dispatch the post hook, not a hardcoded pre hook.
    """
    hooks = {
        'pre_gen_project': '/hooks/pre.py',
        'post_gen_project': '/hooks/post.py',
    }
    with patch('cookiecutter.hooks.find_hooks', return_value=hooks), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=42) as mock_run:
        result = run_hook('post_gen_project', '/project', {})

    # The correct script for post_gen_project must be dispatched
    mock_run.assert_called_once_with('/hooks/post.py', '/project', {})
    assert result == 42

def test_mutation_project_dir_passed_correctly():
    """
    Mutation: Detects if project_dir is swapped with context or script in the run_script_with_context call.
    A correct run_hook SHOULD pass project_dir as the second argument.
    """
    fake_script = '/hooks/pre.py'
    project_dir = '/correct/project/dir'
    context = {'cookiecutter': {'key': 'value'}}

    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        run_hook('pre_gen_project', project_dir, context)

    args, kwargs = mock_run.call_args
    assert args[1] == project_dir, "A correct run_hook SHOULD pass project_dir as second arg to run_script_with_context"

def test_mutation_context_passed_correctly():
    """
    Mutation: Detects if context is swapped with project_dir in the run_script_with_context call.
    A correct run_hook SHOULD pass context as the third argument.
    """
    fake_script = '/hooks/pre.py'
    project_dir = '/project'
    context = {'cookiecutter': {'name': 'mutation_test'}}

    with patch('cookiecutter.hooks.find_hooks', return_value={'pre_gen_project': fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        run_hook('pre_gen_project', project_dir, context)

    args, kwargs = mock_run.call_args
    assert args[2] == context, "A correct run_hook SHOULD pass context as third arg to run_script_with_context"

def test_mutation_find_hooks_called_each_invocation():
    """
    Mutation: Detects if find_hooks result is cached incorrectly (called zero times).
    A correct run_hook SHOULD call find_hooks each time it is invoked.
    """
    with patch('cookiecutter.hooks.find_hooks', return_value={}) as mock_find:
        run_hook('pre_gen_project', '/project', {})
        run_hook('post_gen_project', '/project', {})

    assert mock_find.call_count == 2

def test_mutation_script_passed_not_hook_name():
    """
    Mutation: Detects if hook_name is passed to run_script_with_context instead of the resolved script path.
    A correct run_hook SHOULD pass the script value (file path), not the hook_name string, as first argument.
    """
    fake_script = '/hooks/pre_gen_project.py'
    hook_name = 'pre_gen_project'

    with patch('cookiecutter.hooks.find_hooks', return_value={hook_name: fake_script}), \
         patch('cookiecutter.hooks.run_script_with_context', return_value=0) as mock_run:
        run_hook(hook_name, '/project', {})

    args, kwargs = mock_run.call_args
    assert args[0] == fake_script, "A correct run_hook SHOULD pass the resolved script path, not the hook name"
    assert args[0] != hook_name