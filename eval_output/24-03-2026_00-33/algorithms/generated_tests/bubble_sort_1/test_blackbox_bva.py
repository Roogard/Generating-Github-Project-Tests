import pytest
from algorithms.sorting.bubble_sort import bubble_sort

def test_bubble_sort_empty_list():
    assert bubble_sort([]) == []

def test_bubble_sort_single_element():
    assert bubble_sort([5]) == [5]

def test_bubble_sort_two_elements_already_sorted():
    assert bubble_sort([1, 2]) == [1, 2]

def test_bubble_sort_two_elements_reverse_order():
    assert bubble_sort([2, 1]) == [1, 2]

def test_bubble_sort_three_elements():
    assert bubble_sort([3, 1, 2]) == [1, 2, 3]

def test_bubble_sort_already_sorted():
    assert bubble_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_bubble_sort_reverse_sorted():
    assert bubble_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_bubble_sort_with_duplicates():
    assert bubble_sort([4, 2, 2, 8, 3, 3, 1]) == [1, 2, 2, 3, 3, 4, 8]

def test_bubble_sort_all_identical():
    assert bubble_sort([7, 7, 7, 7]) == [7, 7, 7, 7]

def test_bubble_sort_negative_numbers():
    assert bubble_sort([-5, -1, -3, 0, 4]) == [-5, -3, -1, 0, 4]

def test_bubble_sort_large_list():
    import random
    arr = list(range(100))
    random.shuffle(arr)
    assert bubble_sort(arr) == list(range(100))