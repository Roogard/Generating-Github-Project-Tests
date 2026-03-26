import pytest
from python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_single_element_list():
    assert list(flatten([1])) == [1]

def test_flatten_nested_single_element_list():
    assert list(flatten([[1]])) == [1]

def test_flatten_deeply_nested_list():
    arr = [[[[[1]]]]]
    assert list(flatten(arr)) == [1]

def test_flatten_multiple_elements_mixed_nesting():
    arr = [1, [2, 3], [4, [5, 6]], 7]
    assert list(flatten(arr)) == [1, 2, 3, 4, 5, 6, 7]

def test_flatten_list_with_only_empty_sublists():
    arr = [[], [[], []], []]
    assert list(flatten(arr)) == []

def test_flatten_none_input_raises_type_error():
    with pytest.raises(TypeError):
        list(flatten(None))