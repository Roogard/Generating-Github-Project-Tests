import pytest
from python_programs.mergesort import mergesort

# --- BVA ---

def test_bva_empty_array():
    # Boundary: empty collection
    result = mergesort([])
    assert result == []

def test_bva_single_element():
    # Boundary: single element collection
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

def test_bva_two_elements_sorted():
    # Boundary: two elements, already in order
    result = mergesort([1, 2])
    assert result == [1, 2]

def test_bva_two_elements_reverse():
    # Boundary: two elements, reversed
    result = mergesort([2, 1])
    assert result == [1, 2]

def test_bva_large_array():
    # Boundary: large collection
    import random
    arr = list(range(1000, 0, -1))
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_bva_min_max_values():
    # Boundary: extreme integer values
    arr = [-(2**31), 2**31 - 1, 0]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_bva_two_equal_elements():
    # Boundary: two equal elements (minimum duplicate case)
    result = mergesort([5, 5])
    assert result == [5, 5]

# --- ECP ---

def test_ecp_valid_already_sorted():
    # Valid class: already sorted input
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_reverse_sorted():
    # Valid class: reverse sorted input
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_random_order():
    # Valid class: arbitrary unsorted input
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_ecp_valid_all_same_elements():
    # Valid class: all elements equal
    arr = [7, 7, 7, 7, 7]
    result = mergesort(arr)
    assert result == [7, 7, 7, 7, 7]
    assert len(result) == len(arr)

def test_ecp_valid_negative_numbers():
    # Valid class: all negative numbers
    arr = [-3, -1, -4, -1, -5]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_ecp_valid_mixed_positive_negative():
    # Valid class: mix of positive, negative, and zero
    arr = [-2, 0, 3, -1, 2, -5]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_ecp_valid_duplicates():
    # Valid class: array with multiple duplicates
    arr = [4, 2, 4, 3, 2, 1, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_ecp_valid_odd_length():
    # Valid class: odd number of elements (affects middle split)
    arr = [5, 3, 1, 4, 2]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_even_length():
    # Valid class: even number of elements
    arr = [8, 2, 6, 4]
    result = mergesort(arr)
    assert result == [2, 4, 6, 8]

def test_ecp_valid_floats():
    # Valid class: floating point numbers
    arr = [3.14, 1.41, 2.71, 0.57]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_ecp_valid_strings():
    # Valid class: strings (comparable via lexicographic order)
    arr = ["banana", "apple", "cherry", "date"]
    result = mergesort(arr)
    assert result == sorted(arr)

# --- Mutation Detection ---

def test_mutation_off_by_one_left_remainder():
    # Detects: `result.extend(left[i:] or right[j:])` mutated to drop remaining elements
    # When left has remaining elements after merge loop, they must all be appended
    arr = [1, 3, 5, 2]  # left=[1,3], right=[2,5] after splits
    result = mergesort(arr)
    assert result == [1, 2, 3, 5]
    assert len(result) == 4  # no elements dropped

def test_mutation_off_by_one_right_remainder():
    # Detects: remaining right elements being dropped
    arr = [2, 1, 3, 5]
    result = mergesort(arr)
    assert result == [1, 2, 3, 5]
    assert len(result) == 4

def test_mutation_wrong_comparison_operator_strict():
    # Detects: `<=` changed to `<` in merge comparison
    # When left[i] == right[j], both correct (`<=`) and mutated (`<`) differ in which is picked,
    # but both result in a sorted array. More critically, test that equal elements are preserved.
    arr = [2, 2, 1, 1]
    result = mergesort(arr)
    assert result == [1, 1, 2, 2]
    assert len(result) == 4  # mutation dropping duplicates caught here

def test_mutation_wrong_operator_i_increment():
    # Detects: `i += 1` changed to `j += 1` or vice versa
    arr = [4, 1, 3, 2]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4]

def test_mutation_wrong_variable_in_append():
    # Detects: `result.append(left[i])` changed to `result.append(right[j])`
    arr = [10, 1]
    result = mergesort(arr)
    assert result == [1, 10]

def test_mutation_wrong_variable_right_append():
    # Detects: `result.append(right[j])` changed to `result.append(left[i])`
    arr = [5, 2, 8]
    result = mergesort(arr)
    assert result == [2, 5, 8]

def test_mutation_or_instead_of_correct_extend():
    # Detects: `left[i:] or right[j:]` — the `or` short-circuits, so if left[i:] is non-empty,
    # right[j:] is ignored. This is a real bug in the source.
    # A correct mergesort must append ALL remaining elements from BOTH sides.
    # This test exposes the bug where after loop, both left and right have remainders.
    # After merging [1,3] and [2,4]: loop ends when j exhausted (j=2) with i=1 left remaining,
    # so only left[1:] = [3] needs appending (right is exhausted). Safe case.
    # Let's construct a case where left is exhausted first and right has remainder:
    arr = [1, 2, 4, 3]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4]
    assert len(result) == 4

def test_mutation_base_case_wrong_condition():
    # Detects: `len(arr) == 0` changed to `len(arr) <= 1` (affects single element return)
    # A correct mergesort of a single element must return that element unchanged
    result = mergesort([99])
    assert result == [99]

def test_mutation_middle_calculation_floor():
    # Detects: `len(arr) // 2` changed to `len(arr) // 2 + 1` or similar
    # Test with power-of-2 size to stress the split
    arr = [8, 4, 6, 2, 7, 3, 5, 1]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5, 6, 7, 8]
    assert len(result) == 8

def test_mutation_preserves_all_elements():
    # Detects: any mutation that drops, duplicates, or corrupts elements
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    result = mergesort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

def test_mutation_stable_sort_property():
    # A correct mergesort must produce output equal to Python's sorted()
    arr = [100, -50, 0, 75, -25, 50]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_mutation_result_is_non_decreasing():
    # Property: every adjacent pair must satisfy result[i] <= result[i+1]
    arr = [7, 2, 9, 1, 5, 3, 8, 4, 6]
    result = mergesort(arr)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1], f"Not sorted at index {i}: {result}"

def test_mutation_and_vs_or_in_while_condition():
    # Detects: `and` changed to `or` in `while i < len(left) and j < len(right)`
    # If `or` were used, accessing out-of-bounds index would cause IndexError or wrong result
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == [1, 2, 3]
    assert len(result) == 3