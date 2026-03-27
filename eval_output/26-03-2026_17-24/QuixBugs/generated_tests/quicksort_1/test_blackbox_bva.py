import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([1]) == [1]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_two_elements_equal():
    assert quicksort([1, 1]) == [1]

def test_quicksort_all_equal_elements():
    assert quicksort([5, 5, 5, 5, 5]) == [5]

def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_single_negative():
    assert quicksort([-1]) == [-1]

def test_quicksort_negative_and_positive():
    assert quicksort([-1, 0, 1]) == [-1, 0, 1]

def test_quicksort_all_negative():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]

def test_quicksort_with_zero():
    assert quicksort([0]) == [0]

def test_quicksort_large_first_element():
    assert quicksort([100, 1, 2, 3]) == [1, 2, 3, 100]

def test_quicksort_small_first_element():
    assert quicksort([1, 100, 50, 75]) == [1, 50, 75, 100]

def test_quicksort_duplicates_with_other_values():
    assert quicksort([3, 1, 2, 3, 1]) == [1, 2, 3]

def test_quicksort_large_list():
    input_list = list(range(100, 0, -1))
    expected = list(range(1, 101))
    assert quicksort(input_list) == expected

def test_quicksort_large_list_already_sorted():
    input_list = list(range(1, 101))
    expected = list(range(1, 101))
    assert quicksort(input_list) == expected

def test_quicksort_min_integer_value():
    assert quicksort([-(2**31)]) == [-(2**31)]

def test_quicksort_max_integer_value():
    assert quicksort([2**31 - 1]) == [2**31 - 1]

def test_quicksort_min_and_max_integer():
    assert quicksort([2**31 - 1, -(2**31)]) == [-(2**31), 2**31 - 1]

def test_quicksort_pivot_is_last():
    assert quicksort([2, 3, 4, 1]) == [1, 2, 3, 4]

def test_quicksort_pivot_is_middle():
    assert quicksort([3, 1, 5, 2, 4]) == [1, 2, 3, 4, 5]

def test_quicksort_two_element_equal_list():
    assert quicksort([7, 7]) == [7]

def test_quicksort_float_values():
    assert quicksort([3.5, 1.1, 2.2]) == [1.1, 2.2, 3.5]

def test_quicksort_mixed_negative_zero_positive():
    assert quicksort([0, -1, 1, -2, 2]) == [-2, -1, 0, 1, 2]