from python_programs.mergesort import mergesort

def test_mergesort_empty_list():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([42]) == [42]

def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

def test_mergesort_two_elements_unsorted():
    assert mergesort([2, 1]) == [1, 2]

def test_mergesort_two_elements_equal():
    assert mergesort([5, 5]) == [5, 5]

def test_mergesort_three_elements_sorted():
    assert mergesort([1, 2, 3]) == [1, 2, 3]

def test_mergesort_three_elements_reverse_sorted():
    assert mergesort([3, 2, 1]) == [1, 2, 3]

def test_mergesort_three_elements_mixed():
    assert mergesort([2, 3, 1]) == [1, 2, 3]

def test_mergesort_all_equal_elements():
    assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]

def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_mergesort_large_list():
    arr = list(range(1000, 0, -1))
    assert mergesort(arr) == list(range(1, 1001))

def test_mergesort_large_list_already_sorted():
    arr = list(range(1, 1001))
    assert mergesort(arr) == list(range(1, 1001))

def test_mergesort_with_negative_numbers():
    assert mergesort([-3, -1, -2]) == [-3, -2, -1]

def test_mergesort_with_mixed_negative_and_positive():
    assert mergesort([-1, 3, -2, 0]) == [-2, -1, 0, 3]

def test_mergesort_with_zero():
    assert mergesort([0]) == [0]

def test_mergesort_min_and_max_integers():
    import sys
    arr = [sys.maxsize, -sys.maxsize - 1, 0]
    assert mergesort(arr) == [-sys.maxsize - 1, 0, sys.maxsize]

def test_mergesort_duplicate_boundary_values():
    assert mergesort([1, 1, 2, 2]) == [1, 1, 2, 2]

def test_mergesort_left_half_larger_than_right():
    assert mergesort([4, 5, 1, 2]) == [1, 2, 4, 5]

def test_mergesort_odd_length_list():
    assert mergesort([3, 1, 4, 1, 5]) == [1, 1, 3, 4, 5]

def test_mergesort_even_length_list():
    assert mergesort([4, 2, 3, 1]) == [1, 2, 3, 4]

def test_mergesort_two_element_equal_boundary():
    assert mergesort([3, 3]) == [3, 3]