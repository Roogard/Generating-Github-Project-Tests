import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_quicksort_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

# Valid equivalence class: single element list
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# Valid equivalence class: already sorted list
def test_quicksort_already_sorted():
    input_list = [1, 2, 3, 4, 5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: reverse sorted list
def test_quicksort_reverse_sorted():
    input_list = [5, 4, 3, 2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: unsorted list with distinct positive integers
def test_quicksort_unsorted_distinct_positive():
    input_list = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    # Property: all elements non-descending
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# Valid equivalence class: list with negative integers
def test_quicksort_negative_integers():
    input_list = [-3, -1, -7, -2, -5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with mixed negative and positive integers
def test_quicksort_mixed_negative_positive():
    input_list = [-3, 0, 5, -1, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Invalid equivalence class: list with duplicate elements
# (Note: quicksort drops duplicates — this tests that known behavior)
def test_quicksort_duplicate_elements():
    input_list = [3, 1, 2, 1, 3]
    result = quicksort(input_list)
    # A correct sort with duplicates preserved should equal sorted(input_list)
    # This test documents the expected correct behavior
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with all identical elements
def test_quicksort_all_identical():
    input_list = [7, 7, 7, 7]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with floating point numbers
def test_quicksort_floats():
    input_list = [3.14, 1.41, 2.71, 0.57]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: two-element unsorted list
def test_quicksort_two_elements_unsorted():
    input_list = [2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)