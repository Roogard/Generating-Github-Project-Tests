from python_programs.quicksort import quicksort

# covers: block 1 (empty array, returns [])
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: block 2 (non-empty array, pivot selected, lesser/greater recursion, return)
# single element: lesser and greater are both empty
def test_quicksort_single():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: block 2 with non-trivial lesser and greater partitions
def test_quicksort_multiple_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with already sorted input (greater always empty in recursion)
def test_quicksort_sorted_input():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with reverse sorted input (lesser always empty in recursion)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with duplicate elements (elements equal to pivot are dropped from both partitions)
# a correct quicksort must preserve all elements including duplicates
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # a correct quicksort should preserve all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with negative numbers
def test_quicksort_negative_numbers():
    arr = [-5, -1, -3, 0, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 ensuring all values are present in output (multiset preserved)
def test_quicksort_preserves_elements():
    arr = [10, 7, 8, 9, 1, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert sorted(result) == sorted(arr)