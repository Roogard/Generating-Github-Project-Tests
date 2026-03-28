import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

def test_quicksort_two_elements_sorted():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

def test_quicksort_two_elements_reverse():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

def test_quicksort_two_elements_equal():
    result = quicksort([5, 5])
    assert result == sorted([5, 5])
    assert len(result) == len([5, 5])

def test_quicksort_already_sorted():
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_reverse_sorted():
    inp = [5, 4, 3, 2, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_all_equal_elements():
    inp = [7, 7, 7, 7, 7]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_with_duplicates():
    inp = [3, 1, 2, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_negative_numbers():
    inp = [-1, -3, -2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_mixed_negative_positive():
    inp = [-5, 0, 5, -1, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_single_negative():
    result = quicksort([-1])
    assert result == [-1]
    assert len(result) == 1

def test_quicksort_min_max_integers():
    inp = [-(2**31), 2**31 - 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_large_list():
    inp = list(range(100, 0, -1))
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_pivot_is_max():
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_pivot_is_min():
    inp = [1, 5, 4, 3, 2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_no_nested_lists_in_result():
    inp = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(inp)
    assert all(not isinstance(x, list) for x in result)

def test_quicksort_preserves_multiset():
    inp = [4, 2, 7, 2, 4, 1]
    result = quicksort(inp)
    assert sorted(result) == sorted(inp)

def test_quicksort_two_element_equal_boundary():
    inp = [0, 0]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_zeros_and_ones():
    inp = [1, 0, 1, 0, 0, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)