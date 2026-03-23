import pytest
from more_itertools.recipes import ncycles

# Valid equivalence class: n is a positive integer, iterable is non-empty
def test_ncycles_positive_n_nonempty_iterable():
    result = list(ncycles(["a", "b"], 3))
    assert result == ["a", "b", "a", "b", "a", "b"]

# Valid equivalence class: n is zero, iterable is non-empty
def test_ncycles_zero_n_nonempty_iterable():
    result = list(ncycles(["a", "b"], 0))
    assert result == []

# Valid equivalence class: n is a positive integer, iterable is empty
def test_ncycles_positive_n_empty_iterable():
    result = list(ncycles([], 5))
    assert result == []

# Valid equivalence class: n is zero, iterable is empty
def test_ncycles_zero_n_empty_iterable():
    result = list(ncycles([], 0))
    assert result == []

# Invalid equivalence class: n is a negative integer
def test_ncycles_negative_n():
    # ncycles does not raise ValueError for negative n; it returns empty iterator
    result = list(ncycles(["a", "b"], -1))
    assert result == []

# Invalid equivalence class: n is not an integer (float)
def test_ncycles_non_integer_n():
    # ncycles raises TypeError for float n because repeat expects integer
    with pytest.raises(TypeError):
        list(ncycles(["a", "b"], 2.5))

# Valid equivalence class: n is a large positive integer
def test_ncycles_large_n():
    result = list(ncycles([1], 10**6))
    assert len(result) == 10**6
    assert all(x == 1 for x in result)

# Valid equivalence class: iterable is a generator (consumable once)
def test_ncycles_generator_iterable():
    gen = (x for x in range(3))
    result = list(ncycles(gen, 2))
    # The generator is consumed by tuple(iterable) inside ncycles
    assert result == [0, 1, 2, 0, 1, 2]