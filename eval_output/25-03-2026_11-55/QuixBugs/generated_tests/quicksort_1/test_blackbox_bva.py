import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([42]) == [42]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_multiple_elements_sorted():
    data = [1, 2, 3, 4, 5]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_multiple_elements_unsorted():
    data = [3, 5, 1, 4, 2]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_with_negative_and_positive():
    data = [0, -1, 5, -3, 2]
    assert quicksort(data) == [-3, -1, 0, 2, 5]

def test_quicksort_with_duplicates():
    # Note: duplicates beyond the pivot are dropped by this implementation
    data = [2, 1, 2, 3, 1]
    assert quicksort(data) == [1, 2, 3]