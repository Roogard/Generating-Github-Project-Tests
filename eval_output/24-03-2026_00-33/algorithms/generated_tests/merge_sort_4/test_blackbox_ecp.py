import pytest
from algorithms.sorting.merge_sort import merge_sort

# Valid equivalence class: empty list
def test_merge_sort_empty():
    assert merge_sort([]) == []

# Valid equivalence class: single element list
def test_merge_sort_single():
    assert merge_sort([5]) == [5]

# Valid equivalence class: already sorted list
def test_merge_sort_already_sorted():
    assert merge_sort([1, 2, 3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: reverse sorted list
def test_merge_sort_reverse_sorted():
    assert merge_sort([4, 3, 2, 1]) == [1, 2, 3, 4]

# Valid equivalence class: unsorted list with duplicates
def test_merge_sort_with_duplicates():
    assert merge_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

# Valid equivalence class: unsorted list with negative numbers
def test_merge_sort_with_negatives():
    assert merge_sort([-5, 0, 3, -2, 1]) == [-5, -2, 0, 1, 3]

# Valid equivalence class: large list (representative of typical size)
def test_merge_sort_large():
    input_list = list(range(100, 0, -1))
    expected = list(range(1, 101))
    assert merge_sort(input_list) == expected