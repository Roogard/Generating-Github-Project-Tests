from algorithms.searching.binary_search import binary_search

# --- Statement Coverage ---
def test_empty_array():
    # Covers: low = 0, high = -1, while condition false, return -1
    result = binary_search([], 5)
    # For empty array, query cannot be found
    assert result == -1

def test_single_element_found():
    # Covers: while true, mid = 0, val == query, return mid
    result = binary_search([7], 7)
    # Query is the only element, index 0
    assert result == 0

def test_single_element_not_found_lower():
    # Covers: while true, mid = 0, val < query, low = mid + 1, while false, return -1
    result = binary_search([7], 3)
    # Query less than only element, not found
    assert result == -1

def test_single_element_not_found_higher():
    # Covers: while true, mid = 0, val > query, high = mid - 1, while false, return -1
    result = binary_search([7], 10)
    # Query greater than only element, not found
    assert result == -1

def test_multiple_elements_found_middle():
    # Covers: while true, mid computed, val == query, return mid
    result = binary_search([1, 2, 3, 4, 5], 3)
    # Query at index 2
    assert result == 2

def test_multiple_elements_found_first():
    # Covers: while true, val == query at first iteration or after adjustments
    result = binary_search([1, 2, 3, 4, 5], 1)
    # Query at index 0
    assert result == 0

def test_multiple_elements_found_last():
    result = binary_search([1, 2, 3, 4, 5], 5)
    # Query at index 4
    assert result == 4

def test_multiple_elements_not_found():
    # Covers: while loop with adjustments until low > high, return -1
    result = binary_search([1, 2, 3, 4, 5], 6)
    # Query not in array
    assert result == -1

# --- Block Coverage ---
# Block coverage is satisfied by statement coverage for this function.
# The while loop body and the two if branches are covered.
# No new blocks beyond those already covered.

# --- Condition Coverage ---
def test_condition_val_eq_query_true():
    # val == query: True
    result = binary_search([10, 20, 30], 20)
    assert result == 1

def test_condition_val_eq_query_false_val_lt_query_true():
    # val == query: False, val < query: True
    # Path: query greater than mid, low adjusted
    result = binary_search([10, 20, 30], 25)
    # 25 not in array, should return -1
    assert result == -1

def test_condition_val_eq_query_false_val_lt_query_false():
    # val == query: False, val < query: False (i.e., val > query)
    # Path: query less than mid, high adjusted
    result = binary_search([10, 20, 30], 15)
    # 15 not in array, should return -1
    assert result == -1

# The while condition `low <= high` is covered by previous tests (true and false cases).

# --- Path Coverage ---
# Path 1: Empty array, loop zero iterations, return -1
# Covered by test_empty_array

# Path 2: Single element, found on first iteration
# Covered by test_single_element_found

# Path 3: Single element, not found, val < query, loop ends
# Covered by test_single_element_not_found_lower

# Path 4: Single element, not found, val > query, loop ends
# Covered by test_single_element_not_found_higher

# Path 5: Multiple elements, found on first mid
# Covered by test_multiple_elements_found_middle (if mid is exactly query)

# Path 6: Multiple elements, found after several adjustments (val < query path taken multiple times)
def test_path_found_after_multiple_low_adjustments():
    # path: while true, val < query repeatedly, then val == query
    result = binary_search([1, 3, 5, 7, 9, 11, 13], 11)
    # 11 at index 5, search will adjust low several times
    assert result == 5

# Path 7: Multiple elements, found after several adjustments (val > query path taken multiple times)
def test_path_found_after_multiple_high_adjustments():
    # path: while true, val > query repeatedly, then val == query
    result = binary_search([1, 3, 5, 7, 9, 11, 13], 3)
    # 3 at index 1, search may adjust high
    assert result == 1

# Path 8: Multiple elements, not found, alternating adjustments until exhaustion
def test_path_not_found_exhaustive():
    # path: while true, val < query and val > query adjustments until low > high
    result = binary_search([1, 3, 5, 7, 9, 11, 13], 8)
    # 8 not in array
    assert result == -1

# Path 9: Two elements, found second after one low adjustment
def test_path_two_elements_found_second():
    # path: while true, val < query, low adjusted, next iteration val == query
    result = binary_search([5, 10], 10)
    assert result == 1

# Path 10: Two elements, found first after one high adjustment
def test_path_two_elements_found_first():
    # path: while true, val > query, high adjusted, next iteration val == query
    result = binary_search([5, 10], 5)
    assert result == 0

# Path 11: Two elements, not found between them
def test_path_two_elements_not_found_between():
    # path: while true, val < query? Actually mid=0, val=5 < 7 -> low=1, next iteration low=1, high=1, mid=1, val=10 > 7 -> high=0, loop ends
    result = binary_search([5, 10], 7)
    assert result == -1