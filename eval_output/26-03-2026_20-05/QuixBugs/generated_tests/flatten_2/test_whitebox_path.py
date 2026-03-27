import pytest
from python_programs.flatten import flatten

# path: for-loop 0 iterations (empty list) → return (generator exhausted)
def test_flatten_empty_list():
    result = list(flatten([]))
    assert result == []

# path: for-loop 1 iter → isinstance False → yield x (non-list scalar)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    assert result == [1]

# path: for-loop many iters → isinstance False for each → yield each scalar
def test_flatten_multiple_scalars():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# path: for-loop 1 iter → isinstance True → recursive flatten → inner loop 0 iters (nested empty list)
def test_flatten_single_nested_empty_list():
    result = list(flatten([[]]))
    assert result == []

# path: for-loop 1 iter → isinstance True → recursive flatten → inner loop 1 iter → yield scalar
def test_flatten_single_nested_list_one_element():
    result = list(flatten([[1]]))
    assert result == [1]

# path: for-loop 1 iter → isinstance True → recursive flatten → inner loop many iters → yield scalars
def test_flatten_single_nested_list_multiple_elements():
    result = list(flatten([[1, 2, 3]]))
    assert result == [1, 2, 3]

# path: for-loop many iters → isinstance True for some, False for others → mixed yields
def test_flatten_mixed_nested_and_scalars():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# path: for-loop → isinstance True → recursive flatten → deeply nested list (multiple recursion levels)
def test_flatten_deeply_nested():
    result = list(flatten([[1, [2, [3]]]]))
    assert result == [1, 2, 3]

# path: for-loop many iters → isinstance True → multiple nested lists each with scalars
def test_flatten_multiple_nested_lists():
    result = list(flatten([[1, 2], [3, 4], [5, 6]]))
    assert result == [1, 2, 3, 4, 5, 6]

# path: for-loop 1 iter → isinstance True → recursive flatten → mixed nested and scalar inside
def test_flatten_nested_mixed_inside():
    result = list(flatten([[1, [2], 3]]))
    assert result == [1, 2, 3]

# path: for-loop many iters → isinstance True for all → all nested lists
def test_flatten_all_nested():
    result = list(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]

# path: for-loop 1 iter → isinstance False → yield single string (non-list non-numeric)
def test_flatten_single_string_element():
    result = list(flatten(['a']))
    assert result == ['a']

# path: for-loop many iters → isinstance False → multiple strings
def test_flatten_multiple_strings():
    result = list(flatten(['a', 'b', 'c']))
    assert result == ['a', 'b', 'c']