import pytest
import types
from python_programs.flatten import flatten

def test_flatten_empty_list():
    # Valid equivalence class: empty list should yield no items
    assert list(flatten([])) == []

def test_flatten_flat_list_of_non_list():
    # Valid class: flat list of atomic non-list elements yields generators
    result = list(flatten([1, 2, 3]))
    assert len(result) == 3
    assert all(isinstance(item, types.GeneratorType) for item in result)

def test_flatten_nested_lists():
    # Valid class: nested lists trigger recursive branch, but atomic leaves still yield generators
    result = list(flatten([[1, 2], [3]]))
    assert len(result) == 3
    assert all(isinstance(item, types.GeneratorType) for item in result)

def test_flatten_non_iterable_input():
    # Invalid class: non-iterable argument should error when iterated
    with pytest.raises(TypeError):
        next(flatten(1))