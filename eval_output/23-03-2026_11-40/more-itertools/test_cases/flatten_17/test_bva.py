```python
import pytest
from more_itertools.recipes import _sliding_window_deque

def test_sliding_window_deque_empty_iterable():
    result = list(_sliding_window_deque([], 3))
    assert result == []

def test_sliding_window_deque_iterable_shorter_than_n():
    result = list(_sliding_window_deque([1, 2], 3))
    assert result == []

def test_sliding_window_deque_iterable_length_n():
    result = list(_sliding_window_deque([1, 2, 3], 3))
    assert result == [(1, 2, 3)]

def test_sliding_window_deque_iterable_length_n_plus_one():
    result = list(_sliding_window_deque([1, 2, 3, 4], 3))
    assert result == [(1, 2, 3), (2, 3, 4)]

def test_sliding_window_deque_n_equals_one():
    result = list(_sliding_window_deque([1, 2, 3], 1))
    assert result == [(1,), (2,), (3,)]

def test_sliding_window_deque_n_equals_two():
    result = list(_sliding_window_deque([1, 2, 3], 2))
    assert result == [(1, 2), (2, 3)]

def test_sliding_window_deque_n_equals_zero():
    with pytest.raises(ValueError):
        list(_sliding_window_deque([1, 2, 3], 0))

def test_sliding_window_deque_n_negative():
    with pytest.raises(ValueError):
        list(_sliding_window_deque([1, 2, 3], -1))

def test_sliding_window_deque_large_n():
    result = list(_sliding_window_deque(range(100), 10))
    assert len(result) == 91
    assert result[0] == tuple(range(10))
    assert result[-1] == tuple(range(90, 100))

def test_sliding_window_deque_string_iterable():
    result = list(_sliding_window_deque("abcde", 3))
    assert result == [('a', 'b', 'c'), ('b', 'c', 'd'), ('c', 'd', 'e')]

def test_sliding_window_deque_generator_input():
    gen = (x for x in range(5))
    result = list(_sliding_window_deque(gen, 2))
    assert result == [(0, 1), (1, 2), (2, 3), (3, 4)]
```