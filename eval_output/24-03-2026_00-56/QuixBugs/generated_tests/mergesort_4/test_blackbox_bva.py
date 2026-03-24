import pytest
from correct_python_programs.mergesort import mergesort

def test_mergesort_empty_list():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([5]) == [5]

def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

def test_mergesort_two_elements_unsorted():
    assert mergesort([2, 1]) == [1, 2]

def test_mergesort_three_elements():
    assert mergesort([3, 1, 2]) == [1, 2, 3]

def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_mergesort_with_duplicates():
    assert mergesort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

def test_mergesort_all_equal():
    assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]

def test_mergesort_negative_numbers():
    assert mergesort([-5, 0, 3, -2, 1]) == [-5, -2, 0, 1, 3]

def test_mergesort_single_element_negative():
    assert mergesort([-10]) == [-10]

def test_mergesort_large_even_length():
    arr = list(range(100, 0, -1))
    expected = list(range(1, 101))
    assert mergesort(arr) == expected

def test_mergesort_large_odd_length():
    arr = list(range(99, 0, -1))
    expected = list(range(1, 100))
    assert mergesort(arr) == expected