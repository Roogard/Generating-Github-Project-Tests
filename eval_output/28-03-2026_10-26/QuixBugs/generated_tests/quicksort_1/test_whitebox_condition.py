from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_elements_less_than_pivot():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False (non-empty list), x < pivot → False, x > pivot → True
def test_quicksort_elements_greater_than_pivot():
    arr = [1, 3, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (mixed)
def test_quicksort_mixed_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    # A correct quicksort should return all elements in sorted order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → False, x > pivot → False (duplicates of pivot)
def test_quicksort_duplicates():
    arr = [5, 5, 5]
    result = quicksort(arr)
    # A correct quicksort must preserve all duplicate elements
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (already sorted)
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (reverse sorted)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False with single element (no recursive sub-conditions triggered)
def test_quicksort_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (negative numbers)
def test_quicksort_negative_numbers():
    arr = [-3, -1, -4, -1, -5, -9, -2, -6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (mixed negatives and positives)
def test_quicksort_mixed_negative_positive():
    arr = [3, -1, 4, -1, 5, -9, 2, -6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot: True and False, x > pivot: True and False (with duplicates mixed)
def test_quicksort_duplicates_mixed():
    arr = [4, 2, 4, 1, 4, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all elements including duplicates of pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)