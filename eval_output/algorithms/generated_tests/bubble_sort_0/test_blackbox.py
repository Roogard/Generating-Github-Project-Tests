from algorithms.sorting.bubble_sort import bubble_sort

# --- BVA ---

def test_bva_empty_list():
    # Input: empty collection (min size)
    result = bubble_sort([])
    # Expected: sorted empty list
    assert result == []

def test_bva_single_element():
    # Input: single element collection
    result = bubble_sort([5])
    # Expected: list unchanged
    assert result == [5]

def test_bva_two_elements():
    # Input: smallest non-trivial size (min+1 for sorting)
    result = bubble_sort([2, 1])
    # Expected: sorted ascending
    assert result == [1, 2]

def test_bva_typical_size():
    # Input: typical size list
    result = bubble_sort([5, 3, 1, 4, 2])
    # Expected: sorted ascending
    assert result == [1, 2, 3, 4, 5]

def test_bva_already_sorted():
    # Input: max orderedness (already sorted)
    result = bubble_sort([1, 2, 3, 4, 5])
    # Expected: unchanged
    assert result == [1, 2, 3, 4, 5]

def test_bva_reverse_sorted():
    # Input: min orderedness (reverse sorted)
    result = bubble_sort([5, 4, 3, 2, 1])
    # Expected: fully sorted ascending
    assert result == [1, 2, 3, 4, 5]

def test_bva_duplicate_values():
    # Input: list with duplicate elements (boundary for equality)
    result = bubble_sort([3, 1, 3, 2])
    # Expected: sorted with duplicates preserved
    assert result == [1, 2, 3, 3]

# --- ECP ---

def test_valid_positive_integers():
    # Valid class: typical positive integers
    result = bubble_sort([10, 3, 8])
    assert result == [3, 8, 10]

def test_valid_negative_integers():
    # Valid class: negative integers
    result = bubble_sort([-5, -1, -10])
    assert result == [-10, -5, -1]

def test_valid_mixed_sign_integers():
    # Valid class: mixed positive and negative integers
    result = bubble_sort([0, -3, 5, -1])
    assert result == [-3, -1, 0, 5]

def test_valid_large_range():
    # Valid class: large range of values
    result = bubble_sort([1000, -1000, 0])
    assert result == [-1000, 0, 1000]

def test_valid_single_duplicate_all():
    # Valid class: all elements identical
    result = bubble_sort([7, 7, 7])
    assert result == [7, 7, 7]

# The function signature specifies list[int]. Non-integer lists, None, or other types
# are invalid classes but would cause a type error at runtime, which is outside
# pure blackbox testing based on the spec. We rely on Python's type system/checker.
# No explicit invalid class tests are added as they would require type violations.

# --- Mutation Detection ---

def test_mutation_off_by_one_loop_start():
    # detects off-by-one in loop bound (e.g., range(0, n - passes))
    input_list = [2, 1]
    result = bubble_sort(input_list)
    # Correct implementation must sort
    assert result == [1, 2]

def test_mutation_off_by_one_loop_end():
    # detects off-by-one in loop bound (e.g., range(1, n - passes + 1))
    input_list = [3, 2, 1]
    result = bubble_sort(input_list)
    # Correct implementation must fully sort
    assert result == [1, 2, 3]

def test_mutation_wrong_comparison_operator():
    # detects wrong operator (e.g., < instead of >)
    input_list = [1, 3, 2]
    result = bubble_sort(input_list)
    # With wrong operator, list might become unsorted or reverse sorted
    # Correct must be ascending
    assert result == [1, 2, 3]

def test_mutation_missing_swap_flag_update():
    # detects missing negation or flag update (e.g., swapped not set to True)
    input_list = [5, 1, 4, 2, 8]
    result = bubble_sort(input_list)
    # If swap flag is broken, sorting may be incomplete
    assert result == [1, 2, 4, 5, 8]

def test_mutation_wrong_constant_initial_swap():
    # detects wrong constant (e.g., swapped = False initially)
    input_list = [1, 2]
    result = bubble_sort(input_list)
    # If swapped starts False, loop may not run; already sorted list is fine,
    # but unsorted list would fail. Use unsorted list.
    input_unsorted = [2, 1]
    result_unsorted = bubble_sort(input_unsorted)
    assert result_unsorted == [1, 2]

def test_mutation_boundary_inclusivity():
    # detects boundary inclusivity (e.g., while swapped == True)
    # This mutation would not exit loop early; test with already sorted list.
    input_list = [1, 2, 3]
    result = bubble_sort(input_list)
    # Correct implementation returns same list, infinite loop mutation would not return
    # This test passes if function returns.
    assert result == [1, 2, 3]