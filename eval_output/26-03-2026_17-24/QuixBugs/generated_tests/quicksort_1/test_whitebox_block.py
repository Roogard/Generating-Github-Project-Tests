from python_programs.quicksort import quicksort

# covers: block 1 (empty array -> return [])
def test_empty_array():
    assert quicksort([]) == []

# covers: block 2 (single element, lesser and greater are both empty)
def test_single_element():
    assert quicksort([1]) == [1]

# covers: block 2, recursive lesser and greater paths
def test_sorted_array():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: block 2, recursive lesser and greater paths with unsorted input
def test_unsorted_array():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# covers: block 2 with reverse sorted input (exercises greater path heavily)
def test_reverse_sorted_array():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 2, duplicates (elements equal to pivot are excluded from lesser and greater)
def test_all_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# covers: block 2 with negative numbers
def test_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# covers: block 2 with mixed negative and positive
def test_mixed_positive_negative():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]

# covers: block 2 with two elements (lesser empty, greater non-empty)
def test_two_elements_ascending():
    assert quicksort([1, 2]) == [1, 2]

# covers: block 2 with two elements (lesser non-empty, greater empty)
def test_two_elements_descending():
    assert quicksort([2, 1]) == [1, 2]