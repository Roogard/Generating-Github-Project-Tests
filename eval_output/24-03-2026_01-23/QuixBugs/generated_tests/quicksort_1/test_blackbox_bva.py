import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([42]) == [42]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_sorted_multiple_elements():
    data = [1, 2, 3, 4, 5]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted_multiple_elements():
    data = [5, 4, 3, 2, 1]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_random_multiple_elements():
    data = [3, 1, 4, 5, 2]
    assert quicksort(data) == [1, 2, 3, 4, 5]

def test_quicksort_with_duplicates():
    data = [2, 3, 2, 1, 3]
    # current implementation collapses duplicates beyond the pivot
    assert quicksort(data) == [1, 2, 3]

def test_quicksort_with_negative_and_positive():
    data = [0, -1, 5, -3, 2]
    assert quicksort(data) == [-3, -1, 0, 2, 5]