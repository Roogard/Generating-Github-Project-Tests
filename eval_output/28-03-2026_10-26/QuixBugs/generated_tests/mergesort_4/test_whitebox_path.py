import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → return arr (base case, empty)
def test_mergesort_empty():
    result = mergesort([])
    assert result == []

# path: len(arr) != 0 → split → recursive base → merge with while 0 iterations (single element)
def test_mergesort_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# path: len(arr) != 0 → split → merge with while loop, left[i] <= right[j] branch (ascending pair)
def test_mergesort_two_elements_ascending():
    inp = [1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → split → merge with while loop, else branch (right[j] smaller, descending pair)
def test_mergesort_two_elements_descending():
    inp = [2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → split → merge with while loop, equal elements (left[i] <= right[j] via equality)
def test_mergesort_two_equal_elements():
    inp = [5, 5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → split → merge with while loop many iterations, left remainder extended
def test_mergesort_left_remainder():
    # After merge loop, left has remaining elements to extend
    inp = [1, 2, 3, 10]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → split → merge with while loop many iterations, right remainder extended
def test_mergesort_right_remainder():
    # After merge loop, right has remaining elements to extend
    inp = [10, 1, 2, 3]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → multiple levels of recursion → merge many iterations with mixed branches
def test_mergesort_multiple_elements_mixed():
    inp = [5, 3, 8, 1, 9, 2, 7, 4, 6]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → contains duplicates → merge preserves all duplicates
def test_mergesort_with_duplicates():
    inp = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → already sorted → merge while loop only takes left branch
def test_mergesort_already_sorted():
    inp = [1, 2, 3, 4, 5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → reverse sorted → merge while loop only takes right branch heavily
def test_mergesort_reverse_sorted():
    inp = [5, 4, 3, 2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → negative numbers → merge handles negatives correctly
def test_mergesort_negative_numbers():
    inp = [-3, -1, -7, -2, -5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → mixed negative and positive → merge handles mixed correctly
def test_mergesort_mixed_sign_numbers():
    inp = [3, -2, 0, -5, 4, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

# path: len(arr) != 0 → three elements (odd length, uneven split)
def test_mergesort_three_elements():
    inp = [3, 1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)