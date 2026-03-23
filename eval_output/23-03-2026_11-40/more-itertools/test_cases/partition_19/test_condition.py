from more_itertools.recipes import ncycles

# condition: n > 0? (implicit in repeat behavior) - but repeat handles n=0
# The condition is effectively: n > 0? (since repeat with n=0 yields empty)
# We'll treat the implicit condition as: "should produce items" vs "should produce empty"

# n > 0: True, iterable non-empty: True → produces repeated sequence
def test_ncycles_positive_n_nonempty_iterable():
    result = list(ncycles(["a", "b"], 3))
    assert result == ['a', 'b', 'a', 'b', 'a', 'b']

# n > 0: True, iterable empty: True → produces empty (but still n cycles of empty)
def test_ncycles_positive_n_empty_iterable():
    result = list(ncycles([], 3))
    assert result == []

# n > 0: False (n=0), iterable non-empty: True → produces empty
def test_ncycles_zero_n_nonempty_iterable():
    result = list(ncycles(["a", "b"], 0))
    assert result == []

# n > 0: False (n=0), iterable empty: True → produces empty
def test_ncycles_zero_n_empty_iterable():
    result = list(ncycles([], 0))
    assert result == []

# Additional edge case: n=1
def test_ncycles_n_one():
    result = list(ncycles(["x", "y"], 1))
    assert result == ['x', 'y']