import pytest
from sorts.quick_sort import quick_sort

def test_quick_sort_empty_list():
    assert quick_sort([]) == []

def test_quick_sort_single_element():
    assert quick_sort([5]) == [5]

def test_quick_sort_two_elements():
    result = quick_sort([2, 1])
    assert result == [1, 2]

def test_quick_sort_already_sorted():
    assert quick_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quick_sort_reverse_sorted():
    assert quick_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quick_sort_with_duplicates():
    result = quick_sort([3, 1, 4, 1, 5, 9, 2, 6, 5])
    assert result == [1, 1, 2, 3, 4, 5, 5, 6, 9]

def test_quick_sort_all_equal():
    assert quick_sort([7, 7, 7, 7]) == [7, 7, 7, 7]

def test_quick_sort_negative_numbers():
    assert quick_sort([-5, -1, -3, -2, -4]) == [-5, -4, -3, -2, -1]

def test_quick_sort_mixed_positive_negative():
    result = quick_sort([-2, 5, 0, -45, 3])
    assert result == [-45, -2, 0, 3, 5]

def test_quick_sort_large_list():
    collection = list(range(100, 0, -1))
    result = quick_sort(collection)
    assert result == list(range(1, 101))