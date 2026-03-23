import pytest
from algorithms.sorting.merge_sort import merge_sort

# Valid equivalence class: empty list
def test_merge_sort_empty_list():
    assert merge_sort([]) == []

# Valid equivalence class: single element list
def test_merge_sort_single_element():
    assert merge_sort([5]) == [5]

# Valid equivalence class: list with two elements already sorted
def test_merge_sort_two_elements_sorted():
    assert merge_sort([1, 2]) == [1, 2]

# Valid equivalence class: list with two elements unsorted
def test_merge_sort_two_elements_unsorted():
    assert merge_sort([2, 1]) == [1, 2]

# Valid equivalence class: list with multiple elements already sorted
def test_merge_sort_multiple_elements_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: list with multiple elements reverse sorted
def test_merge_sort_multiple_elements_reverse_sorted():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: list with multiple elements random order
def test_merge_sort_multiple_elements_random():
    assert merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# Valid equivalence class: list with duplicate elements
def test_merge_sort_duplicate_elements():
    assert merge_sort([7, 7, 7, 7]) == [7, 7, 7, 7]

# Valid equivalence class: list with negative integers
def test_merge_sort_negative_integers():
    assert merge_sort([-5, 0, 3, -2, 1]) == [-5, -2, 0, 1, 3]