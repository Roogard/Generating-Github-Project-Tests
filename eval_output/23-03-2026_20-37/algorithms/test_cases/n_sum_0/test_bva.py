import pytest
from algorithms.array.n_sum import _same_closure_default

def test_same_closure_default_with_none():
    assert _same_closure_default(None, None) == True

def test_same_closure_default_with_none_and_value():
    assert _same_closure_default(None, 5) == False

def test_same_closure_default_with_value_and_none():
    assert _same_closure_default(5, None) == False

def test_same_closure_default_with_same_integer():
    assert _same_closure_default(10, 10) == True

def test_same_closure_default_with_different_integers():
    assert _same_closure_default(10, 20) == False

def test_same_closure_default_with_same_string():
    assert _same_closure_default("hello", "hello") == True

def test_same_closure_default_with_different_strings():
    assert _same_closure_default("hello", "world") == False

def test_same_closure_default_with_same_list():
    lst = [1, 2, 3]
    assert _same_closure_default(lst, lst) == True

def test_same_closure_default_with_equal_lists_different_identity():
    assert _same_closure_default([1, 2, 3], [1, 2, 3]) == True

def test_same_closure_default_with_different_lists():
    assert _same_closure_default([1, 2, 3], [4, 5, 6]) == False

def test_same_closure_default_with_empty_string():
    assert _same_closure_default("", "") == True

def test_same_closure_default_with_empty_string_and_non_empty():
    assert _same_closure_default("", "a") == False

def test_same_closure_default_with_zero_and_false():
    assert _same_closure_default(0, False) == True

def test_same_closure_default_with_one_and_true():
    assert _same_closure_default(1, True) == True