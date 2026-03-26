import pytest
import types
from python_programs.flatten import flatten

def test_flatten_empty_list():
    # Boundary: empty input list should yield no elements
    assert list(flatten([])) == []

def test_flatten_single_nonlist_element():
    # Boundary: single-element list where the element is not a list
    result = list(flatten([1]))
    # It should yield exactly one item, which is a generator (flatten(1))
    assert len(result) == 1
    assert isinstance(result[0], types.GeneratorType)

def test_flatten_multiple_mixed_elements():
    # Boundary: list with one non-list and one single-level nested list
    result = list(flatten([1, [2]]))
    # Should yield two items, both generators for the non-list and the nested element
    assert len(result) == 2
    assert all(isinstance(item, types.GeneratorType) for item in result)

def test_flatten_only_nested_empty_lists():
    # Boundary: list of empty lists should yield no elements
    assert list(flatten([[], []])) == []

def test_flatten_non_list_input_raises_type_error():
    # Boundary: non-iterable input should raise a TypeError when consumed
    with pytest.raises(TypeError):
        list(flatten(42))  # 42 is not iterable, so flatten should error on iteration