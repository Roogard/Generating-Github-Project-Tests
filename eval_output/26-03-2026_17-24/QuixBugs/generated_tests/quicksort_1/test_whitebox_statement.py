from python_programs.quicksort import quicksort

# covers: empty list check (True branch), return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: empty list check (False branch), pivot assignment,
# lesser/greater recursive calls, return lesser + [pivot] + greater
def test_quicksort_single_element():
    assert quicksort([1]) == [1]

# covers: all statements with multiple elements requiring actual partitioning
def test_quicksort_multiple_elements():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: all statements with duplicates (duplicates are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 3, 1, 2]) == [1, 2, 3, 3]

# covers: all statements with already sorted input
def test_quicksort_sorted_input():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: all statements with reverse sorted input
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: all statements ensuring greater branch is populated
def test_quicksort_lesser_and_greater_populated():
    assert quicksort([2, 1, 3]) == [1, 2, 3]