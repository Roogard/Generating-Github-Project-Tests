from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([42]) == [42]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_all_duplicates():
    assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]

def test_quicksort_two_duplicates():
    assert quicksort([2, 2]) == [2, 2]

def test_quicksort_duplicates_with_other_elements():
    assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]

def test_quicksort_negative_numbers():
    assert quicksort([-1, -3, -2]) == [-3, -2, -1]

def test_quicksort_single_negative():
    assert quicksort([-1]) == [-1]

def test_quicksort_mixed_negative_and_positive():
    assert quicksort([-1, 0, 1]) == [-1, 0, 1]

def test_quicksort_mixed_negative_and_positive_unsorted():
    assert quicksort([1, -1, 0]) == [-1, 0, 1]

def test_quicksort_with_zero():
    assert quicksort([0]) == [0]

def test_quicksort_zeros_and_positives():
    assert quicksort([0, 1, 0]) == [0, 0, 1]

def test_quicksort_large_list_boundary():
    arr = list(range(999, -1, -1))
    assert quicksort(arr) == list(range(0, 1000))

def test_quicksort_large_list_already_sorted():
    arr = list(range(0, 1000))
    assert quicksort(arr) == list(range(0, 1000))

def test_quicksort_large_single_value_repeated():
    arr = [7] * 100
    assert quicksort(arr) == [7] * 100

def test_quicksort_pivot_is_max():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_pivot_is_min():
    assert quicksort([1, 5, 4, 3, 2]) == [1, 2, 3, 4, 5]

def test_quicksort_two_elements_equal():
    assert quicksort([5, 5]) == [5, 5]

def test_quicksort_large_and_small_boundary_values():
    assert quicksort([10**9, -10**9, 0]) == [-10**9, 0, 10**9]

def test_quicksort_single_large_value():
    assert quicksort([10**9]) == [10**9]

def test_quicksort_single_small_value():
    assert quicksort([-10**9]) == [-10**9]