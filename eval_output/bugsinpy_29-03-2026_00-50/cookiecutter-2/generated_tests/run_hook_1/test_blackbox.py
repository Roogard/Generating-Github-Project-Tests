import pytest
import os
import sys
from unittest.mock import patch, MagicMock
from cookiecutter.hooks import run_hook

# --- ECP ---

def test_ecp_no_hook_found_returns_none():
    """ECP: when find_hook returns None (no hook script exists), run_hook should return None without error."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('pre_gen_project', '/some/project', {'cookiecutter': {}})
        assert result is None
        mock_run.assert_not_called()

def test_ecp_hook_found_runs_script():
    """ECP: when find_hook returns a valid script path, run_script_with_context should be called."""
    fake_script = '/hooks/pre_gen_project.py'
    fake_dir = '/some/project'
    fake_context = {'cookiecutter': {'project_name': 'test'}}
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', fake_dir, fake_context)
        mock_run.assert_called_once_with(fake_script, fake_dir, fake_context)

def test_ecp_post_gen_hook_found_runs_script():
    """ECP: post_gen_project hook name is passed through correctly."""
    fake_script = '/hooks/post_gen_project.sh'
    fake_dir = '/output/project'
    fake_context = {'cookiecutter': {}}
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('post_gen_project', fake_dir, fake_context)
        mock_run.assert_called_once_with(fake_script, fake_dir, fake_context)

def test_ecp_empty_context_allowed():
    """ECP: an empty context dict should not cause run_hook to fail before delegating."""
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/dir', {})
        mock_run.assert_called_once_with(fake_script, '/dir', {})

def test_ecp_arbitrary_hook_name_passed_to_find_hook():
    """ECP: any hook name string is passed directly to find_hook."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('custom_hook', '/dir', {})
        mock_find.assert_called_once_with('custom_hook')

# --- BVA ---

def test_bva_hook_name_empty_string():
    """BVA: empty string hook name should be forwarded to find_hook."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('', '/dir', {})
        mock_find.assert_called_once_with('')
        assert result is None
        mock_run.assert_not_called()

def test_bva_hook_name_single_char():
    """BVA: single character hook name is forwarded to find_hook."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('x', '/dir', {})
        mock_find.assert_called_once_with('x')

def test_bva_project_dir_passed_correctly_to_run_script():
    """BVA: project_dir is forwarded exactly as given to run_script_with_context."""
    fake_script = '/hooks/pre.py'
    for project_dir in ['/', '/a', '/very/deeply/nested/project/directory']:
        with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
             patch('cookiecutter.hooks.run_script_with_context') as mock_run:
            run_hook('pre_gen_project', project_dir, {})
            mock_run.assert_called_once_with(fake_script, project_dir, {})

def test_bva_context_with_many_keys():
    """BVA: a large context dict is forwarded unchanged."""
    fake_script = '/hooks/pre.py'
    large_context = {'cookiecutter': {f'key_{i}': f'value_{i}' for i in range(100)}}
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/dir', large_context)
        mock_run.assert_called_once_with(fake_script, '/dir', large_context)

def test_bva_script_path_passed_unchanged():
    """BVA: the script returned by find_hook is passed unchanged to run_script_with_context."""
    for fake_script in ['/a', '/hooks/pre_gen_project.py', '/hooks/post_gen_project.sh']:
        with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
             patch('cookiecutter.hooks.run_script_with_context') as mock_run:
            run_hook('pre_gen_project', '/dir', {})
            args, _ = mock_run.call_args
            assert args[0] == fake_script

# --- Mutation Detection ---

def test_mutation_none_check_not_inverted():
    """Mutation: detects if the None check is inverted (i.e., runs script when hook is None instead of skipping)."""
    with patch('cookiecutter.hooks.find_hook', return_value=None), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/dir', {})
        # A correct implementation must NOT call run_script_with_context when script is None
        mock_run.assert_not_called()

def test_mutation_script_passed_not_hook_name():
    """Mutation: detects if hook_name is passed instead of script to run_script_with_context."""
    fake_script = '/hooks/pre_gen_project.py'
    hook_name = 'pre_gen_project'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook(hook_name, '/dir', {})
        args, _ = mock_run.call_args
        # First argument must be the script path, not the hook name
        assert args[0] == fake_script
        assert args[0] != hook_name

def test_mutation_project_dir_not_swapped_with_script():
    """Mutation: detects if project_dir and script arguments are swapped."""
    fake_script = '/hooks/pre_gen_project.py'
    project_dir = '/my/project'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', project_dir, {})
        args, _ = mock_run.call_args
        assert args[0] == fake_script
        assert args[1] == project_dir

def test_mutation_context_not_swapped_with_project_dir():
    """Mutation: detects if context and project_dir arguments are swapped."""
    fake_script = '/hooks/pre.py'
    project_dir = '/my/project'
    context = {'cookiecutter': {'key': 'value'}}
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', project_dir, context)
        args, _ = mock_run.call_args
        assert args[1] == project_dir
        assert args[2] == context

def test_mutation_find_hook_called_once_not_zero_times():
    """Mutation: detects if find_hook is never called (early return without searching)."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('pre_gen_project', '/dir', {})
        mock_find.assert_called_once()

def test_mutation_run_script_called_once_not_multiple_times():
    """Mutation: detects if run_script_with_context is called more than once for a single hook."""
    fake_script = '/hooks/pre.py'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/dir', {})
        assert mock_run.call_count == 1

def test_mutation_hook_name_forwarded_to_find_hook_not_hardcoded():
    """Mutation: detects if find_hook is called with a hardcoded string instead of hook_name."""
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('post_gen_project', '/dir', {})
        mock_find.assert_called_once_with('post_gen_project')

    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('pre_gen_project', '/dir', {})
        mock_find.assert_called_once_with('pre_gen_project')

def test_mutation_no_exception_when_hook_missing():
    """Mutation: a correct implementation should not raise when no hook is found (not inverted error guard)."""
    with patch('cookiecutter.hooks.find_hook', return_value=None):
        # Should not raise any exception
        try:
            run_hook('pre_gen_project', '/dir', {})
        except Exception as e:
            pytest.fail(f"run_hook raised unexpectedly when hook not found: {e}")

def test_mutation_exception_propagated_from_run_script():
    """Mutation: detects if exceptions from run_script_with_context are swallowed."""
    from cookiecutter.exceptions import FailedHookException
    fake_script = '/hooks/pre.py'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context', side_effect=FailedHookException('hook failed')):
        with pytest.raises(FailedHookException):
            run_hook('pre_gen_project', '/dir', {})