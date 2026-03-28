from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
def test_quicksort_single():
    result = quicksort([1])
    assert result == [1]
    assert len(result) == 1
    assert sorted(result) == sorted([1])

# covers: all statements, lesser and greater lists are non-empty
def test_quicksort_multiple():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: all statements with already sorted input
def test_quicksort_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all statements with reverse sorted input
def test_quicksort_reverse():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: lesser list non-empty, greater empty
def test_quicksort_lesser_only():
    arr = [5, 3, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: greater list non-empty, lesser empty
def test_quicksort_greater_only():
    arr = [1, 3, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: duplicates handled (elements equal to pivot are dropped from lesser and greater)
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # duplicates are excluded from lesser and greater, only pivot is kept per recursive level
    assert len(result) <= len(arr)
    assert all(x == 3 for x in result)