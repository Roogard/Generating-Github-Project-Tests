import pytest
from python_programs.flatten import flatten

# path: outer loop 0 iterations (empty array) → return immediately
def test_flatten_empty():
    result = list(flatten([]))
    assert result == []

# path: outer loop 1 iter → isinstance False → yield x (non-list scalar)
def test_flatten_single_non_list():
    result = list(flatten([1]))
    assert result == [1]

# path: outer loop many iters → all isinstance False → yield each scalar
def test_flatten_multiple_scalars():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# path: outer loop 1 iter → isinstance True → inner flatten call → inner loop 0 iters (nested empty list)
def test_flatten_single_empty_nested_list():
    result = list(flatten([[]]))
    assert result == []

# path: outer loop 1 iter → isinstance True → inner flatten call → inner loop 1 iter → isinstance False → yield
def test_flatten_single_nested_list_one_element():
    result = list(flatten([[42]]))
    assert result == [42]

# path: outer loop 1 iter → isinstance True → inner flatten call → inner loop many iters → all isinstance False
def test_flatten_single_nested_list_multiple_elements():
    result = list(flatten([[1, 2, 3]]))
    assert result == [1, 2, 3]

# path: outer loop many iters → mix of isinstance True and False
def test_flatten_mixed_scalars_and_lists():
    result = list(flatten([1, [2, 3], 4]))
    assert result == [1, 2, 3, 4]

# path: outer loop 1 iter → isinstance True → recursive flatten → isinstance True again (deeply nested)
def test_flatten_deeply_nested():
    result = list(flatten([[[1, 2], 3], [4]]))
    assert result == [1, 2, 3, 4]

# path: outer loop many iters → isinstance True for all → multiple nested lists
def test_flatten_all_nested_lists():
    result = list(flatten([[1, 2], [3, 4], [5, 6]]))
    assert result == [1, 2, 3, 4, 5, 6]

# path: outer loop 1 iter → isinstance True → deep recursion multiple levels
def test_flatten_triple_nested():
    result = list(flatten([[[1]], [[2, 3]]]))
    assert result == [1, 2, 3]

# path: outer loop many iters → isinstance False → scalars of different types (strings, ints)
def test_flatten_mixed_types():
    result = list(flatten([1, 'a', 2, 'b']))
    assert result == [1, 'a', 2, 'b']

# path: outer loop 1 iter → isinstance True → nested list with mixed scalars and deeper lists
def test_flatten_nested_mixed():
    result = list(flatten([[1, [2, 3], 4]]))
    assert result == [1, 2, 3, 4]