import pytest
from python_programs.flatten import flatten

# Valid equivalence class: empty list
def test_flatten_empty_list():
    assert list(flatten([])) == []

# Valid equivalence class: flat list of non-list elements
def test_flatten_flat_list():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

# Valid equivalence class: nested lists at multiple levels
def test_flatten_nested_list():
    nested = [1, [2, [3, 4], 5], 6]
    assert list(flatten(nested)) == [1, 2, 3, 4, 5, 6]

# Invalid equivalence class: non-iterable input
def test_flatten_non_iterable_input():
    with pytest.raises(TypeError):
        list(flatten(None))