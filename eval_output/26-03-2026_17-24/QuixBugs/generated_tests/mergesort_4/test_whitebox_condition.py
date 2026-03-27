from python_programs.mergesort import mergesort

# len(arr) == 0: True → return empty array
def test_mergesort_empty_array():
    assert mergesort([]) == []

# len(arr) == 0: False (single element, no merge needed)
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# len(arr) == 0: False (two elements)
# while: i < len(left): True, j < len(right): True
# left[i] <= right[j]: True (left smaller)
def test_mergesort_two_elements_already_sorted():
    assert mergesort([1, 2]) == [1, 2]

# len(arr) == 0: False (two elements)
# while: i < len(left): True, j < len(right): True
# left[i] <= right[j]: False (right smaller)
def test_mergesort_two_elements_reverse_sorted():
    assert mergesort([2, 1]) == [1, 2]

# len(arr) == 0: False (multiple elements)
# left[i] <= right[j]: True and False exercised within merge
# while exits with remaining left elements (left[i:] is non-empty, right[j:] is empty)
# result.extend(left[i:] or right[j:]) → left[i:] truthy
def test_mergesort_remaining_left_elements():
    # After merging, left side has remaining elements
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# result.extend(left[i:] or right[j:]) → left[i:] is empty (falsy), right[j:] truthy
def test_mergesort_remaining_right_elements():
    assert mergesort([3, 1, 2, 4]) == [1, 2, 3, 4]

# len(arr) == 0: False, multiple recursive calls, all conditions exercised
# left[i] <= right[j]: True (equal elements)
def test_mergesort_duplicate_elements():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]

# len(arr) == 0: False, larger array with mixed order
def test_mergesort_general_case():
    assert mergesort([5, 3, 8, 1, 9, 2, 7, 4, 6]) == [1, 2, 3, 4, 5, 6, 7, 8, 9]

# left[i] <= right[j]: True (equal values throughout)
def test_mergesort_all_same_elements():
    assert mergesort([4, 4, 4, 4]) == [4, 4, 4, 4]

# len(arr) == 0: False, already sorted input
# left[i] <= right[j]: True for every comparison in merge
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# len(arr) == 0: False, reverse sorted input
# left[i] <= right[j]: False for every comparison in merge
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# while i < len(left): False immediately (left is empty after split of size 1 vs rest)
# while j < len(right): condition never reached when left exhausted first
def test_mergesort_two_elements_equal():
    assert mergesort([7, 7]) == [7, 7]

# left[i] <= right[j]: True and False, with negative numbers
def test_mergesort_negative_numbers():
    assert mergesort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# Mixed positive and negative
def test_mergesort_mixed_positive_negative():
    assert mergesort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]