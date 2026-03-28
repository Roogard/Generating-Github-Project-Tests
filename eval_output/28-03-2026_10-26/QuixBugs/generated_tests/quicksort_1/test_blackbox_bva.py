import pytest
from python_programs.quicksort import quicksort

def test_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

def test_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

def test_two_elements_sorted():
    arr = [1, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_two_elements_reverse_sorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_two_equal_elements():
    arr = [5, 5]
    result = quicksort(arr)
    # A correct sort must preserve all elements including duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_all_equal_elements():
    arr = [7, 7, 7, 7]
    result = quicksort(arr)
    # A correct sort must preserve all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_duplicates_with_pivot():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    # A correct sort preserves all elements including duplicates of the pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_negative_numbers():
    arr = [-1, -3, -2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_mixed_negative_and_positive():
    arr = [-5, 0, 3, -2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_large_list_boundary():
    arr = list(range(100, 0, -1))
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_pivot_is_max_element():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_pivot_is_min_element():
    arr = [1, 5, 4, 3, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_all_elements_same_as_pivot():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # A correct sort must return all elements, including all copies of the pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_single_duplicate_pair():
    arr = [2, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_no_nested_lists_in_result():
    arr = [4, 2, 7, 1, 9]
    result = quicksort(arr)
    assert all(not isinstance(x, list) for x in result)
    assert result == sorted(arr)