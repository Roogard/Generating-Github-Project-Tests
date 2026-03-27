import pytest
from python_programs.mergesort import mergesort

# Valid equivalence class: empty list
def test_mergesort_empty_list():
    assert mergesort([]) == []

# Valid equivalence class: single-element list
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# Valid equivalence class: already sorted list
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: reverse sorted list
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: unsorted list with distinct integers
def test_mergesort_unsorted_distinct():
    assert mergesort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# Valid equivalence class: list with duplicate elements
def test_mergesort_duplicates():
    assert mergesort([3, 3, 3, 3]) == [3, 3, 3, 3]

# Valid equivalence class: list with negative numbers
def test_mergesort_negative_numbers():
    assert mergesort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# Valid equivalence class: list with mixed negative and positive numbers
def test_mergesort_mixed_negative_positive():
    assert mergesort([-2, 3, -1, 0, 5]) == [-2, -1, 0, 3, 5]

# Valid equivalence class: list with floating point numbers
def test_mergesort_floats():
    assert mergesort([3.14, 1.41, 2.72]) == [1.41, 2.72, 3.14]

# Valid equivalence class: two-element unsorted list
def test_mergesort_two_elements_unsorted():
    assert mergesort([2, 1]) == [1, 2]