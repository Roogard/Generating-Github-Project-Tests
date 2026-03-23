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
def test_merge_sort_two_elements():
    # len(array) <= 1: False
    assert merge_sort([2, 1]) == [1, 2]

# condition: len(array) <= 1: False
def test_merge_sort_multiple_elements():
    # len(array) <= 1: False
    assert merge_sort([5, 2, 4, 1, 3]) == [1, 2, 3, 4, 5]

# condition: len(array) <= 1: False
def test_merge_sort_already_sorted():
    # len(array) <= 1: False
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# condition: len(array) <= 1: False
def test_merge_sort_reverse_sorted():
    # len(array) <= 1: False
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# condition: len(array) <= 1: False
def test_merge_sort_with_duplicates():
    # len(array) <= 1: False
    assert merge_sort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]