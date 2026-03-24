import pytest
from correct_python_programs.flatten import flatten

# path: outer loop 0 iterations → exit
def test_flatten_empty():
    result = list(flatten([]))
    assert result == []

# path: outer loop 1 iteration → inner if False → yield x
def test_flatten_single_non_list():
    result = list(flatten([5]))
    assert result == [5]

# path: outer loop 1 iteration → inner if True → inner recursive call (empty) → inner for loop 0 iterations
def test_flatten_single_empty_list():
    result = list(flatten([[]]))
    assert result == []

# path: outer loop 1 iteration → inner if True → inner recursive call (single non-list) → inner for loop 1 iteration (yield y)
def test_flatten_single_nested_non_list():
    result = list(flatten([[7]]))
    assert result == [7]

# path: outer loop 1 iteration → inner if True → inner recursive call (nested list) → inner for loop many iterations
def test_flatten_single_nested_list_multiple():
    result = list(flatten([[1, 2, 3]]))
    assert result == [1, 2, 3]

# path: outer loop many iterations → all inner if False → yield each x
def test_flatten_multiple_non_list():
    result = list(flatten([1, 2, 3]))
    assert result == [1, 2, 3]

# path: outer loop many iterations → first inner if True, second inner if False → mixed
def test_flatten_mixed_first_list():
    result = list(flatten([[1, 2], 3]))
    assert result == [1, 2, 3]

# path: outer loop many iterations → first inner if False, second inner if True → mixed
def test_flatten_mixed_second_list():
    result = list(flatten([1, [2, 3]]))
    assert result == [1, 2, 3]

# path: outer loop many iterations → all inner if True → all recursive calls
def test_flatten_multiple_lists():
    result = list(flatten([[1], [2], [3]]))
    assert result == [1, 2, 3]

# path: outer loop many iterations → inner if True with deeper recursion (multiple levels)
def test_flatten_deeply_nested():
    result = list(flatten([1, [2, [3, [4]], 5]]))
    assert result == [1, 2, 3, 4, 5]

# path: outer loop many iterations → inner if True with recursive call that itself has inner if True (nested list with list inside)
def test_flatten_nested_list_with_inner_list():
    result = list(flatten([[[1, 2], [3, 4]], [5]]))
    assert result == [1, 2, 3, 4, 5]