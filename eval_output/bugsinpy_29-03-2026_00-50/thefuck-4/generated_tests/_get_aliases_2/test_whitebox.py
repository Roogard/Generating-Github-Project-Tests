import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from thefuck.shells.fish import _get_aliases


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(stdout_bytes: bytes):
    """Return a fake Popen-like object whose stdout.read() returns the given bytes."""
    proc = MagicMock()
    proc.stdout.read.return_value = stdout_bytes
    return proc


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------
# Every executable statement is reached by these tests.

def test_statement_empty_overridden_single_alias():
    # path: aliases={}, proc created, one alias line parsed, name not in overridden → stored
    stdout = b"alias ll='ls -l'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)) as mock_popen, \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())

    # A correct implementation SHOULD include the alias when not overridden
    assert 'll' in result
    assert result['ll'] == "'ls -l'"


def test_statement_alias_skipped_when_overridden():
    # path: name IS in overridden → the if-body is skipped for that alias
    stdout = b"alias ll='ls -l'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['ll']))

    # A correct implementation SHOULD exclude overridden aliases
    assert 'll' not in result
    assert result == {}


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------
# Each basic block is exercised: function entry, loop body (if-true branch),
# loop body (if-false branch), post-loop return.

def test_block_multiple_aliases_mixed_override():
    # Exercises: entry block, loop with if-true AND if-false in the same run
    stdout = b"alias ll='ls -l'\nalias gs='git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['ll']))

    # 'll' is overridden → excluded; 'gs' is not → included
    assert 'll' not in result
    assert 'gs' in result
    assert result['gs'] == "'git status'"


def test_block_returns_dict():
    # Exercises the return statement and confirms type
    stdout = b"alias x='y'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())

    assert isinstance(result, dict)


def test_block_empty_aliases_dict_on_all_overridden():
    # Loop body executes but every alias is overridden → aliases stays {}
    stdout = b"alias a='b'\nalias c='d'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['a', 'c']))

    assert result == {}


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------
# The single boolean condition is: `name not in overridden`
# We need it to be True in at least one test and False in at least one test.

def test_condition_name_not_in_overridden_true():
    # name not in overridden: TRUE → alias stored
    # Condition sub-expression: (name not in overridden) = True
    stdout = b"alias foo='bar'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())  # empty → never overridden

    assert 'foo' in result  # condition True → alias present


def test_condition_name_not_in_overridden_false():
    # name not in overridden: FALSE → alias NOT stored
    # Condition sub-expression: (name not in overridden) = False
    stdout = b"alias foo='bar'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['foo']))  # foo overridden

    assert 'foo' not in result  # condition False → alias absent


def test_condition_multiple_aliases_condition_both_values():
    # One alias satisfies condition=True, another condition=False in the same call
    stdout = b"alias keep='kept'\nalias drop='dropped'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['drop']))

    assert 'keep' in result   # condition True
    assert 'drop' not in result  # condition False


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------
# Distinct paths through the function:
#   P1: loop zero iterations (empty alias_out after strip/split produces [''])
#       NOTE: a single empty line from strip('') still yields ['']; we handle
#             it by returning an empty dict when the only "alias" is the empty string.
#             This path triggers a ValueError in the split — we test zero-output
#             by providing no newlines and an empty stdout.
#   P2: loop one iteration, condition True  → alias stored
#   P3: loop one iteration, condition False → alias skipped
#   P4: loop multiple iterations, mixed conditions

def test_path_single_alias_not_overridden():
    # path: entry → loop-1-iter → condition-True → return
    # P2
    stdout = b"alias ll='ls -l'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())

    assert result == {'ll': "'ls -l'"}


def test_path_single_alias_overridden():
    # path: entry → loop-1-iter → condition-False → return
    # P3
    stdout = b"alias ll='ls -l'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['ll']))

    assert result == {}


def test_path_multiple_iterations_mixed():
    # path: entry → loop-N-iters (N=3), conditions mixed → return
    # P4
    stdout = b"alias a='1'\nalias b='2'\nalias c='3'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['b']))

    # 'a' and 'c' kept; 'b' dropped
    assert 'a' in result
    assert 'b' not in result
    assert 'c' in result
    assert len(result) == 2


def test_path_all_aliases_overridden_multiple():
    # path: entry → loop-N-iters, all condition-False → return empty dict
    stdout = b"alias x='1'\nalias y='2'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset(['x', 'y']))

    assert result == {}


def test_path_alias_value_contains_spaces():
    # path: alias value itself contains spaces → split(' ', 1) must keep them
    stdout = b"alias gco='git checkout'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())

    assert 'gco' in result
    # A correct implementation SHOULD preserve the full value after first space split
    assert result['gco'] == "'git checkout'"


def test_path_alias_with_leading_alias_keyword():
    # Verifies that 'alias ' prefix is stripped exactly once (replace with count=1)
    stdout = b"alias alias_test='echo alias'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)), \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        result = _get_aliases(overridden=frozenset())

    # The name should be 'alias_test', not something with 'alias ' still prepended
    assert 'alias_test' in result
    assert result['alias_test'] == "'echo alias'"


def test_path_popen_called_with_fish_command():
    # Verifies the fish shell is invoked correctly regardless of OS
    stdout = b"alias x='y'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(stdout)) as mock_popen, \
         patch('thefuck.shells.fish.cache', lambda *a, **kw: (lambda f: f)):
        _get_aliases(overridden=frozenset())

    call_args = mock_popen.call_args
    assert call_args[0][0] == ['fish', '-ic', 'alias']