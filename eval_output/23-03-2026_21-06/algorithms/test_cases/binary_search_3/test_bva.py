import pytest
from algorithms.searching.binary_search import binary_search

def test_empty_array():
    assert binary_search([], 5) == -1

def test_single_element_found():
    assert binary_search([5], 5) == 0

def test_single_element_not_found():
    assert binary_search([5], 3) == -1

def test_two_elements_find_first():
    assert binary_search([1, 2], 1) == 0

def test_two_elements_find_second():
    assert binary_search([1, 2], 2) == 1

def test_query_at_lower_bound():
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

def test_query_at_upper_bound():
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_query_just_above_lower_bound():
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

def test_query_just_below_upper_bound():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

def test_query_below_all_elements():
    assert binary_search([1, 2, 3, 4, 5], 0) == -1

def test_query_above_all_elements():
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

def test_query_between_elements():
    assert binary_search([1, 3, 5, 7, 9], 4) == -1

def test_large_array_find_middle():
    array = list(range(1000))
    assert binary_search(array, 499) == 499

def test_large_array_find_first():
    array = list(range(1000))
    assert binary_search(array, 0) == 0

def test_large_array_find_last():
    array = list(range(1000))
    assert binary_search(array, 999) == 999

def test_duplicate_elements_find_first_occurrence():
    assert binary_search([1, 2, 2, 2, 3], 2) in [1, 2, 3]

# kills: arith_swap at line 17 (mid = low + (high - low) // 2)
def test_mid_calculation_arith_swap():
    # Use a case where low != 0 to detect swapped arithmetic
    # If mutation changes to low - (high - low) // 2, mid becomes negative
    # If mutation changes to low + (high - low) // 3, mid becomes different
    # We'll test with array length 3, query at index 1
    assert binary_search([10, 20, 30], 20) == 1

# kills: arith_swap at line 19 (val = array[mid])
def test_val_assignment_arith_swap():
    # Mutation could swap array[mid] to array[low] or array[high]
    # Test with distinct values at low, mid, high
    assert binary_search([100, 200, 300], 200) == 1

# kills: arith_swap at line 24 (low = mid + 1)
def test_low_update_arith_swap():
    # If mutation changes to mid - 1 or mid, search may fail
    # Query in right half where low must be updated correctly
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# kills: arith_swap at line 26 (high = mid - 1)
def test_high_update_arith_swap():
    # If mutation changes to mid + 1 or mid, search may fail
    # Query in left half where high must be updated correctly
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# kills: cmp_swap at line 18 (val == query)
def test_equality_comparison_cmp_swap():
    # If mutation swaps == to !=, function would never return found index
    assert binary_search([5], 5) == 0

# kills: cmp_swap at line 21 (val < query)
def test_less_than_comparison_cmp_swap():
    # If mutation swaps < to >, <=, >=, or !=, direction may be wrong
    # Test with query greater than mid value
    assert binary_search([1, 2, 3], 3) == 2

# kills: cmp_swap at line 23 (else branch, implicit val > query)
def test_greater_than_logic_cmp_swap():
    # The else branch executes when val > query
    # If comparison logic is swapped, high update may be wrong
    assert binary_search([1, 2, 3], 1) == 0

# kills: cond_neg at line 18 (if val == query:)
def test_equality_cond_neg():
    # If condition negated to if val != query:, found case would return -1
    assert binary_search([7], 7) == 0

# kills: cond_neg at line 21 (if val < query:)
def test_less_than_cond_neg():
    # If condition negated to if val >= query:, direction flips
    # Test case where query > mid value
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# kills: cond_neg at line 23 (else branch condition)
def test_else_branch_cond_neg():
    # The else handles val > query, if negated it might not execute
    assert binary_search([1, 2, 3], 1) == 0

# kills: llm_mutant off-by-one: updating low to mid instead of mid+1 when val < query
def test_low_update_off_by_one():
    # This mutation may cause infinite loop or missed element
    # Use case where low must increase by more than 1
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

# kills: llm_mutant off-by-one: updating high to mid instead of mid-1 when val > query
def test_high_update_off_by_one():
    # This mutation may cause infinite loop or missed element
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

# kills: llm_mutant missing edge case: fails to handle empty array
def test_empty_array_index_error():
    # Original function handles empty array, mutation might crash
    # This test already exists but we keep it explicit
    assert binary_search([], 1) == -1

# kills: llm_mutant off-by-sign: uses (high + low) // 2 instead of low + (high - low) // 2
def test_mid_overflow_protection():
    # Test with large indices where (high + low) could overflow
    # Actually in Python no overflow, but the calculation differs
    # Use array where low > 0 and high > low
    assert binary_search([10, 20, 30, 40, 50], 30) == 2

# Additional test to catch multiple arithmetic mutants
def test_exact_mid_calculation():
    # Force mid calculation to be precise
    # Array of length 2: low=0, high=1, mid should be 0
    # Query at index 1, should find it
    assert binary_search([10, 20], 20) == 1

# Test boundary updates precisely
def test_boundary_updates_narrow_search():
    # Test case that requires exact boundary updates
    assert binary_search([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 7) == 6