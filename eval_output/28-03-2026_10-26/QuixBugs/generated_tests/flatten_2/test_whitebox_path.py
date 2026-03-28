import pytest
from python_programs.flatten import flatten

# path: for-loop 0 iterations (empty list) → return immediately
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []
    assert len(result) == 0

# path: for-loop 1 iteration → isinstance False → yield (scalar element)
def test_flatten_single_scalar():
    result = list(flatten([42]))
    # A correct flatten should yield the scalar value 42
    assert result == [42]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# path: for-loop many iterations → isinstance False for each → yield scalars
def test_flatten_multiple_scalars():
    result = list(flatten([1, 2, 3]))
    # A correct flatten of [1, 2, 3] should return [1, 2, 3]
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-loop 1 iteration → isinstance True → recurse → inner loop 0 iterations
def test_flatten_single_empty_nested_list():
    result = list(flatten([[]]))
    # A correct flatten of [[]] should return []
    assert result == []
    assert all(not isinstance(x, list) for x in result)

# path: for-loop 1 iteration → isinstance True → recurse → inner loop 1 iteration → isinstance False
def test_flatten_single_nested_list_one_element():
    result = list(flatten([[5]]))
    # A correct flatten of [[5]] should return [5]
    assert result == [5]
    assert len(result) == 1
    assert all(not isinstance(x, list) for x in result)

# path: for-loop 1 iteration → isinstance True → recurse → inner loop many iterations → isinstance False
def test_flatten_single_nested_list_multiple_elements():
    result = list(flatten([[1, 2, 3]]))
    # A correct flatten of [[1, 2, 3]] should return [1, 2, 3]
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-loop many iterations → mix of isinstance True and False
def test_flatten_mixed_scalars_and_nested():
    result = list(flatten([1, [2, 3], 4]))
    # A correct flatten should return [1, 2, 3, 4]
    assert result == [1, 2, 3, 4]
    assert len(result) == 4
    assert all(not isinstance(x, list) for x in result)

# path: for-loop → isinstance True → deep recursion (nested list within nested list)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    # A correct flatten should fully flatten all levels: [1, 2, 3]
    assert result == [1, 2, 3]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)

# path: for-loop many iterations → isinstance True multiple times (multiple nested lists)
def test_flatten_multiple_nested_lists():
    result = list(flatten([[1, 2], [3, 4], [5]]))
    # A correct flatten should return [1, 2, 3, 4, 5]
    assert result == [1, 2, 3, 4, 5]
    assert len(result) == 5
    assert all(not isinstance(x, list) for x in result)

# path: for-loop → isinstance True → recurse → mixed scalars and further nested lists inside
def test_flatten_complex_nested():
    result = list(flatten([1, [2, [3, 4], 5], 6]))
    # A correct flatten should return [1, 2, 3, 4, 5, 6]
    assert result == [1, 2, 3, 4, 5, 6]
    assert len(result) == 6
    assert all(not isinstance(x, list) for x in result)

# path: for-loop → isinstance False → non-integer scalar (string)
def test_flatten_string_scalars():
    result = list(flatten(["a", "b", "c"]))
    # A correct flatten of scalar strings should return them as-is
    assert result == ["a", "b", "c"]
    assert len(result) == 3
    assert all(not isinstance(x, list) for x in result)