from python_programs.mergesort import mergesort

# len(arr) == 0: True → return empty array
def test_mergesort_empty_array():
    assert mergesort([]) == []

# len(arr) == 0: False (single element, no merge needed)
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# len(arr) == 0: False; left[i] <= right[j]: True (left element is smaller)
def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

# len(arr) == 0: False; left[i] <= right[j]: False (right element is smaller)
def test_mergesort_two_elements_reversed():
    assert mergesort([2, 1]) == [1, 2]

# left[i] <= right[j]: True (equal elements)
def test_mergesort_equal_elements():
    assert mergesort([3, 3, 3]) == [3, 3, 3]

# len(arr) == 0: False; left[i] <= right[j]: both True and False paths exercised
def test_mergesort_multiple_elements():
    assert mergesort([5, 3, 8, 1, 9, 2]) == [1, 2, 3, 5, 8, 9]

# len(arr) == 0: False; left[i] <= right[j]: True repeatedly (already sorted)
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# len(arr) == 0: False; left[i] <= right[j]: False repeatedly (reverse sorted)
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# result.extend(left[i:] or right[j:]) where left[i:] is non-empty (right exhausted first)
def test_mergesort_left_remainder():
    # After merging, left has remaining elements
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# result.extend(left[i:] or right[j:]) where right[j:] is non-empty (left exhausted first)
def test_mergesort_right_remainder():
    # After merging, right has remaining elements
    assert mergesort([3, 1, 2]) == [1, 2, 3]

# len(arr) == 0: False; left[i] <= right[j]: both True and False; duplicates preserved
def test_mergesort_with_duplicates():
    assert mergesort([4, 2, 4, 1, 2]) == [1, 2, 2, 4, 4]

# len(arr) == 0: False; negative numbers mixed with positive
def test_mergesort_negative_numbers():
    assert mergesort([-3, 1, -1, 2, 0]) == [-3, -1, 0, 1, 2]

# len(arr) == 0: False; single comparison needed in while loop (i < len(left) True, j < len(right) True then one becomes False)
def test_mergesort_while_condition_both_true_then_false():
    # Two elements: while runs once, then one index exhausted
    assert mergesort([10, 5]) == [5, 10]

# i < len(left): False before j < len(right): False — left side exhausted first
def test_mergesort_left_exhausted_first():
    assert mergesort([1, 5, 6, 2, 3, 4]) == [1, 2, 3, 4, 5, 6]

# j < len(right): False before i < len(left): False — right side exhausted first
def test_mergesort_right_exhausted_first():
    assert mergesort([4, 5, 6, 1, 2, 3]) == [1, 2, 3, 4, 5, 6]