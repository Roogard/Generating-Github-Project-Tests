import pytest
from toolz.itertoolz import partition_all
from toolz.utils import no_default as no_pad

# Valid equivalence class: n is positive integer, seq is non-empty iterable
def test_partition_all_valid_nonempty_seq():
    result = list(partition_all(2, [1, 2, 3, 4]))
    assert result == [(1, 2), (3, 4)]

# Valid equivalence class: n is positive integer, seq length is multiple of n
def test_partition_all_seq_length_multiple_of_n():
    result = list(partition_all(3, [1, 2, 3, 4, 5, 6]))
    assert result == [(1, 2, 3), (4, 5, 6)]

# Valid equivalence class: n is positive integer, seq length not multiple of n (final tuple shorter)
def test_partition_all_seq_length_not_multiple_of_n():
    result = list(partition_all(2, [1, 2, 3, 4, 5]))
    assert result == [(1, 2), (3, 4), (5,)]

# Valid equivalence class: n is positive integer, seq is empty
def test_partition_all_empty_seq():
    result = list(partition_all(3, []))
    assert result == []

# Valid equivalence class: n is 1
def test_partition_all_n_equals_one():
    result = list(partition_all(1, [1, 2, 3]))
    assert result == [(1,), (2,), (3,)]

# Valid equivalence class: n larger than seq length
def test_partition_all_n_larger_than_seq_length():
    result = list(partition_all(5, [1, 2, 3]))
    assert result == [(1, 2, 3)]

# Valid equivalence class: seq is tuple (different sequence type)
def test_partition_all_seq_is_tuple():
    result = list(partition_all(2, (1, 2, 3, 4)))
    assert result == [(1, 2), (3, 4)]

# Valid equivalence class: seq is generator
def test_partition_all_seq_is_generator():
    gen = (x for x in range(5))
    result = list(partition_all(2, gen))
    assert result == [(0, 1), (2, 3), (4,)]

# Invalid equivalence class: n is zero
def test_partition_all_n_zero():
    # The function does not raise ZeroDivisionError; it will treat n=0 as a valid integer.
    # The zip_longest with n=0 creates an empty iterator, so the function yields nothing.
    result = list(partition_all(0, [1, 2, 3]))
    assert result == []

# Invalid equivalence class: n is negative integer
def test_partition_all_n_negative():
    # The function does not raise ValueError; it will treat negative n as valid.
    # zip_longest with negative n creates an empty iterator, so the function yields nothing.
    result = list(partition_all(-1, [1, 2, 3]))
    assert result == []

# Invalid equivalence class: n is not integer (float)
def test_partition_all_n_float():
    with pytest.raises(TypeError):
        list(partition_all(2.5, [1, 2, 3]))

# Invalid equivalence class: seq is None (not iterable)
def test_partition_all_seq_none():
    with pytest.raises(TypeError):
        list(partition_all(2, None))

# Invalid equivalence class: seq is integer (not iterable)
def test_partition_all_seq_integer():
    with pytest.raises(TypeError):
        list(partition_all(2, 5))