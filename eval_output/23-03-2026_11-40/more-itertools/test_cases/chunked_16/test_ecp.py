import pytest
from more_itertools.more import divide

# Valid equivalence class: n = 1 (minimum valid)
def test_divide_n_1():
    g1, = divide(1, [1, 2, 3])
    assert list(g1) == [1, 2, 3]

# Valid equivalence class: n > 1, length divisible by n
def test_divide_n_greater_1_length_divisible():
    g1, g2 = divide(2, [1, 2, 3, 4])
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]

# Valid equivalence class: n > 1, length not divisible by n
def test_divide_n_greater_1_length_not_divisible():
    g1, g2, g3 = divide(3, [1, 2, 3, 4, 5])
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]
    assert list(g3) == [5]

# Valid equivalence class: length smaller than n
def test_divide_length_smaller_than_n():
    g1, g2, g3, g4 = divide(4, [1, 2])
    assert list(g1) == [1]
    assert list(g2) == [2]
    assert list(g3) == []
    assert list(g4) == []

# Valid equivalence class: empty iterable
def test_divide_empty_iterable():
    g1, g2 = divide(2, [])
    assert list(g1) == []
    assert list(g2) == []

# Valid equivalence class: iterable is a tuple (supports slicing)
def test_divide_iterable_tuple():
    g1, g2 = divide(2, (1, 2, 3, 4))
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]

# Valid equivalence class: iterable is a string (supports slicing)
def test_divide_iterable_string():
    g1, g2 = divide(2, "abcd")
    assert list(g1) == ['a', 'b']
    assert list(g2) == ['c', 'd']

# Valid equivalence class: iterable is a generator (does not support slicing)
def test_divide_iterable_generator():
    gen = (x for x in range(6))
    g1, g2, g3 = divide(3, gen)
    assert list(g1) == [0, 1]
    assert list(g2) == [2, 3]
    assert list(g3) == [4, 5]

# Invalid equivalence class: n = 0
def test_divide_n_zero():
    with pytest.raises(ValueError):
        divide(0, [1, 2, 3])

# Invalid equivalence class: n negative
def test_divide_n_negative():
    with pytest.raises(ValueError):
        divide(-1, [1, 2, 3])