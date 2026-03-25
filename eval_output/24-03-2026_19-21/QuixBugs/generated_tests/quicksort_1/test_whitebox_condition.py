from python_programs.quicksort import quicksort

# not arr: True
def test_quicksort_empty():
    assert quicksort([]) == []

# not arr: False
def test_quicksort_single_element():
    assert quicksort([5]) == [5]

# not arr: False
def test_quicksort_sorted_list():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# not arr: False
def test_quicksort_reverse_list():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# not arr: False
def test_quicksort_mixed_list():
    assert quicksort([3, 1, 4, 2, 5]) == [1, 2, 3, 4, 5]