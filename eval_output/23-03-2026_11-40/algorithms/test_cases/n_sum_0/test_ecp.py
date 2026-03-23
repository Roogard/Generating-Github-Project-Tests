import pytest
from algorithms.array.n_sum import _sum_closure_default

# Valid equivalence class: both arguments are integers
def test_sum_closure_default_integers():
    assert _sum_closure_default(3, 5) == 8

# Valid equivalence class: both arguments are floats
def test_sum_closure_default_floats():
    assert _sum_closure_default(2.5, 3.1) == 5.6

# Valid equivalence class: both arguments are strings (concatenation)
def test_sum_closure_default_strings():
    assert _sum_closure_default("hello", "world") == "helloworld"

# Valid equivalence class: both arguments are lists (concatenation)
def test_sum_closure_default_lists():
    assert _sum_closure_default([1, 2], [3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: mixed numeric types (int + float)
def test_sum_closure_default_mixed_numeric():
    assert _sum_closure_default(4, 2.5) == 6.5

# Valid equivalence class: one argument is None (if addition with None is defined by Python's behavior)
def test_sum_closure_default_with_none():
    with pytest.raises(TypeError):
        _sum_closure_default(None, 5)

# Valid equivalence class: both arguments are None
def test_sum_closure_default_both_none():
    with pytest.raises(TypeError):
        _sum_closure_default(None, None)

# Valid equivalence class: boolean values (True + True)
def test_sum_closure_default_booleans():
    assert _sum_closure_default(True, False) == 1  # True is 1, False is 0

# Valid equivalence class: complex numbers
def test_sum_closure_default_complex():
    assert _sum_closure_default(1+2j, 3+4j) == (4+6j)

# Valid equivalence class: dictionary (if Python's + is not defined, will raise TypeError)
def test_sum_closure_default_dict():
    with pytest.raises(TypeError):
        _sum_closure_default({"a": 1}, {"b": 2})