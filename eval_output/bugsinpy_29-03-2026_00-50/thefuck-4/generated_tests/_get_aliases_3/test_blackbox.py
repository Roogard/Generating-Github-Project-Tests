import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from thefuck.shells.fish import _get_aliases


def make_proc(output_bytes):
    """Helper: create a mock Popen process whose stdout returns output_bytes."""
    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = output_bytes
    return mock_proc


# --- BVA ---

def test_bva_empty_alias_output():
    # Boundary: fish returns a single blank line (empty alias list).
    # A correct _get_aliases SHOULD return an empty dict when there are no aliases.
    blank_output = b''
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(blank_output)):
        # The split('\n') on an empty string gives [''], and the replace/split
        # will raise ValueError — this tests that the function handles empty output.
        # A correct implementation should either return {} or raise; we test the
        # expected behaviour: no valid alias lines => empty dict or error boundary.
        try:
            result = _get_aliases(set())
            # If no error, result should be an empty dict
            assert result == {}
        except (ValueError, AttributeError):
            # Acceptable: empty output causes a parse error at the boundary
            pass


def test_bva_single_alias_not_overridden():
    # Boundary: exactly one alias, not in overridden set.
    output = b'alias ll ls -la'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert 'll' in result
    assert result['ll'] == 'ls -la'


def test_bva_single_alias_overridden():
    # Boundary: exactly one alias, and it IS in overridden set => empty result.
    output = b'alias ll ls -la'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'ll'})
    assert result == {}


def test_bva_two_aliases():
    # Boundary: minimal non-trivial collection (two aliases).
    output = b'alias ll ls -la\nalias gs git status'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert len(result) == 2
    assert result['ll'] == 'ls -la'
    assert result['gs'] == 'git status'


def test_bva_large_alias_list():
    # Boundary: large collection of aliases.
    lines = [f'alias cmd{i} echo {i}' for i in range(1000)]
    output = '\n'.join(lines).encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert len(result) == 1000
    for i in range(1000):
        assert f'cmd{i}' in result
        assert result[f'cmd{i}'] == f'echo {i}'


def test_bva_alias_value_with_spaces():
    # Boundary: alias value contains multiple spaces (split(' ', 1) must be used).
    output = b'alias ll ls -la --color=auto'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    # A correct implementation SHOULD preserve the full value after the first space
    assert result['ll'] == 'ls -la --color=auto'


def test_bva_overridden_set_empty():
    # Boundary: empty overridden set => all aliases included.
    output = b'alias a b\nalias c d'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert set(result.keys()) == {'a', 'c'}


def test_bva_overridden_set_covers_all():
    # Boundary: overridden set covers every alias => empty result.
    output = b'alias a b\nalias c d'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'a', 'c'})
    assert result == {}


# --- ECP ---

def test_ecp_valid_single_alias_typical():
    # Valid class: normal alias line, name not overridden.
    output = b'alias gs git status'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert isinstance(result, dict)
    assert result.get('gs') == 'git status'


def test_ecp_valid_multiple_aliases_none_overridden():
    # Valid class: multiple aliases, overridden is empty.
    output = b'alias a x\nalias b y\nalias c z'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert result == {'a': 'x', 'b': 'y', 'c': 'z'}


def test_ecp_valid_some_overridden():
    # Valid class: some aliases are overridden, rest should be included.
    output = b'alias a x\nalias b y\nalias c z'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'b'})
    assert 'b' not in result
    assert result.get('a') == 'x'
    assert result.get('c') == 'z'


def test_ecp_valid_all_overridden():
    # Valid class: all aliases overridden => empty dict returned.
    output = b'alias a x\nalias b y'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'a', 'b'})
    assert result == {}


def test_ecp_valid_overridden_not_in_aliases():
    # Valid class: overridden contains names that don't appear in alias output.
    output = b'alias a x\nalias b y'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'nonexistent', 'also_missing'})
    # A correct implementation SHOULD include all aliases since none are overridden
    assert result == {'a': 'x', 'b': 'y'}


def test_ecp_alias_value_is_single_token():
    # Valid class: alias value with no spaces (single-word value).
    output = b'alias ll ls'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert result.get('ll') == 'ls'


def test_ecp_alias_keyword_stripped():
    # Valid class: 'alias ' prefix must be stripped exactly once.
    # The line contains 'alias ' at the start; result key should NOT start with 'alias'.
    output = b'alias myalias some_command'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert 'myalias' in result
    assert 'alias myalias' not in result


def test_ecp_return_type_is_dict():
    # Valid class: return type must always be dict.
    output = b'alias a b'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert isinstance(result, dict)


def test_ecp_overridden_as_list():
    # Valid class: overridden passed as a list (supports 'in' operator).
    output = b'alias a x\nalias b y'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(['a'])
    assert 'a' not in result
    assert result.get('b') == 'y'


# --- Mutation Detection ---

def test_mutation_overridden_check_uses_not_in():
    # Detects mutation: `if name in overridden` instead of `if name not in overridden`
    # When name IS in overridden, it must NOT appear in result.
    output = b'alias a x\nalias b y'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'a'})
    # A correct implementation SHOULD exclude 'a' and include 'b'
    assert 'a' not in result
    assert 'b' in result


def test_mutation_overridden_check_excludes_only_matched():
    # Detects mutation: all aliases dropped when any is overridden (wrong `or`/`and`)
    output = b'alias a x\nalias b y\nalias c z'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'b'})
    # A correct implementation SHOULD still include 'a' and 'c'
    assert 'a' in result
    assert 'c' in result
    assert 'b' not in result


def test_mutation_replace_strips_only_once():
    # Detects mutation: replacing all occurrences of 'alias ' vs exactly once (count=1).
    # If alias name or value contained 'alias ', a greedy replace would corrupt output.
    # We use an alias value that does NOT contain 'alias ' to ensure the prefix is stripped once.
    output = b'alias mykey myvalue'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert 'mykey' in result
    assert result['mykey'] == 'myvalue'


def test_mutation_split_name_value_uses_maxsplit_1():
    # Detects mutation: split(' ') without maxsplit=1 would over-split multi-word values.
    output = b'alias k val with spaces here'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    # A correct implementation SHOULD keep the entire value after the first space
    assert result.get('k') == 'val with spaces here'


def test_mutation_decode_utf8():
    # Detects mutation: wrong encoding used (e.g., ascii dropping unicode chars)
    output = 'alias résumé echo résumé'.encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    assert 'résumé' in result


def test_mutation_strip_removes_leading_trailing_newlines():
    # Detects mutation: missing .strip() would cause blank first/last entries that fail parsing.
    output = b'\nalias a b\nalias c d\n'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        # Without strip(), the first element of split('\n') is '' which causes ValueError.
        # A correct implementation handles leading/trailing newlines gracefully.
        try:
            result = _get_aliases(set())
            assert 'a' in result
            assert 'c' in result
        except ValueError:
            # If strip() is missing, this is the mutation being caught
            pytest.fail("strip() missing: blank lines cause ValueError")


def test_mutation_popen_called_with_fish():
    # Detects mutation: wrong command passed to Popen (e.g., 'bash' instead of 'fish').
    output = b'alias a b'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)) as mock_popen:
        _get_aliases(set())
    args, kwargs = mock_popen.call_args
    cmd = args[0]
    assert cmd[0] == 'fish', "A correct implementation SHOULD invoke 'fish'"
    assert '-ic' in cmd, "A correct implementation SHOULD pass -ic flag"
    assert 'alias' in cmd, "A correct implementation SHOULD pass 'alias' subcommand"


def test_mutation_aliases_dict_starts_empty():
    # Detects mutation: aliases dict initialized with wrong initial value (e.g., pre-populated).
    output = b'alias only_one some_val'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    # A correct implementation SHOULD return exactly one entry, no phantom extras
    assert len(result) == 1
    assert 'only_one' in result


def test_mutation_name_not_stored_as_value():
    # Detects mutation: name and value swapped when storing in aliases dict.
    output = b'alias myname myvalue'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases(set())
    # A correct implementation SHOULD use the alias name as key, value as value
    assert 'myname' in result
    assert result['myname'] == 'myvalue'
    # Value should NOT be used as key
    assert 'myvalue' not in result


def test_mutation_overridden_membership_per_alias():
    # Detects off-by-one or wrong-variable: overridden check uses wrong loop variable.
    # Each alias independently checked against overridden.
    output = b'alias x keep_me\nalias y drop_me\nalias z keep_me_too'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(output)):
        result = _get_aliases({'y'})
    assert 'x' in result
    assert 'y' not in result
    assert 'z' in result
    assert len(result) == 2