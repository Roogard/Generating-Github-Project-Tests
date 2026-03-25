import pytest
from python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_single_element_list():
    assert list(flatten([42])) == [42]

def test_flatten_flat_list_of_multiple_elements():
    assert list(flatten([1, 2, 3, 4, 5])) == [1, 2, 3, 4, 5]

def test_flatten_one_level_nested_list():
    input_list = [1, [2, 3], 4]
    expected = [1, 2, 3, 4]
    assert list(flatten(input_list)) == expected

def test_flatten_multi_level_nested_list():
    input_list = [1, [2, [3, 4], 5], 6]
    expected = [1, 2, 3, 4, 5, 6]
    assert list(flatten(input_list)) == expected

def test_flatten_with_empty_sublists():
    input_list = [[], [1, [], [2]], []]
    expected = [1, 2]
    assert list(flatten(input_list)) == expected