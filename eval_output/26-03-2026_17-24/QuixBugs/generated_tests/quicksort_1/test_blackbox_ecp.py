import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_quicksort_empty_list():
    assert quicksort([]) == []

# Valid equivalence class: single element list
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# Valid equivalence class: already sorted list
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: reverse sorted list
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: unsorted list with distinct elements
def test_quicksort_unsorted_distinct():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 2, 3, 4, 5, 6, 9]

# Valid equivalence class: list with duplicate elements
def test_quicksort_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# Valid equivalence class: list with negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# Valid equivalence class: list with mixed negative and positive numbers
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]

# Valid equivalence class: list with all identical elements
def test_quicksort_all_identical():
    assert quicksort([7, 7, 7, 7]) == [7, 7, 7, 7]

# Valid equivalence class: list with two elements in wrong order
def test_quicksort_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]