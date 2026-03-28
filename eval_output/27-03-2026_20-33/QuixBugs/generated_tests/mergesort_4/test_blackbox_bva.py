import pytest
from python_programs.mergesort import mergesort

def test_empty_array():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

def test_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

def test_two_elements_sorted():
    inp = [1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_two_elements_reverse_sorted():
    inp = [2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_three_elements():
    inp = [3, 1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_already_sorted():
    inp = [1, 2, 3, 4, 5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_reverse_sorted():
    inp = [5, 4, 3, 2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_all_equal_elements():
    inp = [7, 7, 7, 7]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_duplicate_elements():
    inp = [3, 1, 2, 3, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_negative_numbers():
    inp = [-3, -1, -4, -1, -5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mixed_negative_and_positive():
    inp = [-2, 3, -1, 0, 4, -5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_large_array():
    import random
    random.seed(0)
    inp = random.sample(range(10000), 1000)
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_large_array_boundary_size_two_power():
    inp = list(range(16, 0, -1))
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_odd_length_array():
    inp = [5, 3, 8, 1, 9]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_even_length_array():
    inp = [5, 3, 8, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_min_max_integers():
    inp = [2**31 - 1, -(2**31), 0, 2**31 - 2, -(2**31) + 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_preserves_all_elements_no_drops():
    inp = [4, 2, 2, 8, 5, 5, 1]
    result = mergesort(inp)
    assert sorted(result) == sorted(inp)
    assert len(result) == len(inp)

def test_result_is_non_nested():
    inp = [3, 1, 2]
    result = mergesort(inp)
    assert all(not isinstance(x, list) for x in result)

def test_two_elements_equal():
    inp = [5, 5]
    result = mergesort(inp)
    assert result == [5, 5]
    assert len(result) == 2

def test_single_negative_element():
    result = mergesort([-1])
    assert result == [-1]
    assert len(result) == 1

def test_single_zero():
    result = mergesort([0])
    assert result == [0]
    assert len(result) == 1