from correct_python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([5]) == [5]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_three_elements():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 2, 1, 3]) == [1, 1, 2, 3, 3]

def test_quicksort_all_equal():
    assert quicksort([7, 7, 7]) == [7, 7, 7]

def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]

def test_quicksort_mixed_numbers():
    assert quicksort([0, -5, 10, 3]) == [-5, 0, 3, 10]

def test_quicksort_large_list():
    arr = list(range(100, 0, -1))
    assert quicksort(arr) == list(range(1, 101))