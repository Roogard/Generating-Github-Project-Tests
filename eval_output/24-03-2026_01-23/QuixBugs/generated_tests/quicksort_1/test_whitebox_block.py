from python_programs.quicksort import quicksort

# covers: block 1 (empty input branch)
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block 2, block 3, block 4, block 5 (non-empty input, recursion on both lesser and greater)
def test_quicksort_mixed():
    assert quicksort([3, 1, 4, 2]) == [1, 2, 3, 4]

# covers: deeper recursion paths (all greater elements, then all lesser elements)
def test_quicksort_sorted_and_reverse():
    assert quicksort([1, 2, 3, 4]) == [1, 2, 3, 4]
    assert quicksort([4, 3, 2, 1]) == [1, 2, 3, 4]