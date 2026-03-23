import pytest
from more_itertools.recipes import _sliding_window_deque

# Paths:
# 1. n <= 0? Not in function - n is assumed >=1? Actually function expects n >=1 because of n-1 in islice.
#    But we can test n=1 (special case: window size 1).
# 2. iterable length < n-1 -> window never fills, loop never runs (0 iterations)
# 3. iterable length == n-1 -> window fills to n-1, loop runs 0 times (0 iterations)
# 4. iterable length == n -> window fills to n-1, loop runs 1 time (1 iteration)
# 5. iterable length > n -> window fills to n-1, loop runs multiple times (many iterations)

# path: n=1, window size 1, islice(iterator, 0) -> empty, window = deque([], maxlen=1), loop runs for each x in iterator
def test_sliding_window_deque_n1():
    result = list(_sliding_window_deque([10, 20, 30], 1))
    assert result == [(10,), (20,), (30,)]

# path: iterable length < n-1 (here n=3, length=1), window never fills, loop 0 iterations
def test_sliding_window_deque_short_iterable():
    result = list(_sliding_window_deque([5], 3))
    assert result == []

# path: iterable length == n-1 (here n=3, length=2), window fills to n-1, loop 0 iterations
def test_sliding_window_deque_exact_n_minus_1():
    result = list(_sliding_window_deque([5, 6], 3))
    assert result == []

# path: iterable length == n (here n=3, length=3), window fills to n-1, loop 1 iteration
def test_sliding_window_deque_exact_n():
    result = list(_sliding_window_deque([5, 6, 7], 3))
    assert result == [(5, 6, 7)]

# path: iterable length > n (here n=3, length=5), window fills to n-1, loop many iterations
def test_sliding_window_deque_long_iterable():
    result = list(_sliding_window_deque([1, 2, 3, 4, 5], 3))
    assert result == [(1, 2, 3), (2, 3, 4), (3, 4, 5)]

# Additional path: empty iterable, n>1, window never fills, loop 0 iterations
def test_sliding_window_deque_empty_iterable():
    result = list(_sliding_window_deque([], 3))
    assert result == []