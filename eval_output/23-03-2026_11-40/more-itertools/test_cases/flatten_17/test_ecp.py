import pytest
from more_itertools.recipes import _sliding_window_deque

# Valid equivalence class: iterable with length >= n, n > 1
def test_valid_iterable_length_greater_than_n():
    result = list(_sliding_window_deque([1, 2, 3, 4], 2))
    assert result == [(1, 2), (2, 3), (3, 4)]

# Valid equivalence class: iterable with length == n, n > 1
def test_valid_iterable_length_equal_to_n():
    result = list(_sliding_window_deque([1, 2, 3], 3))
    assert result == [(1, 2, 3)]

# Valid equivalence class: iterable with length < n, n > 1
def test_valid_iterable_length_less_than_n():
    result = list(_sliding_window_deque([1, 2], 3))
    assert result == []

# Valid equivalence class: empty iterable, n > 1
def test_valid_empty_iterable():
    result = list(_sliding_window_deque([], 2))
    assert result == []

# Valid equivalence class: n == 1
def test_valid_n_equal_one():
    result = list(_sliding_window_deque([1, 2, 3], 1))
    assert result == [(1,), (2,), (3,)]

# Invalid equivalence class: n <= 0
def test_invalid_n_zero():
    with pytest.raises(ValueError):
        list(_sliding_window_deque([1, 2, 3], 0))

def test_invalid_n_negative():
    with pytest.raises(ValueError):
        list(_sliding_window_deque([1, 2, 3], -1))

# Invalid equivalence class: n is not an integer
def test_invalid_n_not_integer():
    with pytest.raises(ValueError):
        list(_sliding_window_deque([1, 2, 3], 2.5))

# Valid equivalence class: non-list iterable (e.g., generator)
def test_valid_generator_iterable():
    gen = (x for x in range(5))
    result = list(_sliding_window_deque(gen, 2))
    assert result == [(0, 1), (1, 2), (2, 3), (3, 4)]