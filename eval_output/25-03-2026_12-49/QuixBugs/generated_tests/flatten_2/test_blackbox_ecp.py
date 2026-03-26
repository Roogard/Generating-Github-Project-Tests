import pytest
from python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_flat_list_of_ints():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

def test_flatten_single_level_nested_list():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

def test_flatten_deeply_nested_list():
    nested = [[1], [[2], [3, [4]]]]
    assert list(flatten(nested)) == [1, 2, 3, 4]

def test_flatten_list_with_atomic_tuple():
    assert list(flatten([1, (2, 3), 4])) == [1, (2, 3), 4]

def test_flatten_non_list_input_raises_type_error():
    with pytest.raises(TypeError):
        list(flatten(123))

def test_flatten_list_with_none_element_raises_type_error():
    with pytest.raises(TypeError):
        list(flatten([1, None, 3]))

def test_flatten_list_with_string_element_raises_recursion_error():
    with pytest.raises(RecursionError):
        list(flatten(['abc']))   # strings are iterable, leading to infinite recursion