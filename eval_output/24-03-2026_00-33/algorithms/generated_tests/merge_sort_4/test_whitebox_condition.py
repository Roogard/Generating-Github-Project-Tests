from algorithms.sorting.merge_sort import merge_sort

# condition: len(array) <= 1: True
def test_merge_sort_empty():
    # len(array) <= 1: True
    assert merge_sort([]) == []

# condition: len(array) <= 1: True
def test_merge_sort_single():
    # len(array) <= 1: True
    assert merge_sort([5]) == [5]

# condition: len(array) <= 1: False
def test_merge_sort_sorted_pair():
    # len(array) <= 1: False
    assert merge_sort([1, 2]) == [1, 2]

# condition: len(array) <= 1: False
def test_merge_sort_unsorted_pair():
    # len(array) <= 1: False
    assert merge_sort([2, 1]) == [1, 2]

# condition: len(array) <= 1: False
def test_merge_sort_multiple():
    # len(array) <= 1: False
    assert merge_sort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]