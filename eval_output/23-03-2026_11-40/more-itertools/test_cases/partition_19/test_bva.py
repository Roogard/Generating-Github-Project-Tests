from more_itertools.recipes import ncycles

def test_ncycles_with_zero_cycles():
    assert list(ncycles([1, 2, 3], 0)) == []

def test_ncycles_with_one_cycle():
    assert list(ncycles([1, 2, 3], 1)) == [1, 2, 3]

def test_ncycles_with_two_cycles():
    assert list(ncycles([1, 2, 3], 2)) == [1, 2, 3, 1, 2, 3]

def test_ncycles_with_large_n():
    assert list(ncycles([1], 5)) == [1, 1, 1, 1, 1]

def test_ncycles_with_empty_iterable():
    assert list(ncycles([], 3)) == []

def test_ncycles_with_empty_iterable_and_zero_n():
    assert list(ncycles([], 0)) == []

def test_ncycles_with_single_element_iterable():
    assert list(ncycles([42], 1)) == [42]

def test_ncycles_with_string_iterable():
    assert list(ncycles("ab", 2)) == ['a', 'b', 'a', 'b']