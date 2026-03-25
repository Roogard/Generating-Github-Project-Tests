from python_programs.quicksort import quicksort

def test_quicksort_empty_array():
    assert quicksort([]) == []

def test_quicksort_single_element_array():
    assert quicksort([42]) == [42]

def test_quicksort_two_element_sorted_array():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_element_reversed_array():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_array_with_duplicates():
    # Duplicates are only retained once due to pivot logic
    assert quicksort([3, 1, 2, 1, 3]) == [1, 2, 3]

def test_quicksort_multiple_elements_mixed_signs():
    assert quicksort([0, -1, 5, -3, 2]) == [-3, -1, 0, 2, 5]