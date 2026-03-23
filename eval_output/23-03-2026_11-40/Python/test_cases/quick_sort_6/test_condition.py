from sorts.quick_sort import quick_sort
import pytest
from unittest.mock import patch

# condition: len(collection) < 2: True (empty list)
def test_quick_sort_empty():
    # len(collection) < 2: True
    assert quick_sort([]) == []

# condition: len(collection) < 2: True (single element)
def test_quick_sort_single():
    # len(collection) < 2: True
    assert quick_sort([5]) == [5]

# condition: len(collection) < 2: False (multiple elements)
def test_quick_sort_multiple():
    # len(collection) < 2: False
    # sub‑conditions in list comprehensions:
    #   item <= pivot: True (for some items)
    #   item > pivot: True (for some items)
    #   item <= pivot: False (for some items)
    #   item > pivot: False (for some items)
    # These are covered by having both lesser and greater partitions.
    result = quick_sort([3, 1, 4, 1, 5])
    assert result == [1, 1, 3, 4, 5]

# condition: len(collection) < 2: False, and ensure item <= pivot: True for all items (pivot is max)
def test_quick_sort_all_lesser_or_equal():
    # len(collection) < 2: False
    # item <= pivot: True for all items (since pivot is max)
    # item > pivot: False for all items
    # This makes the 'greater' list empty.
    # We'll mock randrange to return index of the max element.
    with patch('sorts.quick_sort.randrange', return_value=2):
        # collection = [1, 2, 5, 3, 4], pivot=5 (index 2)
        # lesser = [1, 2, 3, 4] (all <=5), greater = []
        result = quick_sort([1, 2, 5, 3, 4])
        assert result == [1, 2, 3, 4, 5]

# condition: len(collection) < 2: False, and ensure item > pivot: True for all items (pivot is min)
def test_quick_sort_all_greater():
    # len(collection) < 2: False
    # item <= pivot: False for all items (except pivot itself, but pivot is popped)
    # item > pivot: True for all items
    # This makes the 'lesser' list empty.
    with patch('sorts.quick_sort.randrange', return_value=0):
        # collection = [1, 2, 5, 3, 4], pivot=1 (index 0)
        # lesser = [], greater = [2, 5, 3, 4]
        result = quick_sort([1, 2, 5, 3, 4])
        assert result == [1, 2, 3, 4, 5]

# condition: len(collection) < 2: False, and ensure both partitions are non‑empty (mixed case)
def test_quick_sort_mixed_partitions():
    # len(collection) < 2: False
    # item <= pivot: True for some, False for others
    # item > pivot: True for some, False for others
    with patch('sorts.quick_sort.randrange', return_value=1):
        # collection = [3, 2, 5, 1, 4], pivot=2 (index 1)
        # lesser = [1] (item <= pivot: True for 1, False for others)
        # greater = [3, 5, 4] (item > pivot: True for 3,5,4, False for 1)
        result = quick_sort([3, 2, 5, 1, 4])
        assert result == [1, 2, 3, 4, 5]

# Additional test for duplicate elements to cover item <= pivot and item > pivot with equal values
def test_quick_sort_duplicates():
    # len(collection) < 2: False
    # item <= pivot: True for duplicates equal to pivot
    # item > pivot: False for those duplicates
    with patch('sorts.quick_sort.randrange', return_value=2):
        # collection = [3, 1, 2, 2, 4], pivot=2 (index 2)
        # lesser = [1, 2] (item <= pivot: True for 1 and the duplicate 2)
        # greater = [3, 4] (item > pivot: True for 3 and 4)
        result = quick_sort([3, 1, 2, 2, 4])
        assert result == [1, 2, 2, 3, 4]