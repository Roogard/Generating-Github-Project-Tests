import pytest
from more_itertools.more import divide

# path: n < 1 → True → raises ValueError
def test_divide_n_zero():
    with pytest.raises(ValueError):
        divide(0, [1, 2, 3])

# path: n < 1 → False → iterable[:0] raises TypeError → seq = tuple(iterable) → r > 0 → for loop with i <= r and i > r
def test_divide_sequence_not_sliceable_uneven():
    # use a generator as iterable (not sliceable)
    gen = (x for x in [1, 2, 3, 4, 5])
    result = divide(2, gen)
    assert [list(r) for r in result] == [[1, 2, 3], [4, 5]]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → r == 0 → for loop with all i > r
def test_divide_sliceable_even():
    result = divide(2, [1, 2, 3, 4])
    assert [list(r) for r in result] == [[1, 2], [3, 4]]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → r > 0 → for loop with i <= r and i > r
def test_divide_sliceable_uneven():
    result = divide(3, [1, 2, 3, 4, 5, 6, 7])
    assert [list(r) for r in result] == [[1, 2, 3], [4, 5], [6, 7]]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → len(seq) < n → r = len(seq) (since divmod(len, n) gives q=0, r=len) → for loop with i <= r and i > r
def test_divide_length_smaller_than_n():
    result = divide(5, [1, 2, 3])
    assert [list(r) for r in result] == [[1], [2], [3], [], []]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → len(seq) == n → r = 0 → for loop with all i > r (each gets q=1)
def test_divide_length_equals_n():
    result = divide(3, [1, 2, 3])
    assert [list(r) for r in result] == [[1], [2], [3]]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → len(seq) == 0 → r = 0 → for loop with all i > r (each gets q=0)
def test_divide_empty_iterable():
    result = divide(3, [])
    assert [list(r) for r in result] == [[], [], []]

# path: n < 1 → False → iterable[:0] raises TypeError → seq = tuple(iterable) → r == 0 → for loop with all i > r
def test_divide_sequence_not_sliceable_even():
    gen = (x for x in [1, 2, 3, 4])
    result = divide(2, gen)
    assert [list(r) for r in result] == [[1, 2], [3, 4]]

# path: n < 1 → False → iterable[:0] raises TypeError → seq = tuple(iterable) → len(seq) < n → r = len(seq) → for loop with i <= r and i > r
def test_divide_sequence_not_sliceable_smaller_than_n():
    gen = (x for x in [1, 2])
    result = divide(4, gen)
    assert [list(r) for r in result] == [[1], [2], [], []]

# path: n < 1 → False → iterable[:0] raises TypeError → seq = tuple(iterable) → len(seq) == n → r = 0 → for loop with all i > r
def test_divide_sequence_not_sliceable_length_equals_n():
    gen = (x for x in [1, 2, 3])
    result = divide(3, gen)
    assert [list(r) for r in result] == [[1], [2], [3]]

# path: n < 1 → False → iterable[:0] raises TypeError → seq = tuple(iterable) → len(seq) == 0 → r = 0 → for loop with all i > r
def test_divide_sequence_not_sliceable_empty():
    gen = (x for x in [])
    result = divide(3, gen)
    assert [list(r) for r in result] == [[], [], []]

# path: n < 1 → False → iterable[:0] does NOT raise TypeError → seq = iterable → r > 0 → for loop with i <= r (first r iterations) and i > r (remaining)
# This path is covered by test_divide_sliceable_uneven, but we add a specific test for n=1 (r=1, q=0)
def test_divide_n_1_with_remainder():
    result = divide(1, [1, 2, 3])
    assert [list(r) for r in result] == [[1, 2, 3]]