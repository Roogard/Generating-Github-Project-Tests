from python_programs.quicksort import quicksort

# covers: block 1 (empty input)
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block 2 (pivot path), block 3 & 4 (recursive calls on empty lists), block 5 (return)
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# covers: recursion on greater sublist (sorted list path)
def test_quicksort_sorted_list():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: recursion on lesser sublist (reverse sorted list path)
def test_quicksort_reverse_list():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: handling of duplicates (elements equal to pivot are dropped)
def test_quicksort_with_duplicates():
    # duplicates 3,2,1 are removed by design of strict < and > in comprehensions
    assert quicksort([3, 1, 2, 3, 2, 1]) == [1, 2, 3]