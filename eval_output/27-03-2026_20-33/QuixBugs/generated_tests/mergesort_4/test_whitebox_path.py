import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → return arr (empty list)
def test_mergesort_empty():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# path: len(arr) != 0 → split → both halves recurse to empty/single → merge with while loop 0 iterations (one side empty after split)
# single element: middle=0, left=mergesort([])=[], right=mergesort([x])... actually middle=0 means left=[], right=[x]
# merge([], [x]): while loop 0 iters, extend with right[0:] = [x]
def test_mergesort_single():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# path: len(arr) != 0 → split → merge with while loop 1 iteration, left[i] <= right[j] branch True
def test_mergesort_two_ascending():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop 1 iteration, left[i] <= right[j] branch False (else branch)
def test_mergesort_two_descending():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop many iterations, mixed True/False branches → extend left remainder
def test_mergesort_multiple_left_remainder():
    arr = [1, 3, 5, 2, 4]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop many iterations, mixed True/False branches → extend right remainder
def test_mergesort_multiple_right_remainder():
    arr = [3, 4, 5, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: many iterations → equal elements (left[i] <= right[j] True for equal values)
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: many iterations → all equal elements
def test_mergesort_all_equal():
    arr = [5, 5, 5, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: already sorted → many iterations mostly True branch
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: reverse sorted → many iterations mostly False (else) branch
def test_mergesort_reverse_sorted():
    arr = [6, 5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: negative numbers → many iterations mixed branches
def test_mergesort_negative_numbers():
    arr = [-3, -1, -4, -1, -5, -9, -2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: mixed positive and negative → many iterations mixed branches
def test_mergesort_mixed_positive_negative():
    arr = [3, -1, 4, -1, 5, -9, 2, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: two elements equal → while loop 1 iteration, left[i] <= right[j] True (equal case)
def test_mergesort_two_equal():
    arr = [7, 7]
    result = mergesort(arr)
    assert result == [7, 7]
    assert len(result) == 2

# path: extend uses left[i:] (non-empty left remainder after while exits)
def test_mergesort_left_tail_extends():
    # After merge, left has remaining elements: e.g., [1,3,5] merged with [2]
    arr = [5, 3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: extend uses right[j:] (non-empty right remainder after while exits)
def test_mergesort_right_tail_extends():
    # After merge, right has remaining elements: e.g., [1] merged with [3,4,5]
    arr = [4, 5, 1, 2, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)