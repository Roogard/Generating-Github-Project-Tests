from algorithms.sorting.merge_sort import merge_sort

# covers: block 1 (len(array) <= 1) and block 2 (return array)
def test_merge_sort_empty():
    assert merge_sort([]) == []

# covers: block 1 (len(array) <= 1) and block 2 (return array)
def test_merge_sort_single():
    assert merge_sort([5]) == [5]

# covers: block 3 (len(array) > 1), recursive calls, and merge
def test_merge_sort_sorted():
    assert merge_sort([1, 2, 3]) == [1, 2, 3]

# covers: block 3 (len(array) > 1), recursive calls, and merge
def test_merge_sort_reverse():
    assert merge_sort([3, 2, 1]) == [1, 2, 3]

# covers: block 3 (len(array) > 1), recursive calls, and merge
def test_merge_sort_duplicates():
    assert merge_sort([5, 2, 8, 2, 5]) == [2, 2, 5, 5, 8]

# covers: block 3 (len(array) > 1), recursive calls, and merge
def test_merge_sort_large():
    assert merge_sort([9, -3, 0, 7, 12, -5]) == [-5, -3, 0, 7, 9, 12]