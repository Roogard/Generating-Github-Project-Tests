from python_programs.quicksort import quicksort

# not arr: True
def test_quicksort_empty():
    assert quicksort([]) == []

# not arr: False, x<pivot: True (2), x<pivot: False (4), x>pivot: True (4), x>pivot: False (2)
def test_quicksort_mixed():
    arr = [3, 4, 2]
    assert quicksort(arr) == [2, 3, 4]

# not arr: False, covers simple single-element recursion
def test_quicksort_single_element():
    assert quicksort([5]) == [5]