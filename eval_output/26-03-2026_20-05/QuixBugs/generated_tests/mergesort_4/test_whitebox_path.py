import pytest
from python_programs.mergesort import mergesort

# path: outer if len(arr)==0 → True → return arr (empty list)
def test_mergesort_empty():
    assert mergesort([]) == []

# path: outer else → middle=0 → recursion bottoms out → merge called with single-element lists
# merge: while loop 0 iterations (one side exhausted immediately), extend with remaining
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# path: outer else → two elements → merge with 1-iteration while loop → left[i] <= right[j] True → extend right remainder
def test_mergesort_two_elements_ascending():
    assert mergesort([1, 2]) == [1, 2]

# path: outer else → two elements → merge with 1-iteration while loop → left[i] <= right[j] False → extend left remainder
def test_mergesort_two_elements_descending():
    assert mergesort([2, 1]) == [1, 2]

# path: outer else → two equal elements → merge → left[i] <= right[j] True (equal case) → extend
def test_mergesort_two_equal_elements():
    assert mergesort([3, 3]) == [3, 3]

# path: outer else → multiple elements → merge with many iterations → mixed True/False branches → left remainder extended
def test_mergesort_multiple_elements_left_remainder():
    # After merge, left side has remaining elements
    assert mergesort([1, 3, 5, 2, 4]) == [1, 2, 3, 4, 5]

# path: outer else → multiple elements → merge with many iterations → right remainder extended
def test_mergesort_multiple_elements_right_remainder():
    # After merge, right side has remaining elements
    assert mergesort([3, 1, 2, 5, 4]) == [1, 2, 3, 4, 5]

# path: outer else → already sorted array → merge always takes left[i] (all True branches) → right remainder
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: outer else → reverse sorted array → merge always takes right[j] (all False branches) → left remainder
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: outer else → array with duplicates → merge with equal comparisons (left[i] <= right[j] True)
def test_mergesort_with_duplicates():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]

# path: outer else → single-element array fed into merge → while loop 0 iterations → extend with entire left or right
def test_mergesort_two_elements_with_extend_left():
    # Result should pick the smaller right element first, then extend left
    assert mergesort([5, 1]) == [1, 5]

# path: outer else → negative numbers → merge with mixed True/False branches
def test_mergesort_negative_numbers():
    assert mergesort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# path: outer else → mixed negative and positive → merge many iterations → mixed branches
def test_mergesort_mixed_negative_positive():
    assert mergesort([-1, 3, -2, 4, 0]) == [-2, -1, 0, 3, 4]

# path: outer else → large array → deep recursion, many merge iterations, both left and right remainders exercised
def test_mergesort_large_array():
    import random
    arr = list(range(20, 0, -1))
    assert mergesort(arr) == list(range(1, 21))