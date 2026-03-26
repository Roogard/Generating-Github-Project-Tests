from python_programs.quicksort import quicksort

# arr empty: arr is False, not arr is True
def test_quicksort_empty():
    assert quicksort([]) == []

# arr non-empty: arr is True, not arr is False
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# arr non-empty: arr is True, not arr is False
def test_quicksort_multiple_elements():
    data = [3, 1, 4, 1, 5, 9, 2, 6, 5]
    assert quicksort(data) == sorted(data)