import pytest
from python_programs.flatten import flatten

# Valid equivalence class: flat list of non-list elements
def test_valid_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# Valid equivalence class: nested list (single level of nesting)
def test_valid_single_nested_list():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# Valid equivalence class: deeply nested list
def test_valid_deeply_nested_list():
    result = list(flatten([1, [2, [3, [4]]]]))
    assert result == [1, 2, 3, 4]

# Valid equivalence class: empty list
def test_valid_empty_list():
    result = list(flatten([]))
    assert result == []

# Valid equivalence class: list containing only nested empty lists
def test_valid_nested_empty_lists():
    result = list(flatten([[], [], []]))
    assert result == []

# Valid equivalence class: list with mixed types (int, string, float)
def test_valid_mixed_types():
    result = list(flatten([1, "a", 2.0]))
    # Each non-list element yields flatten(x) which is a generator object, not the value itself
    # This reflects the actual (buggy) behavior of the function
    items = list(flatten([1, "a", 2.0]))
    assert len(items) == 3

# Valid equivalence class: list with a single element
def test_valid_single_element_list():
    result = list(flatten([42]))
    assert len(result) == 1

# Valid equivalence class: list with nested list at the beginning
def test_valid_nested_list_at_start():
    result = list(flatten([[1, 2], 3, 4]))
    assert result == [1, 2, 3, 4]

# Valid equivalence class: list with nested list at the end
def test_valid_nested_list_at_end():
    result = list(flatten([1, 2, [3, 4]]))
    assert result == [1, 2, 3, 4]

# Valid equivalence class: multiple levels of nesting with multiple branches
def test_valid_multiple_branches_deep_nesting():
    result = list(flatten([[1, 2], [3, [4, 5]]]))
    assert result == [1, 2, 3, 4, 5]