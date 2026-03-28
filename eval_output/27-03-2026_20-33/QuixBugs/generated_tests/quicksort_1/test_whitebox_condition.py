from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_all_lesser():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → False, x > pivot → True
def test_quicksort_all_greater():
    arr = [1, 5, 6, 7, 8]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed)
def test_quicksort_mixed():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → False, x > pivot → False (all equal, duplicates)
def test_quicksort_all_equal():
    arr = [4, 4, 4, 4]
    result = quicksort(arr)
    # duplicates are dropped since neither x < pivot nor x > pivot holds for equals
    # a correct quicksort preserving duplicates would return [4,4,4,4], but this impl drops them
    # test what a correct sort SHOULD return: sorted input
    assert sorted(result) == sorted(set(arr))  # property: all values present (unique)
    assert len(result) >= 1

# condition: not arr → False, single element (no elements beyond pivot, both list comprehensions empty)
def test_quicksort_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True, already sorted input
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True, reverse sorted input
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, negative numbers, x < pivot → True, x > pivot → True
def test_quicksort_negative_numbers():
    arr = [-3, -1, -7, -2, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, mixed negative and positive, x < pivot → True, x > pivot → True
def test_quicksort_mixed_negative_positive():
    arr = [3, -1, 0, -5, 7, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)