import pytest
from algorithms.sorting.merge_sort import merge_sort

# path: base case True (len <= 1) -> return array (empty list)
def test_merge_sort_empty():
    assert merge_sort([]) == []

# path: base case True (len <= 1) -> return array (single element)
def test_merge_sort_single():
    assert merge_sort([42]) == [42]

# path: base case False -> recursive calls -> _merge -> return array
# This path covers the minimal recursive case: len(array) == 2
def test_merge_sort_two_elements():
    assert merge_sort([2, 1]) == [1, 2]

# path: base case False -> recursive calls -> _merge -> return array
# This path covers a case where left and right subarrays each have multiple elements
def test_merge_sort_multiple_elements():
    assert merge_sort([5, 3, 8, 6, 2, 7, 1, 4]) == [1, 2, 3, 4, 5, 6, 7, 8]

# path: base case False -> recursive calls -> _merge -> return array
# This path covers already sorted input
def test_merge_sort_already_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: base case False -> recursive calls -> _merge -> return array
# This path covers reverse sorted input
def test_merge_sort_reverse_sorted():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: base case False -> recursive calls -> _merge -> return array
# This path covers array with duplicate elements
def test_merge_sort_with_duplicates():
    assert merge_sort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]