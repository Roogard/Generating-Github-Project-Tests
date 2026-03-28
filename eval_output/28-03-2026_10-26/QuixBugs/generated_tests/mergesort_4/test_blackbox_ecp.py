import pytest
from python_programs.mergesort import mergesort

# Valid equivalence class: single-element list (already sorted trivially)
def test_single_element():
    arr = [42]
    result = mergesort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# Valid equivalence class: empty list
def test_empty_list():
    arr = []
    result = mergesort(arr)
    assert result == []
    assert len(result) == 0

# Valid equivalence class: already sorted list
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: reverse-sorted list
def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with duplicate elements
def test_with_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with all identical elements
def test_all_identical():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: two-element unsorted list
def test_two_elements_unsorted():
    arr = [9, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with negative numbers
def test_negative_numbers():
    arr = [-3, -1, -7, -2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: mixed negative and positive numbers
def test_mixed_negative_and_positive():
    arr = [3, -1, 0, -5, 4]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: large list (even size)
def test_large_even_size():
    arr = [10, 3, 15, 7, 8, 23, 74, 18]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: large list (odd size)
def test_large_odd_size():
    arr = [10, 3, 15, 7, 8, 23, 74]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Property assertion: result contains exactly the same multiset of elements
def test_preserves_multiset():
    arr = [4, 2, 4, 1, 3, 2]
    result = mergesort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)
    # No nested structures remain
    assert all(not isinstance(x, list) for x in result)