import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO

from thefuck.shells.fish import _get_functions


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_proc(stdout_bytes: bytes):
    """Build a minimal fake Popen object whose stdout returns stdout_bytes."""
    proc = MagicMock()
    proc.stdout.read.return_value = stdout_bytes
    return proc


# --- Statement Coverage ---
# Every executable statement must run at least once.

def test_statement_basic_no_override():
    # Popen is called, stdout is read, decoded, stripped, split, dict built.
    # overridden is empty so all functions are included.
    raw = b"func_a\nfunc_b\nfunc_c"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)) as mock_popen:
        result = _get_functions(set())
    mock_popen.assert_called_once_with(
        ['fish', '-ic', 'functions'], stdout=pytest.importorskip("subprocess").PIPE,
        stderr=pytest.importorskip("thefuck.utils").DEVNULL
    )
    assert result == {"func_a": "func_a", "func_b": "func_b", "func_c": "func_c"}


def test_statement_some_overridden():
    # The `if func not in overridden` branch filters some entries.
    raw = b"func_a\nfunc_b\nfunc_c"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"func_b"})
    assert "func_b" not in result
    assert result == {"func_a": "func_a", "func_c": "func_c"}


# --- Block Coverage ---
# Two basic blocks inside the dict comprehension:
#   block A – func IS in overridden (filtered out)
#   block B – func is NOT in overridden (included)

def test_block_all_overridden():
    # block A: every function is overridden → result is empty dict
    raw = b"func_a\nfunc_b"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"func_a", "func_b"})
    assert result == {}


def test_block_none_overridden():
    # block B: no function is overridden → all included (see test_statement_basic_no_override)
    raw = b"only_func"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    assert result == {"only_func": "only_func"}


def test_block_mixed():
    # Both blocks exercised in a single call.
    raw = b"keep\nremove"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"remove"})
    assert "keep" in result       # block B exercised
    assert "remove" not in result  # block A exercised


# --- Condition Coverage ---
# The single boolean sub-expression is: `func not in overridden`
# It must be True in some test and False in another.

def test_condition_not_in_overridden_true():
    # func not in overridden → True  ⇒  function IS included
    # func_x not in {"func_y"} → True
    raw = b"func_x"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"func_y"})
    # A correct implementation must include func_x
    assert "func_x" in result


def test_condition_not_in_overridden_false():
    # func not in overridden → False  ⇒  function is EXCLUDED
    # func_x not in {"func_x"} → False
    raw = b"func_x"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"func_x"})
    # A correct implementation must exclude func_x
    assert "func_x" not in result


# --- Path Coverage ---
# There are two meaningful end-to-end paths through the comprehension loop
# (the function itself has no explicit branching beyond the comprehension filter):
#
# Path 1: stdout is empty string after strip → split produces [''] → single empty-string key (edge case)
# Path 2: multiple functions, none overridden → all in result
# Path 3: multiple functions, some overridden → partial result
# Path 4: all functions overridden → empty result

def test_path_empty_output():
    # path: Popen returns empty bytes → strip → split('\n') → [''] → '' not in overridden (True)
    # A correct _get_functions should map the empty string to itself when output is empty.
    # This is an edge case: fish returns nothing useful, so the result has at most one entry "".
    raw = b""
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    # Property: result is a dict and every value equals its key
    assert isinstance(result, dict)
    for k, v in result.items():
        assert k == v


def test_path_whitespace_only_output():
    # path: stdout is only whitespace → strip → '' → split('\n') → ['']
    raw = b"   \n   "
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"some_override"})
    assert isinstance(result, dict)
    for k, v in result.items():
        assert k == v


def test_path_multiple_none_overridden():
    # path: many functions, zero overridden → all pass filter
    # path: Popen → read → decode → strip → split → comprehension (all included) → return
    raw = b"alpha\nbeta\ngamma\ndelta"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    expected = {"alpha": "alpha", "beta": "beta", "gamma": "gamma", "delta": "delta"}
    assert result == expected
    # Property: keys and values are identical
    assert all(k == v for k, v in result.items())


def test_path_multiple_some_overridden():
    # path: many functions, partial override → mixed filter results
    raw = b"a\nb\nc\nd"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"b", "d"})
    assert result == {"a": "a", "c": "c"}
    # Property: no overridden key leaks through
    assert "b" not in result
    assert "d" not in result


def test_path_all_overridden():
    # path: all functions overridden → empty result
    # (see test_block_all_overridden – not repeated, just referenced here)
    raw = b"x\ny\nz"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"x", "y", "z"})
    assert result == {}


def test_path_single_function_included():
    # path: exactly one function, not overridden → single-entry dict
    raw = b"lone_func"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    assert result == {"lone_func": "lone_func"}


def test_path_single_function_overridden():
    # path: exactly one function, overridden → empty dict
    raw = b"lone_func"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions({"lone_func"})
    assert result == {}


# --- Additional property assertions ---

def test_result_values_equal_keys():
    # A correct implementation maps each function name to itself (identity dict).
    raw = b"foo\nbar\nbaz"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    assert all(k == v for k, v in result.items())


def test_overridden_as_list():
    # overridden can be any iterable that supports `in`; a list should work.
    raw = b"func1\nfunc2\nfunc3"
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(["func2"])
    assert "func2" not in result
    assert "func1" in result
    assert "func3" in result


def test_utf8_decoding():
    # The function decodes as UTF-8; non-ASCII function names should survive.
    raw = "résumé_func\nnormal_func".encode("utf-8")
    with patch("thefuck.shells.fish.Popen", return_value=_make_proc(raw)):
        result = _get_functions(set())
    assert "résumé_func" in result
    assert "normal_func" in result
    assert all(k == v for k, v in result.items())