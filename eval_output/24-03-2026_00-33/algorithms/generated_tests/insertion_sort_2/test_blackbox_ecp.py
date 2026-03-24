import pytest
from algorithms.sorting.insertion_sort import insertion_sort

# Valid equivalence class: empty list
def test_insertion_sort_empty_list():
    assert insertion_sort([]) == []

# Valid equivalence class: single element list
def test_insertion_sort_single_element():
    assert insertion_sort([5]) == [5]

# Valid equivalence class: already sorted list
def test_insertion_sort_already_sorted():
    assert insertion_sort([1, 2, 3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: reverse sorted list
def test_insertion_sort_reverse_sorted():
    assert insertion_sort([4, 3, 2, 1]) == [1, 2, 3, 4]

# Valid equivalence class: unsorted list with duplicates
def test_insertion_sort_unsorted_with_duplicates():
    assert insertion_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

# Valid equivalence class: unsorted list with negative numbers
def test_insertion_sort_unsorted_with_negatives():
    assert insertion_sort([-5, 2, -3, 0, 4]) == [-5, -3, 0, 2, 4]

# Valid equivalence class: large unsorted list
def test_insertion_sort_large_unsorted():
    assert insertion_sort([9, 7, 5, 3, 1, 0, 2, 4, 6, 8]) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]