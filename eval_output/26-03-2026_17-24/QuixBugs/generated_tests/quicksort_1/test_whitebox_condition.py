from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    assert quicksort([]) == []

# condition: not arr → False (non-empty list); x < pivot → True for some elements
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# condition: not arr → False; x < pivot → True, x > pivot → True (elements on both sides)
def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

# condition: not arr → False; x < pivot → False (all greater), x > pivot → True
def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

# condition: not arr → False; x < pivot → True, x > pivot → True
def test_quicksort_multiple_elements():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# condition: not arr → False; x < pivot → False for all (already sorted ascending)
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# condition: not arr → False; x > pivot → False for all (reverse sorted, all lesser)
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# condition: not arr → False; x < pivot → False, x > pivot → False (all duplicates)
def test_quicksort_all_duplicates():
    assert quicksort([7, 7, 7, 7]) == [7, 7, 7, 7]

# condition: not arr → False; x < pivot → True, x > pivot → True (negative numbers)
def test_quicksort_with_negatives():
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

# condition: not arr → False; x < pivot → True, x > pivot → True (mixed negative and positive)
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, 5, -2]) == [-2, -1, 0, 3, 5]

# condition: not arr → False; x < pivot → True only (pivot is maximum)
def test_quicksort_pivot_is_max():
    assert quicksort([9, 1, 2, 3]) == [1, 2, 3, 9]

# condition: not arr → False; x > pivot → True only (pivot is minimum)
def test_quicksort_pivot_is_min():
    assert quicksort([1, 9, 8, 7]) == [1, 7, 8, 9]