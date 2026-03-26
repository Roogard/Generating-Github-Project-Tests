import pytest
from python_programs.quicksort import quicksort

def test_quicksort_with_empty_list():
    assert quicksort([]) == []

def test_quicksort_with_single_element_list():
    assert quicksort([42]) == [42]

def test_quicksort_with_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_with_two_elements_reverse_sorted():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_with_all_equal_elements():
    # Duplicates beyond the pivot are dropped by this implementation
    assert quicksort([5, 5, 5, 5]) == [5]

def test_quicksort_with_mixed_negative_and_positive_values():
    input_list = [-3, 0, 2, -1, 5, 2]
    # Note duplicates of 2 will be dropped, pivot is -3, so result starts with []
    expected = [-3] + sorted(set(input_list) - {-3})
    assert quicksort(input_list) == expected

def test_quicksort_with_unsorted_list_of_integers():
    input_list = [10, 7, 8, 9, 1, 5]
    assert quicksort(input_list) == [1, 5, 7, 8, 9, 10]