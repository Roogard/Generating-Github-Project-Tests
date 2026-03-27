from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
def test_quicksort_single():
    assert quicksort([1]) == [1]

# covers: all statements with multiple elements requiring recursive lesser and greater branches
def test_quicksort_multiple():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: all statements with duplicates (duplicate elements are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]

# covers: all statements with already sorted input
def test_quicksort_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: all statements with reverse sorted input (exercises greater branch heavily)
def test_quicksort_reverse():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: all statements with negative numbers
def test_quicksort_negatives():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]