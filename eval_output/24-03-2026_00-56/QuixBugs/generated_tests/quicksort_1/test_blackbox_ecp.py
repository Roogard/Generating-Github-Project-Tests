import pytest
from correct_python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_empty_list():
    assert quicksort([]) == []

# Valid equivalence class: single element list
def test_single_element():
    assert quicksort([5]) == [5]

# Valid equivalence class: already sorted list
def test_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: reverse sorted list
def test_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: list with duplicates
def test_with_duplicates():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]) == [1, 1, 2, 3, 3, 4, 5, 5, 5, 6, 9]

# Valid equivalence class: list with negative numbers
def test_with_negatives():
    assert quicksort([-5, 0, 3, -2, 7]) == [-5, -2, 0, 3, 7]

# Valid equivalence class: list with all equal elements
def test_all_equal():
    assert quicksort([7, 7, 7, 7]) == [7, 7, 7, 7]

# Valid equivalence class: list with floating point numbers
def test_floats():
    assert quicksort([3.14, 1.41, 2.71, 0.0]) == [0.0, 1.41, 2.71, 3.14]

# Valid equivalence class: list with mixed comparable types (int and float)
def test_mixed_numbers():
    assert quicksort([1, 2.5, 0, -3]) == [-3, 0, 1, 2.5]