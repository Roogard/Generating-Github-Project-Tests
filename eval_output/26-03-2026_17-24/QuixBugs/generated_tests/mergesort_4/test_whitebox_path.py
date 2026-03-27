import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → return arr (empty list)
def test_mergesort_empty():
    assert mergesort([]) == []

# path: len(arr) != 0 → split → recursive calls each hit base case → merge with 0 while iterations → extend left remainder
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# path: len(arr) != 0 → split → merge: while 1 iteration → left[i] <= right[j] True → extend right remainder
def test_mergesort_two_elements_ascending():
    assert mergesort([1, 2]) == [1, 2]

# path: len(arr) != 0 → split → merge: while 1 iteration → left[i] <= right[j] False → extend left remainder
def test_mergesort_two_elements_descending():
    assert mergesort([2, 1]) == [1, 2]

# path: len(arr) != 0 → split → merge: while 1 iteration → left[i] <= right[j] True (equal) → extend remainder
def test_mergesort_two_equal_elements():
    assert mergesort([5, 5]) == [5, 5]

# path: len(arr) != 0 → split → merge: multiple while iterations → mixed True/False branches → extend left remainder
def test_mergesort_multiple_elements_mixed():
    assert mergesort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# path: len(arr) != 0 → split → merge: multiple iterations all left[i] <= right[j] True → extend right remainder
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: len(arr) != 0 → split → merge: multiple iterations all left[i] <= right[j] False → extend left remainder
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: len(arr) != 0 → split → merge: while exhausts right first → extend left remainder (or branch: left[i:] non-empty)
def test_mergesort_left_remainder():
    # after merge, left side has remaining elements
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# path: len(arr) != 0 → split → merge: while exhausts left first → extend right remainder (or branch: right[j:] non-empty)
def test_mergesort_right_remainder():
    # after merge, right side has remaining elements
    assert mergesort([3, 1, 2]) == [1, 2, 3]

# path: len(arr) != 0 → many recursive levels → merge multiple times with many iterations
def test_mergesort_large_input():
    import random
    arr = list(range(50, 0, -1))
    assert mergesort(arr) == list(range(1, 51))

# path: len(arr) != 0 → single element list with negative numbers
def test_mergesort_negative_numbers():
    assert mergesort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

# path: len(arr) != 0 → mixed positive and negative numbers
def test_mergesort_mixed_sign_numbers():
    assert mergesort([-2, 3, -1, 0, 2]) == [-2, -1, 0, 2, 3]