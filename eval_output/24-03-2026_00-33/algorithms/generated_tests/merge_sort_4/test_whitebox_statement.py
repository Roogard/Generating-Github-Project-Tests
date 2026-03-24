from algorithms.sorting.merge_sort import merge_sort

# covers: if len(array) <= 1: return array (True)
def test_merge_sort_empty():
    assert merge_sort([]) == []

# covers: if len(array) <= 1: return array (True)
def test_merge_sort_single():
    assert merge_sort([5]) == [5]

# covers: if len(array) <= 1: (False), mid = len(array) // 2, left = merge_sort(array[:mid]), right = merge_sort(array[mid:]), _merge(left, right, array), return array
def test_merge_sort_multiple():
    assert merge_sort([3, 1, 2]) == [1, 2, 3]