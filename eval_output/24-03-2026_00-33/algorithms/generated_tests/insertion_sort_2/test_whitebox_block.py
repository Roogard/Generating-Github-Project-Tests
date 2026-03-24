from algorithms.sorting.insertion_sort import insertion_sort

# covers: block 1 (function entry, for loop entry, i=0), block 2 (while condition false), block 3 (return)
def test_empty_array():
    assert insertion_sort([]) == []

# covers: block 1 (function entry, for loop entry, i=0), block 2 (while condition false), block 3 (return)
def test_single_element():
    assert insertion_sort([5]) == [5]

# covers: block 1 (for loop entry, i=0, i=1, i=2), block 2 (while condition false for all i), block 3 (return)
def test_already_sorted():
    assert insertion_sort([1, 2, 3]) == [1, 2, 3]

# covers: block 1 (for loop entry, i=0, i=1, i=2), block 2 (while condition true for i=1 and i=2), block 4 (while body), block 3 (return)
def test_reverse_sorted():
    assert insertion_sort([3, 2, 1]) == [1, 2, 3]

# covers: block 1 (for loop entry, multiple iterations), block 2 (while condition true for some i), block 4 (while body), block 3 (return)
def test_unsorted_with_duplicates():
    assert insertion_sort([4, 2, 5, 2, 1]) == [1, 2, 2, 4, 5]