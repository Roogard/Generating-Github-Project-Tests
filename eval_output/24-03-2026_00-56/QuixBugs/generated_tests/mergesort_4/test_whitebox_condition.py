from correct_python_programs.mergesort import mergesort

# condition: len(arr) <= 1: True
def test_mergesort_empty():
    # len(arr) <= 1: True
    assert mergesort([]) == []

# condition: len(arr) <= 1: True
def test_mergesort_single():
    # len(arr) <= 1: True
    assert mergesort([5]) == [5]

# condition: len(arr) <= 1: False
def test_mergesort_multiple():
    # len(arr) <= 1: False
    assert mergesort([3, 1, 2]) == [1, 2, 3]

# condition in merge: i < len(left): True, j < len(right): True, left[i] <= right[j]: True
def test_merge_left_smaller():
    # i < len(left): True, j < len(right): True, left[i] <= right[j]: True
    left = [1, 3]
    right = [2, 4]
    # manually test merge by calling mergesort on a list that will produce these subarrays
    assert mergesort([3, 1, 4, 2]) == [1, 2, 3, 4]

# condition in merge: i < len(left): True, j < len(right): True, left[i] <= right[j]: False
def test_merge_right_smaller():
    # i < len(left): True, j < len(right): True, left[i] <= right[j]: False
    left = [2, 4]
    right = [1, 3]
    assert mergesort([2, 4, 1, 3]) == [1, 2, 3, 4]

# condition in merge: i < len(left): True, j < len(right): False
def test_merge_left_remaining():
    # i < len(left): True, j < len(right): False
    left = [1, 2, 3]
    right = [4, 5]
    assert mergesort([3, 1, 2, 4, 5]) == [1, 2, 3, 4, 5]

# condition in merge: i < len(left): False, j < len(right): True
def test_merge_right_remaining():
    # i < len(left): False, j < len(right): True
    left = [1, 2]
    right = [3, 4, 5]
    assert mergesort([1, 2, 5, 3, 4]) == [1, 2, 3, 4, 5]

# condition in merge: i < len(left): False, j < len(right): False (both empty after loop)
def test_merge_exact_equal_lengths():
    # i < len(left): False, j < len(right): False
    left = [1, 3]
    right = [2, 4]
    # This case is covered by test_merge_left_smaller, but we ensure both become False
    assert mergesort([1, 3, 2, 4]) == [1, 2, 3, 4]