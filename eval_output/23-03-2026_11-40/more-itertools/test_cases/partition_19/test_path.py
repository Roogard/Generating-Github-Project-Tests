import pytest
from more_itertools.recipes import ncycles

# path: iterable empty, n > 0 → repeat empty tuple n times → chain yields nothing
def test_ncycles_empty_iterable():
    assert list(ncycles([], 3)) == []

# path: iterable non-empty, n == 0 → repeat tuple 0 times → chain yields nothing
def test_ncycles_zero_n():
    assert list(ncycles(["a", "b"], 0)) == []

# path: iterable non-empty, n == 1 → repeat tuple 1 time → chain yields one copy
def test_ncycles_single_repetition():
    assert list(ncycles(["a", "b"], 1)) == ["a", "b"]

# path: iterable non-empty, n > 1 → repeat tuple multiple times → chain yields multiple copies
def test_ncycles_multiple_repetitions():
    assert list(ncycles(["a", "b"], 3)) == ["a", "b", "a", "b", "a", "b"]

# path: iterable non-empty, n > 1, iterable is a generator → tuple consumes it once, repeats n times
def test_ncycles_with_generator():
    gen = (x for x in range(3))
    result = list(ncycles(gen, 2))
    assert result == [0, 1, 2, 0, 1, 2]

# path: iterable non-empty, n > 1, iterable is a string (sequence) → tuple converts, repeats n times
def test_ncycles_with_string():
    assert list(ncycles("ab", 2)) == ["a", "b", "a", "b"]