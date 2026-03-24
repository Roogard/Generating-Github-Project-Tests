import pytest
from algorithms.sorting.insertion_sort import insertion_sort

def test_insertion_sort_empty_list():
    assert insertion_sort([]) == []

def test_insertion_sort_single_element():
    assert insertion_sort([1]) == [1]

def test_insertion_sort_two_elements_unsorted():
    assert insertion_sort([2, 1]) == [1, 2]

def test_insertion_sort_two_elements_sorted():
    assert insertion_sort([1, 2]) == [1, 2]

def test_insertion_sort_three_elements_unsorted():
    assert insertion_sort([3, 1, 2]) == [1, 2, 3]

def test_insertion_sort_already_sorted():
    assert insertion_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_insertion_sort_reverse_sorted():
    assert insertion_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_insertion_sort_with_duplicates():
    assert insertion_sort([4, 2, 2, 8, 3, 3, 1]) == [1, 2, 2, 3, 3, 4, 8]

def test_insertion_sort_negative_numbers():
    assert insertion_sort([-3, -1, -2, -5]) == [-5, -3, -2, -1]

def test_insertion_sort_mixed_positive_negative():
    assert insertion_sort([-2, 3, -5, 1, 0]) == [-5, -2, 0, 1, 3]

def test_insertion_sort_single_negative():
    assert insertion_sort([-7]) == [-7]

def test_insertion_sort_all_identical():
    assert insertion_sort([5, 5, 5, 5]) == [5, 5, 5, 5]