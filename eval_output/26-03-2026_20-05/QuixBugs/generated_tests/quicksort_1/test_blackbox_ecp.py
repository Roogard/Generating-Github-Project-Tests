import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_empty_list():
    assert quicksort([]) == []

# Valid equivalence class: single element list
def test_single_element():
    assert quicksort([42]) == [42]

# Valid equivalence class: already sorted list
def test_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: reverse sorted list
def test_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: unsorted list with distinct positive integers
def test_unsorted_distinct_positive():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 2, 3, 4, 5, 6, 9]

# Valid equivalence class: list with all duplicate elements (note: duplicates are dropped by design)
def test_all_duplicates():
    assert quicksort([7, 7, 7, 7]) == [7]

# Valid equivalence class: list with negative integers
def test_negative_integers():
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1]

# Valid equivalence class: list with mixed negative and positive integers
def test_mixed_negative_and_positive():
    assert quicksort([-2, 3, -1, 0, 5]) == [-2, -1, 0, 3, 5]

# Valid equivalence class: list with floating point numbers
def test_float_elements():
    assert quicksort([3.14, 1.41, 2.71]) == [1.41, 2.71, 3.14]

# Valid equivalence class: list with a single duplicate mixed with distinct elements
def test_some_duplicates():
    assert quicksort([4, 2, 4, 1, 3]) == [1, 2, 3, 4]