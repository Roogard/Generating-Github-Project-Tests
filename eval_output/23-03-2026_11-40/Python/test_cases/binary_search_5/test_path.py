import pytest
from matrix.binary_search_matrix import binary_search

# path: array[r] == value → return r (found immediately)
def test_binary_search_found_midpoint():
    assert binary_search([1, 4, 7, 11, 15], 0, 4, 7) == 2

# path: lower_bound >= upper_bound → return -1 (not found, search space exhausted)
def test_binary_search_not_found_single_element():
    assert binary_search([5], 0, 0, 3) == -1

# path: array[r] < value → recursive call (right half) → eventual found
def test_binary_search_found_in_right_half():
    assert binary_search([1, 4, 7, 11, 15], 0, 4, 11) == 3

# path: array[r] < value → recursive call (right half) → eventual not found
def test_binary_search_not_found_in_right_half():
    assert binary_search([1, 4, 7, 11, 15], 0, 4, 23) == -1

# path: array[r] > value → recursive call (left half) → eventual found
def test_binary_search_found_in_left_half():
    assert binary_search([1, 4, 7, 11, 15], 0, 4, 4) == 1

# path: array[r] > value → recursive call (left half) → eventual not found
def test_binary_search_not_found_in_left_half():
    assert binary_search([1, 4, 7, 11, 15], 0, 4, 0) == -1

# path: array[r] == value on first call with odd-sized range
def test_binary_search_found_midpoint_odd_range():
    assert binary_search([2, 5, 8], 0, 2, 5) == 1

# path: array[r] == value on first call with even-sized range (lower mid)
def test_binary_search_found_midpoint_even_range():
    assert binary_search([2, 5, 8, 10], 0, 3, 5) == 1

# path: recursive path where array[r] < value leads to a later array[r] == value
def test_binary_search_found_after_multiple_right_recursions():
    assert binary_search([1, 3, 5, 7, 9, 11, 13], 0, 6, 13) == 6

# path: recursive path where array[r] > value leads to a later array[r] == value
def test_binary_search_found_after_multiple_left_recursions():
    assert binary_search([1, 3, 5, 7, 9, 11, 13], 0, 6, 1) == 0

# path: recursive path where array[r] < value leads to lower_bound >= upper_bound
def test_binary_search_not_found_after_right_recursion_exhaust():
    assert binary_search([1, 3, 5], 0, 2, 6) == -1

# path: recursive path where array[r] > value leads to lower_bound >= upper_bound
def test_binary_search_not_found_after_left_recursion_exhaust():
    assert binary_search([1, 3, 5], 0, 2, 0) == -1

# path: lower_bound == upper_bound and array[r] != value → return -1 (single element, not found)
def test_binary_search_single_element_not_found():
    assert binary_search([10], 0, 0, 5) == -1

# path: lower_bound == upper_bound and array[r] == value → return r (single element, found)
def test_binary_search_single_element_found():
    assert binary_search([10], 0, 0, 10) == 0

# path: array[r] < value → recursive call → array[r] == value on deeper call
def test_binary_search_found_deep_right():
    assert binary_search([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0, 9, 10) == 9

# path: array[r] > value → recursive call → array[r] == value on deeper call
def test_binary_search_found_deep_left():
    assert binary_search([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 0, 9, 1) == 0