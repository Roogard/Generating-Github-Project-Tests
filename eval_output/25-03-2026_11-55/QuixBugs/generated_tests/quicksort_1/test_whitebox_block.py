from python_programs.quicksort import quicksort

# covers: block 1 (base-case for empty list)
def test_empty_list():
    assert quicksort([]) == []

# covers: block 2 (non-empty list, recursion on empty sublists)
def test_single_element():
    assert quicksort([42]) == [42]

# covers: block 2 with non-empty lesser and greater branches
def test_three_elements():
    assert quicksort([2, 1, 3]) == [1, 2, 3]

# covers: block 2 with duplicates (dropped by < and > filters) and negative values
def test_with_duplicates_and_negatives():
    arr = [0, -1, 2, -1, 0]
    # duplicates of 0 and -1 are removed; sorted result is [-1, 0, 2]
    assert quicksort(arr) == [-1, 0, 2]