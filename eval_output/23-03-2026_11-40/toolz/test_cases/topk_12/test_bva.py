import pytest
from toolz.itertoolz import partition_all
from toolz.utils import no_default as no_pad

def test_partition_all_empty_sequence():
    assert list(partition_all(3, [])) == []

def test_partition_all_n_zero():
    # n=0 should produce an empty iterator because zip_longest with n=0 will have no iterators.
    # The function will immediately raise StopIteration and return.
    assert list(partition_all(0, [1, 2, 3])) == []

def test_partition_all_n_one():
    assert list(partition_all(1, [1, 2, 3])) == [(1,), (2,), (3,)]

def test_partition_all_n_equals_sequence_length():
    assert list(partition_all(3, [1, 2, 3])) == [(1, 2, 3)]

def test_partition_all_n_greater_than_sequence_length():
    assert list(partition_all(5, [1, 2, 3])) == [(1, 2, 3)]

def test_partition_all_sequence_length_one_less_than_multiple():
    result = list(partition_all(2, [1, 2, 3]))
    assert result == [(1, 2), (3,)]

def test_partition_all_sequence_length_one_more_than_multiple():
    result = list(partition_all(2, [1, 2, 3, 4, 5]))
    assert result == [(1, 2), (3, 4), (5,)]

def test_partition_all_large_n_with_small_sequence():
    assert list(partition_all(100, [1, 2])) == [(1, 2)]

def test_partition_all_single_element_sequence():
    assert list(partition_all(3, [42])) == [(42,)]

def test_partition_all_string_sequence():
    result = list(partition_all(2, 'abcde'))
    assert result == [('a', 'b'), ('c', 'd'), ('e',)]

def test_partition_all_generator_input():
    gen = (x for x in range(4))
    result = list(partition_all(2, gen))
    assert result == [(0, 1), (2, 3)]

def test_partition_all_exact_partition():
    result = list(partition_all(2, [1, 2, 3, 4]))
    assert result == [(1, 2), (3, 4)]

def test_partition_all_n_negative():
    # Negative n should produce an empty iterator because zip_longest with negative n will have no iterators.
    # The function will immediately raise StopIteration and return.
    assert list(partition_all(-1, [1, 2, 3])) == []