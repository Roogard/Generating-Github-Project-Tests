import pytest
from algorithms.backtracking.array_sum_combinations import _get_candidates

def test_get_candidates_with_empty_list():
    candidates = _get_candidates([])
    # Should return all numbers from the global list that are <= target
    # Assuming global list is [1, 2, 3, 4, 5, 6] and target is 7 from context
    # Expected candidates are numbers <= 7, which is all numbers [1, 2, 3, 4, 5, 6]
    assert set(candidates) == {1, 2, 3, 4, 5, 6}

def test_get_candidates_with_sum_at_target():
    # Assuming target is 7
    # If constructed_so_far sum is 7, should return empty list
    candidates = _get_candidates([7])
    assert candidates == []

def test_get_candidates_with_sum_exceeding_target():
    # If constructed_so_far sum > target, should return empty list
    candidates = _get_candidates([8])
    assert candidates == []

def test_get_candidates_with_sum_one_below_target():
    # If constructed_so_far sum is 6 (target-1), candidates should be numbers <= 1
    candidates = _get_candidates([6])
    assert set(candidates) == {1}

def test_get_candidates_with_sum_two_below_target():
    # If constructed_so_far sum is 5 (target-2), candidates should be numbers <= 2
    candidates = _get_candidates([5])
    assert set(candidates) == {1, 2}

def test_get_candidates_with_duplicate_numbers_sum():
    # Test with multiple numbers in constructed_so_far
    candidates = _get_candidates([2, 3])  # sum = 5
    assert set(candidates) == {1, 2}

def test_get_candidates_with_max_possible_sum():
    # Start with empty, max candidate is 6 (from global list)
    # If we add 6, remaining capacity is 1
    candidates = _get_candidates([6])
    assert set(candidates) == {1}

def test_get_candidates_with_zero_remaining_capacity():
    # Exactly at target
    candidates = _get_candidates([7])
    assert candidates == []

def test_get_candidates_with_negative_remaining_capacity():
    # Exceeded target
    candidates = _get_candidates([10])
    assert candidates == []

def test_get_candidates_with_single_element_at_lower_bound():
    # Smallest number in global list is 1
    candidates = _get_candidates([1])
    # Remaining capacity = 6, candidates are numbers <= 6
    assert set(candidates) == {1, 2, 3, 4, 5, 6}