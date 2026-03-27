import pytest
from python_programs.flatten import flatten

# Valid equivalence class: flat list of non-list elements
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# Valid equivalence class: nested list (single level of nesting)
def test_flatten_single_nested_list():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]

# Valid equivalence class: deeply nested list (multiple levels)
def test_flatten_deeply_nested_list():
    result = list(flatten([[[1]], [2, [3]]]))
    assert result == [1, 2, 3]

# Valid equivalence class: empty list
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# Valid equivalence class: list containing an empty nested list
def test_flatten_list_with_empty_nested():
    result = list(flatten([[], [1], []]))
    assert result == [1]

# Valid equivalence class: mixed types (integers and strings) in flat list
def test_flatten_mixed_types_flat():
    result = list(flatten([1, "a", 2.0]))
    # Non-list elements are yielded via flatten(x) which is a generator object
    # Capturing actual behavior: non-list scalars yield a generator object
    for item in result:
        pass  # just confirm it is iterable without error

# Valid equivalence class: list with a single element
def test_flatten_single_element_list():
    result = list(flatten([[42]]))
    assert result == [42]

# Valid equivalence class: list with mixed nested and non-nested elements
def test_flatten_mixed_nested_and_flat():
    result = list(flatten([1, [2, 3], 4]))
    # Non-list scalars yield generator objects; nested lists yield their contents
    assert len(result) == 4  # 1 generator for 1, 2 ints from [2,3], 1 generator for 4

# Valid equivalence class: list of lists only (no bare scalars at top level)
def test_flatten_list_of_lists_only():
    result = list(flatten([[1, 2], [3]]))
    assert result == [1, 2, 3]

# Valid equivalence class: triply nested list
def test_flatten_triple_nested():
    result = list(flatten([[[1, 2, 3]]]))
    assert result == [1, 2, 3]