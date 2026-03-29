import pytest
from unittest.mock import patch, MagicMock
import io

from thefuck.shells.fish import _get_aliases


def make_proc(stdout_bytes):
    """Helper to create a mock Popen object with given stdout bytes."""
    proc = MagicMock()
    proc.stdout.read.return_value = stdout_bytes
    return proc


# --- ECP ---

# ECP: Valid class — single alias, not in overridden
def test_ecp_single_alias_not_overridden():
    alias_output = b"alias ll='ls -l'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'll' in result
    assert result['ll'] == "'ls -l'"


# ECP: Valid class — multiple aliases, none overridden
def test_ecp_multiple_aliases_not_overridden():
    alias_output = b"alias ll='ls -l'\nalias la='ls -a'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'll' in result
    assert 'la' in result
    assert result['ll'] == "'ls -l'"
    assert result['la'] == "'ls -a'"


# ECP: Valid class — alias present but name is in overridden (should be excluded)
def test_ecp_alias_in_overridden_excluded():
    alias_output = b"alias ll='ls -l'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'ll'}))
    assert 'll' not in result


# ECP: Valid class — some aliases overridden, some not
def test_ecp_mixed_overridden_and_not():
    alias_output = b"alias ll='ls -l'\nalias la='ls -a'\nalias grep='grep --color'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'ll'}))
    assert 'll' not in result
    assert 'la' in result
    assert 'grep' in result


# ECP: Valid class — alias value contains spaces (split on first space only)
def test_ecp_alias_value_with_spaces():
    alias_output = b"alias gc='git commit -m'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'gc' in result
    assert result['gc'] == "'git commit -m'"


# ECP: Valid class — alias name contains 'alias' as substring (replace only first occurrence)
def test_ecp_alias_name_containing_alias_substring():
    # alias name is 'myalias', value contains 'alias' too
    alias_output = b"alias myalias='do alias stuff'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'myalias' in result
    assert result['myalias'] == "'do alias stuff'"


# ECP: Invalid class — all aliases are overridden, result is empty dict
def test_ecp_all_aliases_overridden():
    alias_output = b"alias ll='ls -l'\nalias la='ls -a'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'ll', 'la'}))
    assert result == {}


# --- BVA ---

# BVA: Empty overridden set (boundary: minimum size = 0)
def test_bva_empty_overridden_set():
    alias_output = b"alias foo='bar'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'foo' in result
    assert result['foo'] == "'bar'"


# BVA: Overridden set with exactly one element (minimum+1)
def test_bva_overridden_set_one_element_matching():
    alias_output = b"alias foo='bar'\nalias baz='qux'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'foo'}))
    assert 'foo' not in result
    assert 'baz' in result


# BVA: Overridden set with exactly one element, not matching any alias
def test_bva_overridden_set_one_element_not_matching():
    alias_output = b"alias foo='bar'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'nonexistent'}))
    assert 'foo' in result


# BVA: Single alias in output (minimum collection size)
def test_bva_single_alias_output():
    alias_output = b"alias x='y'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert len(result) == 1
    assert 'x' in result


# BVA: Large number of aliases (large collection boundary)
def test_bva_many_aliases():
    lines = [f"alias cmd{i}='val{i}'" for i in range(100)]
    alias_output = '\n'.join(lines).encode('utf-8')
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert len(result) == 100
    for i in range(100):
        assert f'cmd{i}' in result
        assert result[f'cmd{i}'] == f"'val{i}'"


# BVA: Large overridden set (all names overridden)
def test_bva_large_overridden_set():
    lines = [f"alias cmd{i}='val{i}'" for i in range(50)]
    alias_output = '\n'.join(lines).encode('utf-8')
    proc = make_proc(alias_output)
    overridden = frozenset(f'cmd{i}' for i in range(50))
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(overridden)
    assert result == {}


# BVA: Alias value that is a single character (minimum value length)
def test_bva_alias_value_single_char():
    alias_output = b"alias x='y'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert result['x'] == "'y'"


# --- Mutation Detection ---

# Mutation: 'not in' vs 'in' — if condition were flipped, overridden names would be included
def test_mutation_not_in_vs_in_overridden_check():
    """Detects mutation: `if name not in overridden` -> `if name in overridden`"""
    alias_output = b"alias ll='ls -l'\nalias la='ls -a'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset({'ll'}))
    # A correct implementation should include 'la' (not overridden) and exclude 'll' (overridden)
    assert 'la' in result
    assert 'll' not in result


# Mutation: replace count argument — if replace('alias ', '', 1) was replace('alias ', '') without count
# The behavior differs when alias name itself contains 'alias'. 
# With count=1, only the first occurrence is replaced; without count (or 0), all occurrences.
def test_mutation_replace_first_occurrence_only():
    """Detects mutation: replace('alias ', '', 1) -> replace('alias ', '') without count"""
    # alias value contains 'alias ' too — with replace all, 'alias ' in value would be stripped
    alias_output = b"alias foo='alias bar'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    # A correct implementation uses count=1, so only the leading 'alias ' is replaced
    assert 'foo' in result
    # The value should still contain 'alias'
    assert 'alias' in result['foo']


# Mutation: split(' ', 1) vs split(' ') — if split had no maxsplit, multi-space value would break
def test_mutation_split_maxsplit_preserves_value_with_spaces():
    """Detects mutation: split(' ', 1) -> split(' ') which would over-split the value"""
    alias_output = b"alias gc='git commit -m message'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    # A correct implementation splits on first space only, preserving rest of value
    assert result['gc'] == "'git commit -m message'"


# Mutation: wrong variable used — returning name instead of value, or vice versa
def test_mutation_correct_key_value_assignment():
    """Detects mutation: aliases[name] = name (wrong variable) instead of aliases[name] = value"""
    alias_output = b"alias ll='ls -l'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    # Key must be the alias name, value must be the alias value (not the name)
    assert result['ll'] == "'ls -l'"
    assert result['ll'] != 'll'


# Mutation: off-by-one in strip/split — if strip() were omitted, trailing newline in last entry
def test_mutation_strip_removes_trailing_whitespace():
    """Detects mutation: removing .strip() before .split() causing empty entry at end"""
    alias_output = b"alias ll='ls -l'\n"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    # A correct implementation strips before splitting, so no empty/broken entry
    assert 'll' in result
    # Should not have an empty string key
    assert '' not in result


# Mutation: {} vs [] — return type must be dict
def test_mutation_return_type_is_dict():
    """Detects mutation: `aliases = []` or returning wrong type"""
    alias_output = b"alias ll='ls -l'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert isinstance(result, dict)


# Mutation: stdout vs stderr — if proc.stderr.read() were used instead of proc.stdout.read()
def test_mutation_reads_stdout_not_stderr():
    """Detects mutation: proc.stderr.read() instead of proc.stdout.read()"""
    proc = MagicMock()
    proc.stdout.read.return_value = b"alias ll='ls -l'"
    proc.stderr.read.return_value = b"alias bogus='wrong'"
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    # A correct implementation reads stdout; 'll' should be present, not 'bogus'
    assert 'll' in result
    assert 'bogus' not in result


# Mutation: decode encoding — if wrong encoding used, non-ASCII aliases may break
def test_mutation_decode_utf8_handles_ascii():
    """Ensures utf-8 decode is used (ASCII is valid UTF-8 subset)"""
    alias_output = "alias foo='bar'".encode('utf-8')
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_aliases(frozenset())
    assert 'foo' in result


# Mutation: Popen command args — if 'alias' subcommand were missing or wrong
def test_mutation_popen_called_with_correct_command():
    """Detects mutation: wrong command passed to Popen (e.g., missing 'alias' arg)"""
    alias_output = b"alias ll='ls -l'"
    proc = make_proc(alias_output)
    with patch('thefuck.shells.fish.Popen', return_value=proc) as mock_popen:
        _get_aliases(frozenset())
    call_args = mock_popen.call_args
    cmd = call_args[0][0]
    assert 'fish' in cmd
    assert 'alias' in cmd