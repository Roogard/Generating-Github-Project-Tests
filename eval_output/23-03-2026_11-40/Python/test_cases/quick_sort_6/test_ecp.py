import pytest
from sorts.quick_sort import quick_sort

# Valid equivalence class: empty list
def test_quick_sort_empty():
    assert quick_sort([]) == []

# Valid equivalence class: single element list
def test_quick_sort_single():
    assert quick_sort([5]) == [5]

# Valid equivalence class: list with multiple unique elements
def test_quick_sort_multiple_unique():
    assert quick_sort([3, 1, 2]) == [1, 2, 3]

# Valid equivalence class: list with duplicate elements
def test_quick_sort_with_duplicates():
    assert quick_sort([2, 1, 2, 3, 1]) == [1, 1, 2, 2, 3]

# Valid equivalence class: list already sorted
def test_quick_sort_already_sorted():
    assert quick_sort([1, 2, 3, 4]) == [1, 2, 3, 4]

# Valid equivalence class: list sorted in descending order
def test_quick_sort_reverse_sorted():
    assert quick_sort([4, 3, 2, 1]) == [1, 2, 3, 4]

# Valid equivalence class: list with negative numbers
def test_quick_sort_negative():
    assert quick_sort([-5, 0, -1, 3]) == [-5, -1, 0, 3]

# Valid equivalence class: list with all identical elements
def test_quick_sort_all_same():
    assert quick_sort([7, 7, 7]) == [7, 7, 7]

# Valid equivalence class: large list (stress test)
def test_quick_sort_large():
    collection = list(range(100, 0, -1))
    expected = list(range(1, 101))
    assert quick_sort(collection) == expected