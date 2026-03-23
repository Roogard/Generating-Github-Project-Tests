import pytest
from more_itertools.more import divide

def test_divide_n_at_lower_bound():
    with pytest.raises(ValueError):
        divide(0, [1, 2, 3])

def test_divide_n_at_min_valid():
    result = divide(1, [1, 2, 3])
    assert len(result) == 1
    assert list(result[0]) == [1, 2, 3]

def test_divide_n_just_above_min():
    result = divide(2, [1, 2, 3])
    assert len(result) == 2
    assert list(result[0]) == [1, 2]
    assert list(result[1]) == [3]

def test_divide_iterable_empty():
    result = divide(3, [])
    assert len(result) == 3
    for chunk in result:
        assert list(chunk) == []

def test_divide_iterable_single_element():
    result = divide(3, [42])
    assert len(result) == 3
    assert list(result[0]) == [42]
    for chunk in result[1:]:
        assert list(chunk) == []

def test_divide_iterable_length_equals_n():
    result = divide(3, [1, 2, 3])
    assert len(result) == 3
    assert list(result[0]) == [1]
    assert list(result[1]) == [2]
    assert list(result[2]) == [3]

def test_divide_iterable_length_one_less_than_n():
    result = divide(4, [1, 2, 3])
    assert len(result) == 4
    assert list(result[0]) == [1]
    assert list(result[1]) == [2]
    assert list(result[2]) == [3]
    assert list(result[3]) == []

def test_divide_iterable_length_one_more_than_n():
    result = divide(3, [1, 2, 3, 4])
    assert len(result) == 3
    assert list(result[0]) == [1, 2]
    assert list(result[1]) == [3]
    assert list(result[2]) == [4]

def test_divide_evenly_divisible():
    result = divide(2, [1, 2, 3, 4])
    assert len(result) == 2
    assert list(result[0]) == [1, 2]
    assert list(result[1]) == [3, 4]

def test_divide_with_remainder():
    result = divide(3, [1, 2, 3, 4, 5])
    assert len(result) == 3
    assert list(result[0]) == [1, 2]
    assert list(result[1]) == [3, 4]
    assert list(result[2]) == [5]

def test_divide_n_larger_than_iterable():
    result = divide(5, [1, 2])
    assert len(result) == 5
    assert list(result[0]) == [1]
    assert list(result[1]) == [2]
    for chunk in result[2:]:
        assert list(chunk) == []

def test_divide_n_much_larger_than_iterable():
    result = divide(10, [1])
    assert len(result) == 10
    assert list(result[0]) == [1]
    for chunk in result[1:]:
        assert list(chunk) == []

def test_divide_with_string_iterable():
    result = divide(3, "abcdef")
    assert len(result) == 3
    assert list(result[0]) == ['a', 'b']
    assert list(result[1]) == ['c', 'd']
    assert list(result[2]) == ['e', 'f']

def test_divide_with_tuple_iterable():
    result = divide(2, (1, 2, 3, 4))
    assert len(result) == 2
    assert list(result[0]) == [1, 2]
    assert list(result[1]) == [3, 4]

def test_divide_with_generator():
    gen = (x for x in range(5))
    result = divide(2, gen)
    assert len(result) == 2
    assert list(result[0]) == [0, 1, 2]
    assert list(result[1]) == [3, 4]