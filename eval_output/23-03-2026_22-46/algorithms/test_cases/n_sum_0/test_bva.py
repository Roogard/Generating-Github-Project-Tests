from algorithms.array.n_sum import _two_sum
from collections.abc import Callable
from typing import Any

def sum_closure(a: Any, b: Any) -> Any:
    return a + b

def compare_closure(a: Any, b: Any) -> int:
    if a < b:
        return -1
    elif a > b:
        return 1
    else:
        return 0

def same_closure(a: Any, b: Any) -> bool:
    return a == b

def test_two_sum_empty_list():
    assert _two_sum([], 0) == []

def test_two_sum_single_element():
    assert _two_sum([1], 2) == []

def test_two_sum_two_elements_matching():
    assert _two_sum([1, 1], 2) == [[1, 1]]

def test_two_sum_two_elements_not_matching():
    assert _two_sum([1, 2], 4) == []

def test_two_sum_minimum_length_with_duplicates():
    assert _two_sum([0, 0], 0) == [[0, 0]]

def test_two_sum_large_list_all_same():
    assert _two_sum([5] * 100, 10) == [[5, 5]]

def test_two_sum_target_at_lower_bound_of_values():
    assert _two_sum([-10, -5, 0, 5, 10], -15) == [[-10, -5]]

def test_two_sum_target_at_upper_bound_of_values():
    assert _two_sum([-10, -5, 0, 5, 10], 15) == [[5, 10]]

def test_two_sum_target_below_all_sums():
    assert _two_sum([1, 2, 3], -10) == []

def test_two_sum_target_above_all_sums():
    assert _two_sum([1, 2, 3], 100) == []

def test_two_sum_with_negative_and_positive():
    assert _two_sum([-3, -2, -1, 0, 1, 2, 3], 0) == [[-3, 3], [-2, 2], [-1, 1], [0, 0]]

def test_two_sum_duplicates_skipped():
    assert _two_sum([1, 1, 1, 2, 2], 3) == [[1, 2]]

def test_two_sum_zero_target_with_mixed():
    assert _two_sum([-2, -1, 0, 1, 2], 0) == [[-2, 2], [-1, 1], [0, 0]]

def test_two_sum_all_negative():
    assert _two_sum([-5, -4, -3, -2, -1], -3) == [[-5, 2], [-4, 1], [-3, 0], [-2, -1]]

def test_two_sum_all_positive():
    assert _two_sum([1, 2, 3, 4, 5], 9) == [[4, 5]]

def test_two_sum_with_zero_in_middle():
    assert _two_sum([-1, 0, 1], 0) == [[-1, 1], [0, 0]]