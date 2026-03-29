import pytest
from unittest.mock import patch, MagicMock
from thefuck.shells.fish import _get_functions


# Helper to create a mock Popen result with given stdout bytes
def _make_proc(stdout_bytes):
    proc = MagicMock()
    proc.stdout.read.return_value = stdout_bytes
    return proc


# --- Statement Coverage ---

def test_statement_basic_no_override():
    # Exercises: Popen call, read, decode, strip, split, dict comprehension
    # path: all statements execute, no function filtered
    # fish returns two functions, neither overridden
    raw = b'foo\nbar'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc) as mock_popen:
        result = _get_functions.__wrapped__(set())
    # A correct implementation should map each function name to itself
    assert result == {'foo': 'foo', 'bar': 'bar'}


def test_statement_with_override():
    # Exercises the `if func not in overridden` filter branch (excluded path)
    # 'bar' is overridden and should be excluded
    raw = b'foo\nbar\nbaz'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'bar'})
    assert 'bar' not in result
    assert result == {'foo': 'foo', 'baz': 'baz'}


# --- Block Coverage ---

def test_block_empty_output():
    # Block: fish returns empty string — after strip/split we get ['']
    # The empty string '' should not appear in valid function names;
    # a correct implementation still maps '' to '' if it isn't overridden
    raw = b''
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    # [''] split from '' — one element ''
    assert isinstance(result, dict)
    assert len(result) == 1
    assert '' in result


def test_block_all_overridden():
    # Block: every function produced by fish is in overridden → empty dict
    raw = b'foo\nbar'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'foo', 'bar'})
    # All filtered out — a correct implementation returns empty dict
    assert result == {}


def test_block_single_function_not_overridden():
    # Block: single function present, not overridden
    raw = b'only_func'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    assert result == {'only_func': 'only_func'}


def test_block_single_function_overridden():
    # Block: single function present, IS overridden
    raw = b'only_func'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'only_func'})
    assert result == {}


# --- Condition Coverage ---

def test_condition_func_not_in_overridden_true():
    # Condition: `func not in overridden` → True  (func included)
    # func='alpha', overridden={'beta'} → alpha not in overridden: True
    raw = b'alpha\nbeta'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'beta'})
    # alpha not in overridden: True → included
    assert 'alpha' in result  # func not in overridden: True
    # beta not in overridden: False → excluded
    assert 'beta' not in result  # func not in overridden: False


def test_condition_func_not_in_overridden_false():
    # Condition: `func not in overridden` → False (func excluded)
    # func='gamma', overridden={'gamma'} → gamma not in overridden: False
    raw = b'gamma'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'gamma'})
    assert 'gamma' not in result  # func not in overridden: False


def test_condition_multiple_mixed():
    # Ensures both True and False sub-expression values in one call
    # f1, f2 not overridden (True), f3 overridden (False)
    raw = b'f1\nf2\nf3'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'f3'})
    assert result == {'f1': 'f1', 'f2': 'f2'}  # f1,f2: True; f3: False


# --- Path Coverage ---

def test_path_no_functions_no_override():
    # path: Popen → read → decode → strip → split → comprehension (0 real funcs after strip on single '')
    # Degenerate: empty output means [''] list
    raw = b''
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    assert isinstance(result, dict)


def test_path_some_included_some_excluded():
    # path: Popen → read → decode → strip → split → loop includes some, excludes others → return dict
    raw = b'included\nexcluded\nalso_included'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'excluded'})
    # path: if-True for 'included', if-False for 'excluded', if-True for 'also_included'
    assert result == {'included': 'included', 'also_included': 'also_included'}
    assert 'excluded' not in result


def test_path_all_included():
    # path: Popen → read → decode → strip → split → all pass filter → return full dict
    raw = b'a\nb\nc'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    # path: if-True for every function → dict with all entries
    assert result == {'a': 'a', 'b': 'b', 'c': 'c'}
    # Property: result keys equal the list of functions produced
    assert set(result.keys()) == {'a', 'b', 'c'}
    # Property: each value equals its key
    assert all(result[k] == k for k in result)


def test_path_all_excluded():
    # path: Popen → read → decode → strip → split → all fail filter → return empty dict
    raw = b'x\ny\nz'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__({'x', 'y', 'z'})
    # path: if-False for every function → empty dict
    assert result == {}


def test_path_return_value_is_identity_map():
    # Property: for any non-overridden function, result[func] == func (identity map)
    raw = b'ls_color\nman\ncd'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    for key, value in result.items():
        assert key == value  # identity mapping invariant


def test_path_popen_called_with_correct_args():
    # Verifies Popen is invoked with correct fish command regardless of override
    from thefuck.utils import DEVNULL
    from subprocess import PIPE
    raw = b'something'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc) as mock_popen:
        _get_functions.__wrapped__(set())
    mock_popen.assert_called_once_with(
        ['fish', '-ic', 'functions'], stdout=PIPE, stderr=DEVNULL
    )


def test_path_whitespace_handling():
    # path: output with leading/trailing whitespace stripped before split
    # A correct implementation strips trailing newline/whitespace
    raw = b'func_a\nfunc_b\n'
    proc = _make_proc(raw)
    with patch('thefuck.shells.fish.Popen', return_value=proc):
        result = _get_functions.__wrapped__(set())
    # After strip, trailing '\n' is removed → no empty string entry
    assert '' not in result
    assert result == {'func_a': 'func_a', 'func_b': 'func_b'}