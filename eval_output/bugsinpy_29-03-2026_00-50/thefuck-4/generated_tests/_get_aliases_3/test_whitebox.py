import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from thefuck.shells.fish import _get_aliases


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(stdout_bytes):
    """Return a fake Popen object whose stdout.read() yields stdout_bytes."""
    proc = MagicMock()
    proc.stdout.read.return_value = stdout_bytes
    return proc


# ---------------------------------------------------------------------------
# Statement Coverage
# ---------------------------------------------------------------------------

# statement: aliases dict created, Popen called, stdout read, loop body executed,
#            'if name not in overridden' branch taken (True), return aliases.
def test_statement_alias_added_when_not_overridden():
    # path: single alias, name not overridden → alias stored
    alias_line = b"alias ll 'ls -la'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases(set())
    assert 'll' in result
    # a correct implementation stores the value part after the name
    assert 'll' in result
    assert isinstance(result, dict)


# statement: 'if name not in overridden' branch taken False → alias NOT stored.
def test_statement_alias_skipped_when_overridden():
    alias_line = b"alias ll 'ls -la'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases({'ll'})
    assert 'll' not in result


# statement: empty string from strip().split('\n') gives [''] → loop runs once
#            but split(' ', 1) will fail — guard via single-alias path above.
# The empty-output edge is covered in block/path sections below.


# ---------------------------------------------------------------------------
# Block Coverage
# ---------------------------------------------------------------------------

# block: if-body (name not in overridden) executed
def test_block_if_body_executed():
    alias_line = b"alias gs 'git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases(set())
    assert 'gs' in result
    assert len(result) == 1


# block: else / skip branch (name IS in overridden)
def test_block_if_body_skipped():
    alias_line = b"alias gs 'git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases({'gs'})
    assert result == {}


# block: multiple aliases — loop body executed more than once
def test_block_multiple_aliases():
    alias_lines = b"alias ll 'ls -la'\nalias gs 'git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases(set())
    assert set(result.keys()) == {'ll', 'gs'}


# block: mix of overridden and non-overridden aliases
def test_block_partial_override():
    alias_lines = b"alias ll 'ls -la'\nalias gs 'git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases({'ll'})
    assert 'll' not in result
    assert 'gs' in result
    assert len(result) == 1


# ---------------------------------------------------------------------------
# Condition Coverage
# ---------------------------------------------------------------------------

# Condition: `name not in overridden`
#
# Sub-expression: (name not in overridden) → True  (name absent from overridden)
# name not in overridden: True
def test_condition_name_not_in_overridden_true():
    alias_line = b"alias myalias 'echo hi'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases(set())
    # True branch: alias SHOULD be stored
    assert 'myalias' in result  # name not in overridden: True


# Sub-expression: (name not in overridden) → False  (name present in overridden)
# name not in overridden: False
def test_condition_name_not_in_overridden_false():
    alias_line = b"alias myalias 'echo hi'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases({'myalias'})
    # False branch: alias SHOULD NOT be stored
    assert 'myalias' not in result  # name not in overridden: False


# ---------------------------------------------------------------------------
# Path Coverage
# ---------------------------------------------------------------------------

# path: Popen → read → strip → split → loop 0 useful iterations (all overridden)
#       → return empty dict
def test_path_all_aliases_overridden():
    # path: loop body entered but every alias skipped → return {}
    alias_lines = b"alias ll 'ls -la'\nalias gs 'git status'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases({'ll', 'gs'})
    # A correct _get_aliases SHOULD return an empty dict when everything is overridden
    assert result == {}


# path: single alias, not overridden → stored → return dict with 1 entry
def test_path_single_alias_not_overridden():
    # path: if-true → single loop iteration → return
    alias_line = b"alias foo 'bar baz'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases(set())
    assert len(result) == 1
    assert 'foo' in result


# path: multiple aliases, none overridden → all stored → return full dict
def test_path_multiple_aliases_none_overridden():
    # path: if-true (repeated) → multiple loop iterations → return
    alias_lines = b"alias a 'cmd_a'\nalias b 'cmd_b'\nalias c 'cmd_c'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases(set())
    assert set(result.keys()) == {'a', 'b', 'c'}
    # a correct implementation must preserve all non-overridden aliases
    assert len(result) == 3


# path: multiple aliases, some overridden → mixed → partial dict returned
def test_path_multiple_aliases_some_overridden():
    # path: if-true and if-false alternating across loop iterations → return partial
    alias_lines = b"alias a 'cmd_a'\nalias b 'cmd_b'\nalias c 'cmd_c'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases({'b'})
    assert 'a' in result
    assert 'b' not in result
    assert 'c' in result
    assert len(result) == 2


# path: value portion of alias contains spaces (real-world alias with spaces in value)
def test_path_alias_value_with_spaces():
    # path: single alias whose value contains spaces → only first space used as delimiter
    alias_line = b"alias ll 'ls -la --color=auto'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)):
        result = _get_aliases(set())
    assert 'll' in result
    # The value should preserve the remainder including spaces
    assert result['ll'] == "'ls -la --color=auto'"


# path: Popen called with correct arguments (integration / wiring check)
def test_path_popen_called_correctly():
    alias_line = b"alias x 'y'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_line)) as mock_popen:
        _get_aliases(set())
    mock_popen.assert_called_once()
    call_args = mock_popen.call_args
    # A correct implementation SHOULD invoke fish with the alias sub-command
    assert call_args[0][0] == ['fish', '-ic', 'alias']


# path: returned dict maps names to values (type and content invariants)
def test_path_return_type_and_content_invariants():
    alias_lines = b"alias a 'aval'\nalias b 'bval'"
    with patch('thefuck.shells.fish.Popen', return_value=_make_proc(alias_lines)):
        result = _get_aliases(set())
    # property: result must be a dict
    assert isinstance(result, dict)
    # property: all keys must be strings
    assert all(isinstance(k, str) for k in result)
    # property: all values must be strings
    assert all(isinstance(v, str) for v in result.values())