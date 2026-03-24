import pytest
from correct_python_programs.flatten import flatten

# Valid equivalence class: empty list
def test_flatten_empty_list():
    assert list(flatten([])) == []

# Valid equivalence class: flat list with no nesting
def test_flatten_flat_list():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

# Valid equivalence class: nested list one level deep
def test_flatten_one_level_nesting():
    assert list(flatten([[1, 2], [3, 4]])) == [1, 2, 3, 4]

# Valid equivalence class: deeply nested list
def test_flatten_deeply_nested():
    assert list(flatten([1, [2, [3, [4, 5]], 6]])) == [1, 2, 3, 4, 5, 6]

# Valid equivalence class: list with mixed types (non‑list elements)
def test_flatten_mixed_types():
    assert list(flatten([1, 'a', [2, 'b'], 3.5])) == [1, 'a', 2, 'b', 3.5]

# Valid equivalence class: list containing only nested empty lists
def test_flatten_nested_empty_lists():
    assert list(flatten([[], [[]], [[[]]]])) == []

# Valid equivalence class: list with single element nested
def test_flatten_single_element_nested():
    assert list(flatten([[42]])) == [42]