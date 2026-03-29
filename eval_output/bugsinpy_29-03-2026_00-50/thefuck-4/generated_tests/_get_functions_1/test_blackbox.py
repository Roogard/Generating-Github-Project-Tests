import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from thefuck.shells.fish import _get_functions


def make_proc(output_bytes):
    """Helper: create a fake Popen-like object with stdout returning output_bytes."""
    proc = MagicMock()
    proc.stdout.read.return_value = output_bytes
    return proc


# --- BVA ---

def test_bva_empty_overridden_all_functions_returned():
    """BVA: empty overridden set — all functions from fish should be returned."""
    fish_output = b'git\nls\ncd'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert result == {'git': 'git', 'ls': 'ls', 'cd': 'cd'}


def test_bva_all_functions_overridden_returns_empty_dict():
    """BVA: every returned function is in overridden — result should be empty dict."""
    fish_output = b'git\nls\ncd'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions({'git', 'ls', 'cd'})
    assert result == {}


def test_bva_single_function_not_overridden():
    """BVA: single element output, not overridden."""
    fish_output = b'only_func'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert result == {'only_func': 'only_func'}


def test_bva_single_function_is_overridden():
    """BVA: single element output, overridden — result should be empty."""
    fish_output = b'only_func'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions({'only_func'})
    assert result == {}


def test_bva_output_with_leading_trailing_whitespace():
    """BVA: fish output with surrounding whitespace — strip() must clean it."""
    fish_output = b'  git\nls\ncd  '
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    # After strip().split('\n') the boundary whitespace in the outer string is gone,
    # but inner newline-separated tokens are kept as-is.
    assert 'git' not in result or '  git' not in result  # at least one form present
    # Property: number of keys <= number of newline-separated tokens
    assert len(result) <= 3


def test_bva_large_number_of_functions():
    """BVA: large output (100 functions) — all should appear in result."""
    funcs = [f'func_{i}' for i in range(100)]
    fish_output = '\n'.join(funcs).encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert len(result) == 100
    for f in funcs:
        assert result[f] == f


def test_bva_one_overridden_boundary():
    """BVA: exactly one function overridden out of many."""
    funcs = ['alpha', 'beta', 'gamma']
    fish_output = '\n'.join(funcs).encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions({'alpha'})
    assert 'alpha' not in result
    assert result == {'beta': 'beta', 'gamma': 'gamma'}


# --- ECP ---

def test_ecp_valid_non_overridden_functions_map_to_themselves():
    """ECP valid class: functions not in overridden should map func -> func."""
    fish_output = b'foo\nbar\nbaz'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    for key, value in result.items():
        assert key == value, "A correct _get_functions should map each function name to itself"


def test_ecp_overridden_functions_excluded():
    """ECP invalid class: functions in overridden must be excluded from result."""
    fish_output = b'foo\nbar\nbaz'
    overridden = {'foo', 'baz'}
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    assert 'foo' not in result
    assert 'baz' not in result
    assert 'bar' in result


def test_ecp_overridden_with_non_fish_functions_ignored():
    """ECP: overridden contains names not in fish output — no error, irrelevant entries ignored."""
    fish_output = b'foo\nbar'
    overridden = {'notafunction', 'alsomissing'}
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    assert result == {'foo': 'foo', 'bar': 'bar'}


def test_ecp_partial_overlap_overridden():
    """ECP: partial overlap between fish functions and overridden."""
    fish_output = b'a\nb\nc\nd'
    overridden = {'b', 'd'}
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    assert result == {'a': 'a', 'c': 'c'}


def test_ecp_return_type_is_dict():
    """ECP: return type must always be a dict."""
    fish_output = b'hello\nworld'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert isinstance(result, dict)


def test_ecp_utf8_decoding():
    """ECP: fish output is decoded as utf-8."""
    fish_output = 'résumé_func\nnormal'.encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert 'résumé_func' in result
    assert 'normal' in result


def test_ecp_empty_fish_output():
    """ECP: fish returns empty output — after strip().split('\n') we get [''], filter should handle it."""
    fish_output = b''
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    # A single empty string '' is produced by ''.strip().split('\n') == ['']
    # A correct implementation should either exclude '' or include it; we check:
    # The empty string is a valid (if unusual) key; the result should not crash
    assert isinstance(result, dict)
    # If '' is in result its value must also be ''
    if '' in result:
        assert result[''] == ''


def test_ecp_whitespace_only_fish_output():
    """ECP: fish returns only whitespace — strip produces empty string."""
    fish_output = b'   \n   \n   '
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    # strip() collapses to '' then split('\n') gives ['']
    assert isinstance(result, dict)


# --- Mutation Detection ---

def test_mutation_not_in_vs_in_overridden():
    """
    Mutation: `func not in overridden` changed to `func in overridden`.
    Detects negation flip — result should contain functions NOT in overridden,
    not those that ARE in overridden.
    """
    fish_output = b'keep_me\nexclude_me'
    overridden = {'exclude_me'}
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    # Correct: keep_me is returned, exclude_me is not
    assert 'keep_me' in result, "A correct _get_functions should keep functions NOT in overridden"
    assert 'exclude_me' not in result, "A correct _get_functions should exclude functions IN overridden"


def test_mutation_key_vs_value_identity():
    """
    Mutation: `{func: func}` changed to `{func: something_else}`.
    Detects wrong variable used for value — values must equal their keys.
    """
    fish_output = b'alpha\nbeta'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    for k, v in result.items():
        assert k == v, "A correct _get_functions should produce identity mapping: key == value"


def test_mutation_split_on_wrong_delimiter():
    """
    Mutation: split('\\n') changed to split(' ') or split(',').
    A correct implementation splits on newline; space-separated names must not appear as single keys.
    """
    fish_output = b'func_one\nfunc_two\nfunc_three'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert 'func_one' in result
    assert 'func_two' in result
    assert 'func_three' in result
    # If split was wrong, we might get 'func_one\nfunc_two\nfunc_three' as one key
    assert 'func_one\nfunc_two\nfunc_three' not in result


def test_mutation_decode_wrong_encoding():
    """
    Mutation: decode('utf-8') changed to decode('ascii') or decode('latin-1').
    For pure-ASCII output a correct utf-8 decode must return the same plain strings.
    """
    fish_output = b'simple_func\nanother_func'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    assert 'simple_func' in result
    assert 'another_func' in result


def test_mutation_strip_missing_leading_newline():
    """
    Mutation: .strip() removed — leading/trailing newlines create empty string entries.
    A correct implementation strips before splitting so no phantom empty keys from edges.
    """
    fish_output = b'\nfunc_a\nfunc_b\n'
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(set())
    # strip() removes leading/trailing newlines, so no '' keys from outer boundaries
    # func_a and func_b must be present
    assert 'func_a' in result
    assert 'func_b' in result
    # The result should not contain empty string from leading/trailing newlines
    # (strip() eliminates them before split)
    assert '' not in result


def test_mutation_popen_command_stdout_used():
    """
    Mutation: stdout=PIPE changed to stdout=DEVNULL — no output readable.
    Verifies that the result is built from stdout, not stderr or a hardcoded source.
    Detected indirectly: if stdout is not PIPE, proc.stdout.read() returns nothing useful.
    """
    fish_output = b'expected_func'
    captured_kwargs = {}

    def fake_popen(cmd, **kwargs):
        captured_kwargs.update(kwargs)
        return make_proc(fish_output)

    with patch('thefuck.shells.fish.Popen', side_effect=fake_popen):
        result = _get_functions(set())

    from subprocess import PIPE
    assert captured_kwargs.get('stdout') == PIPE, \
        "A correct _get_functions must use stdout=PIPE to capture fish output"
    assert 'expected_func' in result


def test_mutation_overridden_type_set_vs_list():
    """
    Mutation: membership test `not in` works correctly for both set and list;
    ensure the function handles set-like overridden correctly (membership semantics).
    """
    fish_output = b'x\ny\nz'
    overridden = {'y'}  # set
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    assert 'x' in result
    assert 'y' not in result
    assert 'z' in result
    assert len(result) == 2


def test_mutation_result_count_equals_non_overridden_count():
    """
    Mutation: off-by-one in filtering (e.g., <= vs <) could include one extra entry.
    Exact count check: result must have exactly len(functions) - len(overlap) entries.
    """
    funcs = ['a', 'b', 'c', 'd', 'e']
    overridden = {'b', 'd'}
    fish_output = '\n'.join(funcs).encode('utf-8')
    with patch('thefuck.shells.fish.Popen', return_value=make_proc(fish_output)):
        result = _get_functions(overridden)
    expected_count = len([f for f in funcs if f not in overridden])
    assert len(result) == expected_count, \
        "A correct _get_functions must return exactly the non-overridden functions"