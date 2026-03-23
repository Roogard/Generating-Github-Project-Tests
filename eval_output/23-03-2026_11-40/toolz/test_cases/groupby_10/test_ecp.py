import pytest
from toolz.itertoolz import nth

# Valid equivalence class: n is non-negative integer, seq is list/tuple/Sequence with length > n
def test_nth_valid_non_negative_index_with_sequence():
    assert nth(1, [10, 20, 30]) == 20

# Valid equivalence class: n is zero, seq is list/tuple/Sequence
def test_nth_valid_zero_index_with_sequence():
    assert nth(0, [10, 20, 30]) == 10

# Valid equivalence class: n is non-negative integer, seq is iterator/generator (not Sequence)
def test_nth_valid_non_negative_index_with_iterator():
    assert nth(2, iter([5, 6, 7, 8])) == 7

# Valid equivalence class: n is zero, seq is iterator/generator
def test_nth_valid_zero_index_with_iterator():
    assert nth(0, iter([5, 6, 7])) == 5

# Invalid equivalence class: n is negative integer, seq is list/tuple/Sequence
def test_nth_invalid_negative_index_with_sequence():
    with pytest.raises(IndexError):
        nth(-1, [10, 20, 30])

# Invalid equivalence class: n is negative integer, seq is iterator
def test_nth_invalid_negative_index_with_iterator():
    with pytest.raises(StopIteration):
        nth(-1, iter([10, 20, 30]))

# Invalid equivalence class: n is out of range (too large), seq is list/tuple/Sequence
def test_nth_invalid_index_out_of_range_with_sequence():
    with pytest.raises(IndexError):
        nth(5, [10, 20, 30])

# Invalid equivalence class: n is out of range (too large), seq is iterator (exhausted)
def test_nth_invalid_index_out_of_range_with_iterator():
    with pytest.raises(StopIteration):
        nth(5, iter([10, 20, 30]))

# Invalid equivalence class: n is not an integer (wrong type)
def test_nth_invalid_n_not_integer():
    with pytest.raises(TypeError):
        nth(2.5, [10, 20, 30])

# Invalid equivalence class: seq is empty list/tuple/Sequence, n is any non-negative integer
def test_nth_invalid_empty_sequence():
    with pytest.raises(IndexError):
        nth(0, [])

# Invalid equivalence class: seq is empty iterator, n is any non-negative integer
def test_nth_invalid_empty_iterator():
    with pytest.raises(StopIteration):
        nth(0, iter([]))