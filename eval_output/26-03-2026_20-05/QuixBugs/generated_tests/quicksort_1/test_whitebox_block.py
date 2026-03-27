from python_programs.quicksort import quicksort

# covers: block 1 (empty array base case) -> return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block 2 (non-empty array), single element (lesser and greater are both empty)
def test_quicksort_single_element():
    assert quicksort([1]) == [1]

# covers: block 2, recursive calls with lesser and greater populated
def test_quicksort_sorted_order():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: block 2, already sorted input (greater populated, lesser empty recursively)
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: block 2, reverse sorted input (lesser populated, greater empty recursively)
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 2, duplicates (elements equal to pivot are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# covers: block 2, mixed duplicates
def test_quicksort_mixed_duplicates():
    assert quicksort([2, 1, 2, 3, 2]) == [1, 2, 2, 2, 3]

# covers: block 2, negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# covers: block 2, mixed negative and positive
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, 2, -5]) == [-5, -1, 0, 2, 3]

# covers: block 2, larger list to ensure full recursive coverage
def test_quicksort_larger_list():
    input_arr = [10, 3, 7, 1, 8, 4, 6, 2, 9, 5]
    assert quicksort(input_arr) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]