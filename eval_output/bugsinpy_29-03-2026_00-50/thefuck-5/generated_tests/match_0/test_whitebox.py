import pytest
from unittest.mock import MagicMock
from thefuck.rules.git_push import match

# Helper to create a fake command object


def make_command(script_parts, output):
    cmd = MagicMock()
    cmd.script_parts = script_parts
    cmd.output = output
    return cmd


# --- Statement Coverage ---

# Every executable statement is reached by covering both True and False cases.

def test_statement_both_true():
    # 'push' in script_parts: True, 'set-upstream' in output: True
    # A correct match SHOULD return True when both conditions hold
    cmd = make_command(['git', 'push'], 'fatal: set-upstream ...')
    assert match(cmd) is True


def test_statement_push_missing():
    # 'push' not in script_parts -> entire expression is False
    cmd = make_command(['git', 'fetch'], 'fatal: set-upstream ...')
    assert match(cmd) is False


def test_statement_set_upstream_missing():
    # 'push' in script_parts but 'set-upstream' not in output -> False
    cmd = make_command(['git', 'push'], 'Everything up-to-date')
    assert match(cmd) is False


# --- Block Coverage ---

# The function has two logical blocks determined by short-circuit evaluation:
#   Block A: 'push' not in script_parts  → False immediately
#   Block B: 'push' in script_parts AND 'set-upstream' in output → True
#   Block C: 'push' in script_parts AND 'set-upstream' NOT in output → False

def test_block_push_absent():
    # Block A: short-circuit on 'push' absence
    cmd = make_command(['git', 'status'], 'set-upstream hint')
    assert match(cmd) is False  # correct match SHOULD return False


def test_block_push_present_upstream_present():
    # Block B: both conditions satisfied
    cmd = make_command(['git', 'push', 'origin'], 'hint: set-upstream to track')
    assert match(cmd) is True


def test_block_push_present_upstream_absent():
    # Block C: push present but no set-upstream hint
    cmd = make_command(['git', 'push', 'origin'], 'error: remote not found')
    assert match(cmd) is False


# --- Condition Coverage ---

# Condition 1: 'push' in command.script_parts  → True / False
# Condition 2: 'set-upstream' in command.output → True / False

def test_condition_push_true_upstream_true():
    # 'push' in script_parts: True, 'set-upstream' in output: True
    cmd = make_command(['git', 'push'], 'To set-upstream use --set-upstream')
    assert match(cmd) is True


def test_condition_push_false_upstream_true():
    # 'push' in script_parts: False, 'set-upstream' in output: True
    cmd = make_command(['git', 'pull'], 'hint: set-upstream')
    assert match(cmd) is False


def test_condition_push_true_upstream_false():
    # 'push' in script_parts: True, 'set-upstream' in output: False
    cmd = make_command(['git', 'push'], 'Everything up-to-date')
    assert match(cmd) is False


def test_condition_push_false_upstream_false():
    # 'push' in script_parts: False, 'set-upstream' in output: False
    cmd = make_command(['git', 'commit'], 'nothing to commit')
    assert match(cmd) is False


def test_condition_push_is_substring_in_list():
    # 'push' must be an exact element in script_parts, not a substring
    # e.g. 'pushd' should not match 'push'
    cmd = make_command(['git', 'pushd'], 'set-upstream hint')
    assert match(cmd) is False


def test_condition_set_upstream_substring_in_output():
    # 'set-upstream' must appear anywhere in output string
    cmd = make_command(['git', 'push'], 'use --set-upstream to track remote branch')
    assert match(cmd) is True


# --- Path Coverage ---

# Path 1: 'push' absent → return False  (short-circuit)
# Path 2: 'push' present, 'set-upstream' absent → return False
# Path 3: 'push' present, 'set-upstream' present → return True

def test_path_1_push_absent():
    # path: 'push' not in script_parts → False
    cmd = make_command([], 'set-upstream info')
    assert match(cmd) is False


def test_path_2_push_present_upstream_absent():
    # path: 'push' in script_parts → 'set-upstream' not in output → False
    cmd = make_command(['git', 'push', '--force'], 'remote: Counting objects...')
    assert match(cmd) is False


def test_path_3_push_present_upstream_present():
    # path: 'push' in script_parts → 'set-upstream' in output → True
    cmd = make_command(
        ['git', 'push', 'origin', 'my-branch'],
        'fatal: The current branch my-branch has no upstream branch.\n'
        'To push the current branch and set the remote as upstream, use\n'
        '    git push --set-upstream origin my-branch'
    )
    assert match(cmd) is True


def test_path_empty_script_parts_and_empty_output():
    # path: 'push' not in [] → False immediately; output irrelevant
    cmd = make_command([], '')
    assert match(cmd) is False


def test_path_only_push_with_empty_output():
    # path: 'push' in script_parts → 'set-upstream' not in '' → False
    cmd = make_command(['push'], '')
    assert match(cmd) is False