import pytest
from correct_python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_single_non_list_element():
    assert list(flatten([1])) == [1]

def test_flatten_single_nested_empty_list():
    assert list(flatten([[]])) == []

def test_flatten_single_nested_single_element():
    assert list(flatten([[5]])) == [5]

def test_flatten_flat_list_multiple_elements():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

def test_flatten_nested_one_level():
    assert list(flatten([[1, 2], [3, 4]])) == [1, 2, 3, 4]

def test_flatten_deeply_nested():
    assert list(flatten([[[[1]]], [[2, 3]], 4])) == [1, 2, 3, 4]

def test_flatten_mixed_types():
    assert list(flatten([1, [2.5, 'three'], [[True]]])) == [1, 2.5, 'three', True]

def test_flatten_with_none():
    assert list(flatten([None, [None]])) == [None, None]