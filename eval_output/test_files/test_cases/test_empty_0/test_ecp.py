import pytest
from algorithms.backtracking import check_sum

# Valid equivalence class: sum equals target
def test_check_sum_valid_match():
    result = check_sum([1, 2, 3], 6)
    assert result == (True, [1, 2, 3])

# Valid equivalence class: sum does not equal target
def test_check_sum_valid_no_match():
    result = check_sum([1, 2, 3], 7)
    assert result == (False, [1, 2, 3])

# Valid equivalence class: empty list, target zero
def test_check_sum_empty_list_target_zero():
    result = check_sum([], 0)
    assert result == (True, [])

# Valid equivalence class: empty list, target non-zero
def test_check_sum_empty_list_target_non_zero():
    result = check_sum([], 5)
    assert result == (False, [])

# Valid equivalence class: single element list, matches target
def test_check_sum_single_element_match():
    result = check_sum([5], 5)
    assert result == (True, [5])

# Valid equivalence class: single element list, does not match target
def test_check_sum_single_element_no_match():
    result = check_sum([5], 3)
    assert result == (False, [5])

# Valid equivalence class: negative numbers, sum matches target
def test_check_sum_negative_numbers_match():
    result = check_sum([-1, -2, 3], 0)
    assert result == (True, [-1, -2, 3])

# Valid equivalence class: negative numbers, sum does not match target
def test_check_sum_negative_numbers_no_match():
    result = check_sum([-1, -2, 3], 5)
    assert result == (False, [-1, -2, 3])

# Valid equivalence class: zero values, sum matches target zero
def test_check_sum_all_zeros_target_zero():
    result = check_sum([0, 0, 0], 0)
    assert result == (True, [0, 0, 0])

# Valid equivalence class: zero values, sum does not match non-zero target
def test_check_sum_all_zeros_target_non_zero():
    result = check_sum([0, 0, 0], 1)
    assert result == (False, [0, 0, 0])