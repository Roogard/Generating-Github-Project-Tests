import pytest
from algorithms.sorting.merge_sort import merge_sort

def test_merge_sort_empty_list():
    assert merge_sort([]) == []

def test_merge_sort_single_element():
    assert merge_sort([5]) == [5]

def test_merge_sort_two_elements():
    assert merge_sort([2, 1]) == [1, 2]

def test_merge_sort_three_elements():
    assert merge_sort([3, 1, 2]) == [1, 2, 3]

def test_merge_sort_already_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_merge_sort_reverse_sorted():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_merge_sort_with_duplicates():
    assert merge_sort([4, 2, 4, 1, 2]) == [1, 2, 2, 4, 4]

def test_merge_sort_large_list():
    import random
    arr = list(range(1000))
    random.shuffle(arr)
    assert merge_sort(arr) == list(range(1000))

def test_merge_sort_negative_numbers():
    assert merge_sort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

def test_merge_sort_single_negative():
    assert merge_sort([-5]) == [-5]