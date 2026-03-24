import pytest
from algorithms.searching.binary_search import binary_search

def test_empty_array():
    assert binary_search([], 5) == -1

def test_single_element_found():
    assert binary_search([7], 7) == 0

def test_single_element_not_found():
    assert binary_search([7], 5) == -1

def test_two_elements_find_first():
    assert binary_search([1, 2], 1) == 0

def test_two_elements_find_second():
    assert binary_search([1, 2], 2) == 1

def test_three_elements_find_middle():
    assert binary_search([1, 2, 3], 2) == 1

def test_query_at_lower_bound():
    assert binary_search([0, 10, 20, 30, 40], 0) == 0

def test_query_just_above_lower_bound():
    assert binary_search([0, 10, 20, 30, 40], 10) == 1

def test_query_at_upper_bound():
    assert binary_search([0, 10, 20, 30, 40], 40) == 4

def test_query_just_below_upper_bound():
    assert binary_search([0, 10, 20, 30, 40], 30) == 3

def test_query_below_all_elements():
    assert binary_search([10, 20, 30, 40, 50], 5) == -1

def test_query_above_all_elements():
    assert binary_search([10, 20, 30, 40, 50], 55) == -1

def test_query_between_elements():
    assert binary_search([10, 20, 30, 40, 50], 25) == -1

def test_large_array_find_first():
    arr = list(range(1000))
    assert binary_search(arr, 0) == 0

def test_large_array_find_last():
    arr = list(range(1000))
    assert binary_search(arr, 999) == 999

def test_large_array_find_middle():
    arr = list(range(1000))
    assert binary_search(arr, 499) == 499

def test_large_array_find_middle_plus_one():
    arr = list(range(1000))
    assert binary_search(arr, 500) == 500

def test_duplicate_elements_find_first_occurrence():
    assert binary_search([1, 2, 2, 2, 3], 2) in [1, 2, 3]

def test_all_identical_elements_found():
    assert binary_search([5, 5, 5, 5], 5) in [0, 1, 2, 3]

def test_all_identical_elements_not_found():
    assert binary_search([5, 5, 5, 5], 3) == -1