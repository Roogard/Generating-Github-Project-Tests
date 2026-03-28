import pytest
from python_programs.flatten import flatten

# Valid equivalence class: flat list of integers (no nesting)
def test_flatten_flat_list():
    input_list = [1, 2, 3]
    result = list(flatten(input_list))
    # A correct flatten of a flat list should return the same elements
    assert result == [1, 2, 3]
    assert len(result) == len(input_list)
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: singly nested list
def test_flatten_singly_nested():
    input_list = [1, [2, 3], 4]
    result = list(flatten(input_list))
    # A correct flatten should produce all non-list leaf values in order
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: deeply nested list
def test_flatten_deeply_nested():
    input_list = [1, [2, [3, [4, 5]]]]
    result = list(flatten(input_list))
    # A correct flatten should unwrap all levels of nesting
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: empty list
def test_flatten_empty_list():
    result = list(flatten([]))
    # A correct flatten of an empty list should yield nothing
    assert result == []

# Valid equivalence class: nested empty lists
def test_flatten_nested_empty_lists():
    input_list = [[], [[], []]]
    result = list(flatten(input_list))
    # A correct flatten of lists containing only empty lists should yield nothing
    assert result == []
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list with mixed types (strings, ints)
def test_flatten_mixed_types():
    input_list = [1, "a", [2, "b"]]
    result = list(flatten(input_list))
    # A correct flatten should preserve all non-list elements regardless of type
    assert result == [1, "a", 2, "b"]
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list containing a single non-list element
def test_flatten_single_element():
    input_list = [42]
    result = list(flatten(input_list))
    # A correct flatten of a single-element flat list should return that element
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list where all elements are nested lists (no bare scalars at top level)
def test_flatten_all_nested():
    input_list = [[1, 2], [3, 4], [5]]
    result = list(flatten(input_list))
    # A correct flatten should extract all scalars from all sublists
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: list with duplicate values
def test_flatten_duplicates_preserved():
    input_list = [1, [1, 1], 1]
    result = list(flatten(input_list))
    # A correct flatten must preserve all duplicates
    assert result == [1, 1, 1, 1]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)