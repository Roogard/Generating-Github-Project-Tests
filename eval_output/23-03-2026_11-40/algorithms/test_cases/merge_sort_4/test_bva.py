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

def test_merge_sort_duplicate_values():
    assert merge_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

def test_merge_sort_negative_numbers():
    assert merge_sort([-3, -1, -2, 0, 2]) == [-3, -2, -1, 0, 2]

def test_merge_sort_large_list():
    import random
    large_list = [random.randint(-1000, 1000) for _ in range(1000)]
    sorted_list = sorted(large_list)
    assert merge_sort(large_list) == sorted_list