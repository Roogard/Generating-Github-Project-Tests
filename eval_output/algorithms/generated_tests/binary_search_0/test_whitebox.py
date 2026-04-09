import pytest
from algorithms.searching.binary_search import binary_search

# --- Statement Coverage ---
def test_empty_array():
    # Covers: low = 0, high = -1, while condition false, return -1
    assert binary_search([], 5) == -1

def test_single_element_found():
    # Covers: while true, mid = 0, val == query, return mid
    assert binary_search([5], 5) == 0

def test_single_element_not_found():
    # Covers: while true, mid = 0, val != query, val < query or val > query, loop ends, return -1
    # Expected output derived from algorithm: 5 is not in [3], so -1
    assert binary_search([3], 5) == -1

def test_multiple_elements_found_middle():
    # Covers: while loop, mid calculation, val == query at first mid
    # From specification: index of query in sorted array
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

def test_multiple_elements_not_found():
    # Covers: while loop, val < query and val > query branches, loop ends, return -1
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

# --- Block Coverage ---
# All blocks covered by statement coverage above.
# No new blocks to add.

# --- Condition Coverage ---
# The loop condition is low <= high.
# The condition inside loop: val == query, val < query, else (val > query).
# We need to cover all truth values for the compound condition (low <= high) and the branches.

def test_condition_low_le_high_true():
    # low <= high: True (enters loop)
    # val == query: True (returns early)
    assert binary_search([10], 10) == 0

def test_condition_low_le_high_false():
    # low <= high: False (skips loop)
    # This is covered by empty array test.
    pass

def test_condition_val_eq_query_false_val_lt_query_true():
    # val == query: False, val < query: True
    # Path: while true, val != query, val < query, low = mid + 1
    # Example: search for 5 in [1,2,3,4,6] -> eventually high < low, return -1
    assert binary_search([1, 2, 3, 4, 6], 5) == -1

def test_condition_val_eq_query_false_val_lt_query_false():
    # val == query: False, val < query: False (so val > query)
    # Path: while true, val != query, val > query, high = mid - 1
    # Example: search for 3 in [1,2,4,5,6] -> eventually high < low, return -1
    assert binary_search([1, 2, 4, 5, 6], 3) == -1

# --- Path Coverage ---
# Paths are determined by sequences of branches in the loop.
# We need to cover different numbers of loop iterations and sequences of val < query / val > query.

def test_path_zero_iterations():
    # Path: low > high initially, return -1
    assert binary_search([], 1) == -1

def test_path_one_iteration_found():
    # Path: enter loop, mid, val == query, return mid
    assert binary_search([7], 7) == 0

def test_path_one_iteration_not_found_val_lt():
    # Path: enter loop, val != query, val < query, low = mid+1, loop condition false, return -1
    assert binary_search([2], 5) == -1

def test_path_one_iteration_not_found_val_gt():
    # Path: enter loop, val != query, val > query, high = mid-1, loop condition false, return -1
    assert binary_search([8], 5) == -1

def test_path_two_iterations_val_lt_then_found():
    # Path: first iteration: val < query, second iteration: val == query
    # Array: [1, 3, 5], query 3.
    # Iter1: low=0, high=2, mid=1, val=3 == query? No, val < query? 3 < 3? False, else: high=0.
    # Wait, that's not correct. Let's design properly.
    # We need val < query first, then val == query.
    # Example: [1, 2, 3], query 2.
    # Iter1: low=0, high=2, mid=1, val=2 == query? True -> returns. That's one iteration.
    # Need two iterations: first iteration val != query and val < query, second iteration val == query.
    # Example: [1, 2, 3, 4], query 3.
    # Iter1: low=0, high=3, mid=1, val=2 !=3, val<3 -> low=2.
    # Iter2: low=2, high=3, mid=2, val=3 == query -> return 2.
    assert binary_search([1, 2, 3, 4], 3) == 2

def test_path_two_iterations_val_gt_then_found():
    # Path: first iteration val > query, second iteration val == query.
    # Example: [1, 2, 3, 4], query 2.
    # Iter1: low=0, high=3, mid=1, val=2 == query? True -> returns. Not two iterations.
    # Need: first iteration val > query.
    # Example: [1, 3, 4, 5], query 3.
    # Iter1: low=0, high=3, mid=1, val=3 == query? True -> returns. Not good.
    # Let's try: [2, 3, 4, 5], query 3.
    # Iter1: low=0, high=3, mid=1, val=3 == query? True -> returns.
    # We need the first mid to be greater than query.
    # So array length 4, query at index 1, but first mid index 1? That's the query.
    # To get first mid not query and val > query, we need query in left half and first mid picks right half.
    # Example: [1, 2, 4, 5, 6], query 2.
    # Iter1: low=0, high=4, mid=2, val=4 > 2 -> high=1.
    # Iter2: low=0, high=1, mid=0, val=1 < 2 -> low=1.
    # Iter3: low=1, high=1, mid=1, val=2 == query -> return 1. That's three iterations.
    # Let's aim for two iterations: first val > query, second val == query.
    # Array length 3: [3, 4, 5], query 3.
    # Iter1: low=0, high=2, mid=1, val=4 > 3 -> high=0.
    # Iter2: low=0, high=0, mid=0, val=3 == query -> return 0.
    assert binary_search([3, 4, 5], 3) == 0

def test_path_multiple_iterations_val_lt_val_lt_found():
    # Path: val < query multiple times, then found.
    # Example: [1, 2, 3, 4, 5], query 5.
    # Iter1: mid=2, val=3 <5 -> low=3.
    # Iter2: mid=3, val=4 <5 -> low=4.
    # Iter3: mid=4, val=5 ==5 -> return 4.
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_path_multiple_iterations_val_gt_val_gt_found():
    # Path: val > query multiple times, then found.
    # Example: [1, 2, 3, 4, 5], query 1.
    # Iter1: mid=2, val=3 >1 -> high=1.
    # Iter2: mid=0, val=1 ==1 -> return 0.
    # That's two iterations. Let's do three.
    # Array: [1, 2, 3, 4, 5, 6, 7], query 1.
    # Iter1: mid=3, val=4 >1 -> high=2.
    # Iter2: mid=1, val=2 >1 -> high=0.
    # Iter3: mid=0, val=1 ==1 -> return 0.
    assert binary_search([1, 2, 3, 4, 5, 6, 7], 1) == 0

def test_path_multiple_iterations_not_found():
    # Path: alternating or series of comparisons until low > high.
    # Example: [1, 3, 5, 7], query 4.
    # Iter1: mid=1, val=3 <4 -> low=2.
    # Iter2: mid=2, val=5 >4 -> high=1.
    # Now low=2, high=1, loop ends, return -1.
    assert binary_search([1, 3, 5, 7], 4) == -1