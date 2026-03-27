from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: empty check → False → arr[1:] empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# path: empty check → False → 1 element in arr[1:] → lesser has element, greater empty
def test_quicksort_two_elements_ascending():
    assert quicksort([2, 1]) == [1, 2]

# path: empty check → False → 1 element in arr[1:] → lesser empty, greater has element
def test_quicksort_two_elements_descending():
    assert quicksort([1, 2]) == [1, 2]

# path: empty check → False → multiple elements → elements go to both lesser and greater
def test_quicksort_multiple_elements_mixed():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# path: empty check → False → all elements less than pivot (all go to lesser)
def test_quicksort_all_lesser():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: empty check → False → all elements greater than pivot (all go to greater)
def test_quicksort_all_greater():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: empty check → False → duplicates of pivot (neither lesser nor greater, duplicates dropped)
def test_quicksort_all_duplicates():
    # duplicates equal to pivot are excluded from both lesser and greater
    assert quicksort([3, 3, 3]) == [3]

# path: empty check → False → mixed with duplicates of pivot
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 3, 2, 3]) == [1, 2, 3]

# path: empty check → False → negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

# path: empty check → False → single element list of zero
def test_quicksort_single_zero():
    assert quicksort([0]) == [0]

# path: empty check → False → mixed positive and negative
def test_quicksort_mixed_positive_negative():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]