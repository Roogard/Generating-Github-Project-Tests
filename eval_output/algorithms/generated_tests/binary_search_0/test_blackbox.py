from algorithms.searching.binary_search import binary_search

# --- BVA ---

def test_bva_empty_array():
    # Boundary: empty collection
    assert binary_search([], 5) == -1

def test_bva_single_element_found():
    # Boundary: single element collection, found
    assert binary_search([7], 7) == 0

def test_bva_single_element_not_found():
    # Boundary: single element collection, not found
    assert binary_search([7], 3) == -1

def test_bva_min_index():
    # Boundary: query at min index (0)
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

def test_bva_max_index():
    # Boundary: query at max index (len-1)
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_bva_just_below_min():
    # Boundary: query just below smallest element
    assert binary_search([10, 20, 30], 5) == -1

def test_bva_just_above_max():
    # Boundary: query just above largest element
    assert binary_search([10, 20, 30], 35) == -1

def test_bva_large_array():
    # Boundary: large collection, query in middle
    arr = list(range(1000))
    assert binary_search(arr, 500) == 500

# --- ECP ---

def test_ecp_valid_middle():
    # Valid class: query present in middle of array
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

def test_ecp_valid_first_half():
    # Valid class: query present in first half
    assert binary_search([1, 2, 3, 4, 5, 6, 7], 2) == 1

def test_ecp_valid_second_half():
    # Valid class: query present in second half
    assert binary_search([1, 2, 3, 4, 5, 6, 7], 6) == 5

def test_ecp_invalid_not_present():
    # Invalid class: query not in array (within range)
    assert binary_search([1, 3, 5, 7, 9], 4) == -1

def test_ecp_invalid_below_range():
    # Invalid class: query below array range
    assert binary_search([10, 20, 30], 5) == -1

def test_ecp_invalid_above_range():
    # Invalid class: query above array range
    assert binary_search([10, 20, 30], 50) == -1

def test_ecp_valid_duplicate_elements():
    # Valid class: array with duplicate elements, must return an index of the query
    # For binary search on sorted array with duplicates, any matching index is correct.
    result = binary_search([1, 2, 2, 2, 3], 2)
    assert result in [1, 2, 3]

# --- Mutation Detection ---

def test_mutation_off_by_one_loop_condition():
    # detects off-by-one in loop bound: if loop used < instead of <=, would miss single-element match
    assert binary_search([5], 5) == 0

def test_mutation_wrong_operator_in_low_update():
    # detects wrong operator: if low = mid (instead of mid+1) when val < query, may loop forever or miss
    # This test uses a query greater than mid in a multi-element array.
    assert binary_search([1, 2, 3, 4, 5], 5) == 4

def test_mutation_wrong_operator_in_high_update():
    # detects wrong operator: if high = mid (instead of mid-1) when val > query, may loop forever or miss
    # This test uses a query smaller than mid in a multi-element array.
    assert binary_search([1, 2, 3, 4, 5], 1) == 0

def test_mutation_boundary_inclusivity():
    # detects boundary inclusivity: if high initialized as len(array) instead of len(array)-1, may cause index error
    # Property: function must not raise IndexError for any valid input.
    try:
        binary_search([1, 2, 3], 2)
    except IndexError:
        assert False, "IndexError indicates wrong high initialization"

def test_mutation_missing_negation_in_found_check():
    # detects missing negation: if condition were val != query for found case, would return -1 incorrectly
    assert binary_search([10, 20, 30], 20) == 1

def test_mutation_wrong_constant_return():
    # detects wrong constant: if function returned 0 instead of -1 for not found
    assert binary_search([1, 2, 3], 4) == -1

def test_mutation_off_by_one_mid_calculation():
    # detects off-by-one in mid calculation: if used (high+low)//2 without adjustment, still correct but property test
    # For large range, the search should still find the element.
    arr = list(range(10000))
    assert binary_search(arr, 5000) == 5000