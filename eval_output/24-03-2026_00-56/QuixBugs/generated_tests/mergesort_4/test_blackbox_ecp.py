import pytest
from correct_python_programs.mergesort import mergesort

# Valid equivalence class: empty list
def test_mergesort_empty_list():
    assert mergesort([]) == []

# Valid equivalence class: single-element list
def test_mergesort_single_element():
    assert mergesort([5]) == [5]

# Valid equivalence class: list with multiple elements already sorted
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: list with multiple elements reverse sorted
def test_mergesort_reverse_sorted():
    assert mergesort([4, 3, 2, 1]) == [1, 2, 3, 4]

# Valid equivalence class: list with multiple elements in random order
def test_mergesort_random_order():
    assert mergesort([3, 1, 4, 2]) == [1, 2, 3, 4]

# Valid equivalence class: list with duplicate elements
def test_mergesort_duplicate_elements():
    assert mergesort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

# Valid equivalence class: list with negative numbers
def test_mergesort_negative_numbers():
    assert mergesort([-5, 0, 3, -2]) == [-5, -2, 0, 3]

# Valid equivalence class: list with all identical elements
def test_mergesort_all_identical():
    assert mergesort([7, 7, 7]) == [7, 7, 7]

# Valid equivalence class: list with floating point numbers
def test_mergesort_floats():
    assert mergesort([3.5, 1.2, 2.8]) == [1.2, 2.8, 3.5]

# Valid equivalence class: list with mixed comparable types (e.g., ints and floats)
def test_mergesort_mixed_numeric():
    assert mergesort([3, 1.5, 2]) == [1.5, 2, 3]