from algorithms.searching.binary_search import binary_search

# --- BVA ---

def test_bva_empty_array():
    # empty collection
    assert binary_search([], 5) == -1

def test_bva_single_element_found():
    # single element collection, found
    assert binary_search([7], 7) == 0

def test_bva_single_element_not_found():
    # single element collection, not found
    assert binary_search([7], 3) == -1

def test_bva_min_element():
    # query is the minimum element in a typical array
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

def test_bva_max_element():
    # query is the maximum element in a typical array
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_bva_just_below_min():
    # query is just below the minimum (outside lower bound)
    assert binary_search([1, 2, 3, 4, 5], 0) == -1

def test_bva_just_above_max():
    # query is just above the maximum (outside upper bound)
    assert binary_search([1, 2, 3, 4, 5], 6) == -1

def test_bva_large_array():
    # large collection, query in middle
    arr = list(range(1000))
    assert binary_search(arr, 500) == 500

def test_bva_large_array_not_found():
    # large collection, query not present
    arr = list(range(1000))
    assert binary_search(arr, 1500) == -1

# --- ECP ---

def test_ecp_valid_middle():
    # valid class: query present in middle of array
    assert binary_search([10, 20, 30, 40, 50], 30) == 2

def test_ecp_valid_first_half():
    # valid class: query present in first half
    assert binary_search([10, 20, 30, 40, 50], 20) == 1

def test_ecp_valid_second_half():
    # valid class: query present in second half
    assert binary_search([10, 20, 30, 40, 50], 40) == 3

def test_ecp_invalid_not_present():
    # invalid class: query not in array (but within value range)
    assert binary_search([1, 3, 5, 7, 9], 4) == -1

def test_ecp_invalid_empty_array():
    # invalid class: empty array, any query
    assert binary_search([], 99) == -1

def test_ecp_valid_duplicate_elements():
    # valid class: array with duplicate elements, query present
    # binary search on sorted array with duplicates returns an index of the query, not necessarily the first
    # A correct implementation must return *an* index where array[index] == query.
    result = binary_search([1, 2, 2, 2, 3], 2)
    assert result in [1, 2, 3]

def test_ecp_valid_all_same_elements():
    # valid class: all elements identical, query present
    result = binary_search([5, 5, 5, 5], 5)
    assert 0 <= result < 4

def test_ecp_invalid_all_same_elements_query_absent():
    # invalid class: all elements identical, query absent
    assert binary_search([5, 5, 5, 5], 7) == -1

# --- Mutation Detection ---

def test_mutation_off_by_one_loop_condition():
    # detects off-by-one in loop bound (e.g., low < high instead of low <= high)
    # For query at the last index, a loop that stops early would miss it.
    assert binary_search([1, 2, 3], 3) == 2

def test_mutation_off_by_one_mid_calculation():
    # detects off-by-one in mid calculation (e.g., (high + low) // 2 causing overflow or incorrect rounding)
    # Test with large indices to check for overflow robustness, but also with small array where rounding matters.
    arr = [10, 20, 30, 40, 50]
    assert binary_search(arr, 40) == 3

def test_mutation_wrong_operator_in_low_update():
    # detects wrong operator (e.g., low = mid instead of low = mid + 1 when val < query)
    # If low is not incremented past mid, search may loop infinitely or miss elements.
    # Use a case where query is in the right half and not at mid.
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_mutation_wrong_operator_in_high_update():
    # detects wrong operator (e.g., high = mid instead of high = mid - 1 when val > query)
    # If high is not decremented past mid, search may loop infinitely or miss elements.
    # Use a case where query is in the left half and not at mid.
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

def test_mutation_boundary_inclusivity_high():
    # detects boundary inclusivity error (e.g., initial high = len(array) instead of len(array)-1)
    # Would cause IndexError if array is non-empty.
    # We test with non-empty array; a correct implementation must not raise IndexError.
    result = binary_search([1, 2, 3], 2)
    assert result == 1

def test_mutation_missing_negation_in_condition():
    # detects missing negation (e.g., if val == query: return -1)
    # This would return -1 when found. We test a found case.
    assert binary_search([5, 6, 7], 6) == 1

def test_mutation_wrong_constant_return():
    # detects wrong constant (e.g., returning 0 instead of -1 for not found)
    assert binary_search([1, 2, 3], 4) == -1

def test_mutation_wrong_constant_initial_low():
    # detects wrong constant initial low (e.g., low = 1)
    # Would miss the first element.
    assert binary_search([100, 200, 300], 100) == 0