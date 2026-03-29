import pytest
from unittest.mock import patch, MagicMock
import io

from thefuck.shells.fish import _get_functions


# Helper to build a mock Popen that returns given stdout bytes
def _make_popen(stdout_content: bytes):
    mock_proc = MagicMock()
    mock_proc.stdout.read.return_value = stdout_content
    return mock_proc


# We patch subprocess.Popen and also bypass the cache decorator so each test
# runs the real function body.
def _call(overridden, stdout_content: bytes):
    """Run _get_functions with a patched Popen, bypassing the cache."""
    with patch('thefuck.shells.fish.Popen', return_value=_make_popen(stdout_content)):
        # Call the underlying function directly through the cache wrapper;
        # patch ensures the real body executes with controlled output.
        return _get_functions.__wrapped__(overridden) if hasattr(_get_functions, '__wrapped__') else _get_functions(overridden)


# Because _get_functions is decorated with @cache we need to reach the inner
# function.  The cache decorator may expose __wrapped__ or we can patch Popen
# and just call the public name (cache may be a transparent pass-through in
# tests).  We use a helper that tries both.
def call_fn(overridden, stdout_bytes: bytes):
    with patch('thefuck.shells.fish.Popen', return_value=_make_popen(stdout_bytes)) as _:
        try:
            # Try unwrapped first
            fn = _get_functions.__wrapped__
        except AttributeError:
            fn = _get_functions
        return fn(overridden)


# --- BVA ---

def test_bva_empty_stdout_returns_empty_dict():
    """BVA: fish returns no output (empty string) — result should be empty dict."""
    result = call_fn(set(), b'')
    assert isinstance(result, dict)
    assert result == {}


def test_bva_single_function_not_overridden():
    """BVA: exactly one function, not in overridden — should appear in result."""
    result = call_fn(set(), b'my_func')
    assert result == {'my_func': 'my_func'}


def test_bva_single_function_is_overridden():
    """BVA: exactly one function, and it IS in overridden — should be absent."""
    result = call_fn({'my_func'}, b'my_func')
    assert result == {}


def test_bva_two_functions_both_not_overridden():
    """BVA: min+1 boundary — two functions, neither overridden."""
    result = call_fn(set(), b'func_a\nfunc_b')
    assert result == {'func_a': 'func_a', 'func_b': 'func_b'}


def test_bva_leading_trailing_whitespace_stripped():
    """BVA: stdout with leading/trailing whitespace — strip() is called."""
    result = call_fn(set(), b'  func_a\nfunc_b  \n')
    # strip() operates on the whole string before splitting; internal spacing
    # within function names is left intact but leading/trailing newlines are removed.
    assert 'func_a' in result or '  func_a' in result  # at least present
    # A correct implementation strips the full output before splitting
    assert '' not in result  # no empty-string key from trailing newline


def test_bva_large_function_list():
    """BVA: large collection — 200 functions, none overridden."""
    funcs = [f'func_{i}' for i in range(200)]
    stdout = '\n'.join(funcs).encode('utf-8')
    result = call_fn(set(), stdout)
    assert len(result) == 200
    for f in funcs:
        assert result[f] == f


def test_bva_overridden_set_covers_all_functions():
    """BVA: overridden set equals the full function list — result must be empty."""
    funcs = ['a', 'b', 'c']
    overridden = set(funcs)
    result = call_fn(overridden, '\n'.join(funcs).encode('utf-8'))
    assert result == {}


def test_bva_overridden_set_covers_no_functions():
    """BVA: overridden is empty set — all functions returned."""
    funcs = ['x', 'y', 'z']
    result = call_fn(set(), '\n'.join(funcs).encode('utf-8'))
    assert set(result.keys()) == set(funcs)


# --- ECP ---

def test_ecp_valid_nonoverlapping_functions_and_empty_overridden():
    """ECP: valid class — non-empty function list, empty overridden."""
    result = call_fn(set(), b'ls\ncd\npwd')
    assert result == {'ls': 'ls', 'cd': 'cd', 'pwd': 'pwd'}


def test_ecp_valid_partial_overlap_with_overridden():
    """ECP: valid class — some functions overridden, some not."""
    result = call_fn({'ls', 'pwd'}, b'ls\ncd\npwd')
    assert result == {'cd': 'cd'}


def test_ecp_valid_all_overridden():
    """ECP: valid class — every returned function is in overridden."""
    result = call_fn({'ls', 'cd', 'pwd'}, b'ls\ncd\npwd')
    assert result == {}


def test_ecp_valid_none_overridden_multiple():
    """ECP: valid class — multiple functions, overridden is empty."""
    result = call_fn(set(), b'git\nhg\nsvn')
    assert set(result.keys()) == {'git', 'hg', 'svn'}
    # Values must equal keys (identity mapping)
    assert all(result[k] == k for k in result)


def test_ecp_identity_mapping_property():
    """ECP: a correct implementation maps each function name to itself."""
    result = call_fn(set(), b'alpha\nbeta\ngamma')
    for key, value in result.items():
        assert key == value, f"Expected identity mapping but got {key!r} -> {value!r}"


def test_ecp_overridden_as_list_like_structure():
    """ECP: overridden passed as a frozenset — membership test must still work."""
    result = call_fn(frozenset({'alpha'}), b'alpha\nbeta')
    assert 'alpha' not in result
    assert result == {'beta': 'beta'}


def test_ecp_non_ascii_function_name():
    """ECP: UTF-8 encoded function name — decoding must be correct."""
    result = call_fn(set(), 'función\nother'.encode('utf-8'))
    assert 'función' in result
    assert result['función'] == 'función'


# --- Mutation Detection ---

def test_mutation_not_in_vs_in_operator():
    """
    Mutation: 'func not in overridden' mutated to 'func in overridden'.
    A function NOT in overridden should appear; one IN overridden should not.
    """
    result = call_fn({'excluded'}, b'included\nexcluded')
    # Correct: 'included' present, 'excluded' absent
    assert 'included' in result, "Non-overridden function must be included"
    assert 'excluded' not in result, "Overridden function must be excluded"


def test_mutation_filter_direction():
    """
    Mutation: filter condition inverted — keeps overridden, drops non-overridden.
    """
    overridden = {'should_be_gone'}
    result = call_fn(overridden, b'should_be_gone\nshould_stay')
    assert 'should_stay' in result
    assert 'should_be_gone' not in result


def test_mutation_value_vs_key_in_dict():
    """
    Mutation: dict comprehension uses wrong expression for value,
    e.g., {func: 'constant'} or {func: None}.
    A correct implementation must use func as both key and value.
    """
    result = call_fn(set(), b'abc\ndef')
    for k, v in result.items():
        assert k == v, f"Value must equal key; got key={k!r} value={v!r}"


def test_mutation_strip_missing():
    """
    Mutation: .strip() removed — trailing newline produces empty-string key.
    A correct implementation must not include '' as a key.
    """
    result = call_fn(set(), b'func_a\nfunc_b\n')
    assert '' not in result, "Empty string must not appear as a function name"


def test_mutation_split_delimiter_wrong():
    """
    Mutation: split('\\n') replaced with split() or split(' ').
    With space-separated names, a correct newline-split yields proper keys.
    """
    result = call_fn(set(), b'alpha\nbeta\ngamma')
    # If split were on whitespace and stdout had spaces between names,
    # these three should still be distinct keys.
    assert 'alpha' in result
    assert 'beta' in result
    assert 'gamma' in result
    assert len(result) == 3


def test_mutation_decode_encoding_wrong():
    """
    Mutation: decode('ascii') or decode('latin-1') instead of decode('utf-8').
    A correct implementation decodes utf-8 properly.
    """
    result = call_fn(set(), 'résumé'.encode('utf-8'))
    assert 'résumé' in result


def test_mutation_empty_overridden_still_returns_all():
    """
    Mutation: condition always excludes (e.g., 'if func in overridden' with logic flipped).
    With empty overridden, ALL functions must be returned.
    """
    result = call_fn(set(), b'f1\nf2\nf3')
    assert len(result) == 3


def test_mutation_off_by_one_strip_split_interaction():
    """
    Mutation: strip called after split, leaving empty entries from boundary newlines.
    Correct: strip the whole string first, then split — no empty keys.
    """
    result = call_fn(set(), b'\nfunc_a\nfunc_b\n')
    assert '' not in result
    assert 'func_a' in result
    assert 'func_b' in result


def test_mutation_popen_command_receives_fish():
    """
    Mutation: wrong shell command passed (e.g., 'bash' instead of 'fish').
    We verify Popen is called with 'fish' as the executable.
    """
    with patch('thefuck.shells.fish.Popen', return_value=_make_popen(b'func')) as mock_popen:
        try:
            fn = _get_functions.__wrapped__
        except AttributeError:
            fn = _get_functions
        fn(set())
        args, kwargs = mock_popen.call_args
        cmd = args[0]
        assert cmd[0] == 'fish', f"Expected 'fish' as executable, got {cmd[0]!r}"


def test_mutation_result_is_dict_not_set_or_list():
    """
    Mutation: return type changed to set or list.
    A correct implementation must return a dict.
    """
    result = call_fn(set(), b'abc')
    assert isinstance(result, dict)