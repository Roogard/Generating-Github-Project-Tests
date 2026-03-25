import pytest
from python_programs.mergesort import mergesort

def test_mergesort_empty_list():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([42]) == [42]

def test_mergesort_two_elements_already_sorted():
    assert mergesort([1, 2]) == [1, 2]

def test_mergesort_two_elements_reverse_order():
    assert mergesort([2, 1]) == [1, 2]

def test_mergesort_two_equal_elements():
    assert mergesort([5, 5]) == [5, 5]

def test_mergesort_three_elements_mixed_order():
    assert mergesort([3, 1, 2]) == [1, 2, 3]

def test_mergesort_multiple_elements_with_negatives_and_duplicates():
    data = [0, -1, 5, 3, -1, 2]
    assert mergesort(data) == sorted(data)