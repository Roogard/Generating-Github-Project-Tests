from more_itertools.more import divide

# condition: n < 1: False (n >= 1)
def test_divide_n_positive():
    # n >= 1: False, iterable length divisible by n
    g1, g2 = divide(2, [1, 2, 3, 4])
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]

# condition: n < 1: True (n < 1)
def test_divide_n_zero_raises():
    # n < 1: True
    try:
        divide(0, [1, 2, 3])
    except ValueError as e:
        assert str(e) == 'n must be at least 1'

# condition: iterable[:0] raises TypeError: True
def test_divide_iterable_not_sliceable():
    # iterable[:0] raises TypeError: True
    def gen():
        yield from [1, 2, 3, 4]
    g1, g2 = divide(2, gen())
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]

# condition: iterable[:0] raises TypeError: False
def test_divide_iterable_sliceable():
    # iterable[:0] raises TypeError: False
    g1, g2 = divide(2, [1, 2, 3, 4])
    assert list(g1) == [1, 2]
    assert list(g2) == [3, 4]

# condition: i <= r: True (i <= remainder)
def test_divide_with_remainder_first_chunk():
    # i <= r: True for i=1, r=1
    children = divide(3, [1, 2, 3, 4, 5])
    lists = [list(c) for c in children]
    assert lists == [[1, 2], [3, 4], [5]]

# condition: i <= r: False (i > remainder)
def test_divide_with_remainder_later_chunk():
    # i <= r: False for i=3, r=1
    children = divide(3, [1, 2, 3, 4, 5])
    lists = [list(c) for c in children]
    assert lists[2] == [5]

# condition: iterable length < n: True
def test_divide_iterable_shorter_than_n():
    # iterable length < n: True
    children = divide(5, [1, 2, 3])
    lists = [list(c) for c in children]
    assert lists == [[1], [2], [3], [], []]

# condition: iterable length < n: False
def test_divide_iterable_longer_than_n():
    # iterable length < n: False
    children = divide(2, [1, 2, 3, 4])
    lists = [list(c) for c in children]
    assert lists == [[1, 2], [3, 4]]

# condition: remainder == 0: True (divisible)
def test_divide_evenly_divisible():
    # remainder == 0: True
    children = divide(2, [1, 2, 3, 4])
    lists = [list(c) for c in children]
    assert lists == [[1, 2], [3, 4]]

# condition: remainder == 0: False (not divisible)
def test_divide_not_evenly_divisible():
    # remainder == 0: False
    children = divide(3, [1, 2, 3, 4, 5])
    lists = [list(c) for c in children]
    assert lists == [[1, 2], [3, 4], [5]]