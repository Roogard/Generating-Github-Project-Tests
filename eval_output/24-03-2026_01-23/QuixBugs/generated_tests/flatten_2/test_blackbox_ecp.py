import pytest
from python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_flat_list_of_ints():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

def test_flatten_nested_list():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

def test_flatten_deeply_nested_list():
    assert list(flatten([[1, [2]], 3])) == [1, 2, 3]

def test_flatten_with_empty_sublists():
    assert list(flatten([[], [1, []], 2])) == [1, 2]

def test_flatten_non_iterable_raises_type_error():
    with pytest.raises(TypeError):
        list(flatten(42))

def test_flatten_none_raises_type_error():
    with pytest.raises(TypeError):
        list(flatten(None))