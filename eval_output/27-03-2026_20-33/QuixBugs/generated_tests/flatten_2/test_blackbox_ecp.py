import pytest
from python_programs.flatten import flatten

# Valid equivalence class: flat list of integers (no nesting)
def test_flatten_flat_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: single-level nested list
def test_flatten_single_level_nested():
    result = list(flatten([[1, 2], [3, 4]]))
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: deeply nested list
def test_flatten_deeply_nested():
    result = list(flatten([[[1]], [[2, 3]], [[[4]]]]]))
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: mixed nesting depths
def test_flatten_mixed_nesting():
    result = list(flatten([1, [2, [3, 4]], 5]))
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: empty outer list
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

# Valid equivalence class: list containing an empty list
def test_flatten_contains_empty_list():
    result = list(flatten([[], [], []]))
    assert result == []
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list with single element (non-list)
def test_flatten_single_element():
    result = list(flatten([42]))
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list containing strings (non-list elements of a different type)
def test_flatten_strings():
    result = list(flatten(["a", "b", ["c", "d"]]))
    assert result == ["a", "b", "c", "d"]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# Invalid equivalence class: non-list non-integer yielded at top level
# The function should yield plain scalar values, not generator objects
def test_flatten_yields_plain_values_not_generators():
    result = list(flatten([1, [2, 3]]))
    # Every element must be a plain (non-generator, non-list) value
    import types
    assert all(not isinstance(x, types.GeneratorType) for x in result)
    assert all(not isinstance(x, list) for x in result)