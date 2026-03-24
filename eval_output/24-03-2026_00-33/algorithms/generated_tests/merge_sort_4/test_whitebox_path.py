import pytest
from algorithms.sorting.merge_sort import merge_sort

# path: base case True (len <= 1) → return
def test_merge_sort_empty():
    assert merge_sort([]) == []

# path: base case True (len <= 1) → return
def test_merge_sort_single():
    assert merge_sort([42]) == [42]

# path: base case False → recursive left → base case True (single) → recursive right → base case True (single) → _merge → return
def test_merge_sort_two_sorted():
    assert merge_sort([1, 2]) == [1, 2]

# path: base case False → recursive left → base case True (single) → recursive right → base case True (single) → _merge → return
def test_merge_sort_two_reverse():
    assert merge_sort([2, 1]) == [1, 2]

# path: base case False → recursive left → recursive left → ... (multiple splits) → multiple merges → return
def test_merge_sort_odd_length():
    assert merge_sort([3, 1, 2]) == [1, 2, 3]

# path: base case False → recursive left → recursive left → ... (multiple splits) → multiple merges → return
def test_merge_sort_even_length():
    assert merge_sort([5, 3, 8, 1]) == [1, 3, 5, 8]

# path: base case False → recursive left → recursive left → ... (multiple splits) → multiple merges → return
def test_merge_sort_already_sorted():
    assert merge_sort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: base case False → recursive left → recursive left → ... (multiple splits) → multiple merges → return
def test_merge_sort_reverse_sorted():
    assert merge_sort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: base case False → recursive left → recursive left → ... (multiple splits) → multiple merges → return
def test_merge_sort_duplicates():
    assert merge_sort([4, 2, 4, 1, 2]) == [1, 2, 2, 4, 4]