import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_empty_list():
    result = quicksort([])
    assert result == []

# Valid equivalence class: single element list
def test_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# Valid equivalence class: already sorted list
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: reverse sorted list
def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: unsorted list with distinct elements
def test_unsorted_distinct_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    # A correct quicksort MUST preserve all elements including duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with duplicate elements
def test_duplicate_elements():
    arr = [5, 3, 5, 1, 5, 2]
    result = quicksort(arr)
    # A correct quicksort MUST preserve all duplicate values, not drop them
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: all identical elements
def test_all_identical_elements():
    arr = [7, 7, 7, 7]
    result = quicksort(arr)
    # A correct quicksort MUST return all elements including duplicates of pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with negative numbers
def test_negative_numbers():
    arr = [-3, -1, -4, -1, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with mixed positive and negative numbers
def test_mixed_positive_negative():
    arr = [-2, 3, -1, 0, 4, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with a single repeated pair
def test_two_identical_elements():
    arr = [4, 4]
    result = quicksort(arr)
    # A correct quicksort MUST preserve both copies
    assert result == sorted(arr)
    assert len(result) == len(arr)