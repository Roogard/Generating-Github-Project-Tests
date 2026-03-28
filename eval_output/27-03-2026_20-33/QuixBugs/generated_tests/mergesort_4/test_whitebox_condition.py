from python_programs.mergesort import mergesort

# condition: len(arr) == 0: True → return empty array
def test_mergesort_empty_array():
    # len(arr) == 0: True
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# condition: len(arr) == 0: False (single element, no merge needed)
def test_mergesort_single_element():
    # len(arr) == 0: False
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1
    assert sorted(result) == sorted([42])

# condition: len(arr) == 0: False; left[i] <= right[j]: True (left element smaller)
def test_mergesort_two_elements_sorted():
    # len(arr) == 0: False; left[i] <= right[j]: True
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False; left[i] <= right[j]: False (right element smaller)
def test_mergesort_two_elements_reversed():
    # len(arr) == 0: False; left[i] <= right[j]: False
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: left[i] <= right[j]: True (equal elements, covers <=)
def test_mergesort_equal_elements():
    # left[i] <= right[j]: True (equal case)
    arr = [3, 3, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: while i < len(left) and j < len(right): True then False
# exercises the while loop running and terminating; result.extend uses left[i:] remainder
def test_mergesort_left_remainder():
    # while i < len(left): True then exhausts right first; left[i:] is non-empty
    arr = [1, 3, 5, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: while i < len(left) and j < len(right): True then False
# exercises right[j:] remainder
def test_mergesort_right_remainder():
    # while j < len(right): True then exhausts left first; right[j:] is non-empty
    arr = [2, 1, 3, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: i < len(left): False (left exhausted), j < len(right): True
def test_mergesort_left_exhausted_first():
    # i < len(left): False before j < len(right): False
    arr = [1, 4, 5, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: i < len(left): True, j < len(right): False (right exhausted)
def test_mergesort_right_exhausted_first():
    # j < len(right): False before i < len(left): False
    arr = [3, 4, 5, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# General large array test covering multiple recursive splits
def test_mergesort_larger_array():
    # len(arr) == 0: False multiple times; left[i] <= right[j]: both True and False
    arr = [5, 3, 8, 1, 9, 2, 7, 4, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False; left[i] <= right[j]: True and False with duplicates
def test_mergesort_with_duplicates():
    # left[i] <= right[j]: True (equal and less), False (greater)
    arr = [4, 2, 4, 1, 3, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False with negative numbers
def test_mergesort_negative_numbers():
    # len(arr) == 0: False; left[i] <= right[j]: both True and False
    arr = [-3, -1, -4, -1, -5, -9, -2, -6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: left[i] <= right[j]: True and False with mixed positive/negative
def test_mergesort_mixed_positive_negative():
    # left[i] <= right[j]: True and False
    arr = [-2, 3, -1, 0, 4, -3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: result.extend uses left[i:] or right[j:] — left[i:] non-empty (truthy)
def test_mergesort_extend_uses_left_remainder():
    # After while loop, left[i:] is non-empty → left[i:] or right[j:] evaluates left[i:]
    arr = [1, 2, 5, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: result.extend uses left[i:] or right[j:] — left[i:] empty, right[j:] non-empty
def test_mergesort_extend_uses_right_remainder():
    # After while loop, left[i:] is empty → left[i:] or right[j:] evaluates right[j:]
    arr = [3, 1, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)