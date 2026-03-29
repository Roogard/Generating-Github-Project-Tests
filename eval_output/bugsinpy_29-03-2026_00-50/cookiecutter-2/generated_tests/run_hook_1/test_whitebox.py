import pytest
from unittest.mock import patch, MagicMock
from cookiecutter.hooks import run_hook

# --- Statement Coverage ---

def test_no_hook_found_returns_none():
    # Phase 1: find_hook returns None → early return path
    # Phase 2: A correct run_hook should return None (implicitly) when no hook is found
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('pre_gen_project', '/some/project', {'cookiecutter': {}})
        mock_find.assert_called_once_with('pre_gen_project')
        mock_run.assert_not_called()
        assert result is None

def test_hook_found_executes_script():
    # Phase 1: find_hook returns a script path → run_script_with_context is called
    # Phase 2: A correct run_hook should delegate execution to run_script_with_context
    fake_script = '/hooks/pre_gen_project.py'
    context = {'cookiecutter': {'project_name': 'myproject'}}
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/some/project', context)
        mock_find.assert_called_once_with('pre_gen_project')
        mock_run.assert_called_once_with(fake_script, '/some/project', context)

# --- Block Coverage ---

# Block 1: function entry + find_hook returns None + logger.debug + return
def test_block_no_hook_debug_logged():
    # Phase 1: find_hook returns None → hits the None-branch block
    # Phase 2: A correct run_hook should log and return without running any script
    with patch('cookiecutter.hooks.find_hook', return_value=None), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run, \
         patch('cookiecutter.hooks.logger') as mock_logger:
        run_hook('post_gen_project', '/project', {})
        mock_logger.debug.assert_any_call('No %s hook found', 'post_gen_project')
        mock_run.assert_not_called()

# Block 2: find_hook returns a script → logger.debug + run_script_with_context block
def test_block_hook_found_debug_logged():
    # Phase 1: find_hook returns a valid script path → hits the else-block
    # Phase 2: A correct run_hook should log "Running hook" before delegating
    fake_script = '/hooks/post_gen_project.sh'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run, \
         patch('cookiecutter.hooks.logger') as mock_logger:
        run_hook('post_gen_project', '/project', {'cookiecutter': {}})
        mock_logger.debug.assert_any_call('Running hook %s', 'post_gen_project')
        mock_run.assert_called_once()

# --- Condition Coverage ---

# The single boolean condition is: `if script is None`
# Condition: script is None → True
def test_condition_script_is_none_true():
    # script is None: True  →  early return
    with patch('cookiecutter.hooks.find_hook', return_value=None), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('pre_gen_project', '/project', {})
        assert result is None
        mock_run.assert_not_called()

# Condition: script is None → False
def test_condition_script_is_none_false():
    # script is None: False  →  script is executed
    fake_script = '/hooks/pre_gen_project.py'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', '/project', {})
        mock_run.assert_called_once_with(fake_script, '/project', {})

# --- Path Coverage ---

# Path 1: entry → find_hook returns None → log "No hook" → return
# (Covered by test_no_hook_found_returns_none; noted here for completeness)

# Path 2: entry → find_hook returns script → log "Running hook" → run_script_with_context → return
def test_path_hook_found_and_executed():
    # path: find_hook-not-None → log → run_script_with_context → implicit return None
    fake_script = '/hooks/pre_gen_project.py'
    context = {'cookiecutter': {'repo_name': 'testrepo'}}
    project_dir = '/output/testrepo'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('pre_gen_project', project_dir, context)
        # A correct run_hook returns None implicitly after running the script
        assert result is None
        mock_find.assert_called_once_with('pre_gen_project')
        mock_run.assert_called_once_with(fake_script, project_dir, context)

# Path 1 explicit with different hook name to exercise the no-op path distinctly
def test_path_no_hook_for_post_gen():
    # path: find_hook-returns-None → log → return None
    # A correct run_hook SHOULD return None and not call run_script_with_context
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find, \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        result = run_hook('post_gen_project', '/any/dir', {'cookiecutter': {}})
        assert result is None
        mock_find.assert_called_once_with('post_gen_project')
        mock_run.assert_not_called()

# Property assertions: hook_name is forwarded correctly to find_hook
def test_hook_name_forwarded_to_find_hook():
    # A correct run_hook SHOULD pass exactly the hook_name argument to find_hook
    with patch('cookiecutter.hooks.find_hook', return_value=None) as mock_find:
        run_hook('my_custom_hook', '/dir', {})
        mock_find.assert_called_once_with('my_custom_hook')

# Property assertion: project_dir and context are forwarded correctly
def test_project_dir_and_context_forwarded():
    # A correct run_hook SHOULD pass project_dir and context unchanged to run_script_with_context
    fake_script = '/hooks/hook.py'
    context = {'cookiecutter': {'foo': 'bar'}}
    project_dir = '/my/project'
    with patch('cookiecutter.hooks.find_hook', return_value=fake_script), \
         patch('cookiecutter.hooks.run_script_with_context') as mock_run:
        run_hook('pre_gen_project', project_dir, context)
        args, kwargs = mock_run.call_args
        assert args[1] == project_dir
        assert args[2] == context