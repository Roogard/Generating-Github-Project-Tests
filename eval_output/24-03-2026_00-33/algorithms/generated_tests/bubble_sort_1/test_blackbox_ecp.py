import pytest
from algorithms.sorting.bubble_sort import bubble_sort

# Valid equivalence class: empty list
def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []

# Valid equivalence class: single element list
def test_bubble_sort_single_element():
    assert bubble_sort([5]) == [5]

# Valid equivalence class: list already sorted ascending
def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: list sorted descending
def test_bubble_sort_reverse_sorted():
    assert bubble_sort([4, 3, 2, 1]) == [1, 2, 3, 4]

# Valid equivalence class: list with random order
def test_bubble_sort_random_order():
    assert bubble_sort([3, 1, 4, 1, 5, 9, 2]) == [1, 1, 2, 3, 4, 5, 9]

# Valid equivalence class: list with duplicate values
def test_bubble_sort_duplicates():
    assert bubble_sort([7, 7, 7]) == [7, 7, 7]

# Valid equivalence class: list with negative integers
def test_bubble_sort_negative_integers():
    assert bubble_sort([-5, 0, 5, -10, 10]) == [-10, -5, 0, 5, 10]