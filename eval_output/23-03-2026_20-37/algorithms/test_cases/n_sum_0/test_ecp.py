import pytest

def _same_closure_default(a, b):
    return a == b

# Valid equivalence class: two equal values (any type)
def test_same_closure_default_equal_values():
    assert _same_closure_default(5, 5) == True

# Valid equivalence class: two different values (any type)
def test_same_closure_default_different_values():
    assert _same_closure_default(5, 10) == False

# Valid equivalence class: equal strings
def test_same_closure_default_equal_strings():
    assert _same_closure_default("hello", "hello") == True

# Valid equivalence class: different strings
def test_same_closure_default_different_strings():
    assert _same_closure_default("hello", "world") == False

# Valid equivalence class: equal lists (same reference not required, equality by ==)
def test_same_closure_default_equal_lists():
    assert _same_closure_default([1, 2], [1, 2]) == True

# Valid equivalence class: different lists
def test_same_closure_default_different_lists():
    assert _same_closure_default([1, 2], [3, 4]) == False

# Valid equivalence class: None values (both None)
def test_same_closure_default_both_none():
    assert _same_closure_default(None, None) == True

# Valid equivalence class: None vs non-None
def test_same_closure_default_none_vs_value():
    assert _same_closure_default(None, 42) == False