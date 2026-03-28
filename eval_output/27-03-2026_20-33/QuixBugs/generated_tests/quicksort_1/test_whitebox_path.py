from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# path: empty check → False → arr[1:] empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# path: empty check → False → 1 iter → all elements go to lesser → greater=[]
def test_quicksort_two_descending():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

# path: empty check → False → 1 iter → all elements go to greater → lesser=[]
def test_quicksort_two_ascending():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

# path: empty check → False → multiple iters → elements split into both lesser and greater
def test_quicksort_multiple_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → duplicates of pivot → neither lesser nor greater gets them (duplicates dropped)
def test_quicksort_all_duplicates():
    arr = [5, 5, 5, 5]
    result = quicksort(arr)
    # Note: duplicates of pivot are excluded from both lesser and greater
    assert result == [5]
    assert len(result) == 1

# path: empty check → False → some duplicates of pivot mixed with other values
def test_quicksort_with_some_duplicates():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    # duplicates of pivot (3) are dropped; only unique values survive
    assert result == [1, 2, 3]

# path: empty check → False → already sorted input → all go to greater recursively
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → reverse sorted input → all go to lesser recursively
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → negative numbers mixed with positives
def test_quicksort_negative_numbers():
    arr = [-3, 1, -1, 2, 0]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → single element repeated with unique elements around it
def test_quicksort_two_elements_equal():
    arr = [1, 1]
    result = quicksort(arr)
    # pivot=1, arr[1:] = [1], neither < 1 nor > 1, so result = [1]
    assert result == [1]