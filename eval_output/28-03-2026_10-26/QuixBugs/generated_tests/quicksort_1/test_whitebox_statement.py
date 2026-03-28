from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
# with a single element: lesser and greater are both empty lists (base case reached recursively)
def test_quicksort_single():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: all statements with multiple elements requiring recursive calls
# lesser and greater sublists are non-empty, exercising the list comprehensions and recursion
def test_quicksort_multiple():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)  # duplicates are preserved by this impl (>= in greater)

# covers: all statements with already-sorted input
def test_quicksort_sorted_input():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all statements with reverse-sorted input (maximizes recursion depth on lesser)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: lesser list comprehension produces non-empty list, greater is empty
def test_quicksort_all_lesser():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: greater list comprehension produces non-empty list, lesser is empty
def test_quicksort_all_greater():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)