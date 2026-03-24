from algorithms.searching.binary_search import binary_search

# Block mapping:
# block 1: low, high = 0, len(array) - 1
# block 2: while low <= high: (loop header)
# block 3: mid = low + (high - low) // 2; val = array[mid]
# block 4: if val == query: return mid
# block 5: if val < query: low = mid + 1
# block 6: else: high = mid - 1
# block 7: return -1 (while loop condition false)

# covers: block 1, block 2 (enters loop), block 3, block 4, block 7 (loop not entered)
def test_empty_array():
    assert binary_search([], 5) == -1

# covers: block 1, block 2 (enters loop), block 3, block 4 (found first iteration), block 7 (not reached)
def test_single_element_found():
    assert binary_search([7], 7) == 0

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (val < query), block 6 (not taken), block 2 (loop continues), block 7 (not reached)
def test_single_element_not_found_query_greater():
    assert binary_search([3], 5) == -1

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (not taken), block 6 (val > query), block 2 (loop continues), block 7 (not reached)
def test_single_element_not_found_query_smaller():
    assert binary_search([8], 5) == -1

# covers: block 1, block 2 (enters loop), block 3, block 4 (found at mid), block 7 (not reached)
def test_multi_element_found_at_mid():
    assert binary_search([1, 2, 3, 4, 5], 3) == 2

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (val < query), block 6 (not taken), block 2 (loop continues), block 3, block 4 (found after moving low), block 7 (not reached)
def test_multi_element_found_after_low_move():
    assert binary_search([1, 2, 3, 4, 5], 4) == 3

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (not taken), block 6 (val > query), block 2 (loop continues), block 3, block 4 (found after moving high), block 7 (not reached)
def test_multi_element_found_after_high_move():
    assert binary_search([1, 2, 3, 4, 5], 2) == 1

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (val < query), block 6 (not taken), block 2 (loop continues), repeated until low>high, block 7 (exit loop)
def test_multi_element_not_found_query_greater():
    assert binary_search([1, 3, 5, 7, 9], 10) == -1

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (not taken), block 6 (val > query), block 2 (loop continues), repeated until low>high, block 7 (exit loop)
def test_multi_element_not_found_query_smaller():
    assert binary_search([1, 3, 5, 7, 9], 0) == -1

# covers: block 1, block 2 (enters loop), block 3, block 4 (not equal), block 5 (val < query), block 6 (not taken), block 2 (loop continues), block 3, block 4 (not equal), block 5 (not taken), block 6 (val > query), block 2 (loop continues), block 3, block 4 (found), block 7 (not reached)
def test_multi_element_found_after_both_moves():
    assert binary_search([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 7) == 6