import pytest
from python_programs.flatten import flatten

# path: for-0-iterations (empty list) → return immediately
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

# path: for-1-iteration → isinstance False → yield flatten(x) (non-list scalar)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    # A correct flatten should yield the scalar value itself
    assert len(result) == 1
    # The yielded value should be the scalar (or a generator of it)
    # We check property: no nested lists remain
    assert all(not isinstance(x, list) for x in result)

# path: for-many-iterations → all isinstance False → yield flatten(x) for each
def test_flatten_multiple_non_list_elements():
    result = list(flatten([1, 2, 3]))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-1-iteration → isinstance True → recurse → inner for-0-iterations
def test_flatten_single_empty_nested_list():
    result = list(flatten([[]]))
    assert result == []
    assert len(result) == 0

# path: for-1-iteration → isinstance True → recurse → inner for-1-iteration → isinstance False
def test_flatten_single_nested_list_single_element():
    result = list(flatten([[1]]))
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# path: for-1-iteration → isinstance True → recurse → inner for-many-iterations → isinstance False
def test_flatten_single_nested_list_multiple_elements():
    result = list(flatten([[1, 2, 3]]))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-many-iterations → mixed isinstance True and False
def test_flatten_mixed_nested_and_scalars():
    result = list(flatten([1, [2, 3], 4]))
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# path: for-many-iterations → isinstance True → recurse deeply (multi-level nesting)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-many-iterations → multiple nested lists at same level
def test_flatten_multiple_nested_lists():
    result = list(flatten([[1, 2], [3, 4], [5]]))
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# path: for-1-iteration → isinstance False → yield flatten(x) for string (non-list)
def test_flatten_string_element():
    result = list(flatten(["hello"]))
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# path: for-many-iterations → isinstance False for all → multiple types
def test_flatten_mixed_scalar_types():
    result = list(flatten([1, "two", 3.0, True]))
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# path: for-1-iteration → isinstance True → recurse → inner for-many-iterations → some isinstance True
def test_flatten_nested_list_with_sublists():
    result = list(flatten([[1, [2], 3]]))
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)