from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    assert quicksort([]) == []

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# condition: not arr → False, x < pivot → True (elements less than pivot exist), x > pivot → True (elements greater than pivot exist)
def test_quicksort_sorted_ascending():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# condition: not arr → False, x < pivot → True, x > pivot → True
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → False (no element less than pivot), x > pivot → True
def test_quicksort_all_greater_than_pivot():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → True, x > pivot → False (no element greater than pivot)
def test_quicksort_all_lesser_than_pivot():
    assert quicksort([5, 1, 2, 3, 4]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → False, x > pivot → False (duplicates only, all equal to pivot)
def test_quicksort_all_duplicates():
    assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed with duplicates)
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 2, 3, 4]) == [1, 2, 3, 3, 4]

# condition: not arr → False, x < pivot → True, x > pivot → True (negative numbers)
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed negative and positive)
def test_quicksort_mixed_negative_positive():
    assert quicksort([-1, 3, -2, 0, 2]) == [-2, -1, 0, 2, 3]

# condition: not arr → False, x < pivot → False, x > pivot → False (single duplicate pair)
def test_quicksort_two_equal_elements():
    assert quicksort([7, 7]) == [7, 7]

# condition: not arr → False, x < pivot → True, x > pivot → True (larger list)
def test_quicksort_larger_list():
    assert quicksort([10, 3, 7, 1, 9, 5]) == [1, 3, 5, 7, 9, 10]