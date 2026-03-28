from python_programs.mergesort import mergesort

# len(arr) == 0: True → returns empty array
def test_mergesort_empty():
    arr = []
    result = mergesort(arr)
    # A correct mergesort of an empty list should return an empty list
    assert result == []
    assert len(result) == 0

# len(arr) == 0: False (single element) → enters else branch
def test_mergesort_single_element():
    arr = [42]
    result = mergesort(arr)
    # A correct mergesort of a single element should return that same element
    assert result == [42]
    assert len(result) == len(arr)
    assert result == sorted(arr)

# len(arr) == 0: False (two elements, already sorted)
# left[i] <= right[j]: True → left element appended first
def test_mergesort_two_elements_sorted():
    arr = [1, 2]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# len(arr) == 0: False (two elements, reverse sorted)
# left[i] <= right[j]: False → right element appended first
def test_mergesort_two_elements_reversed():
    arr = [2, 1]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# len(arr) == 0: False (multiple elements)
# left[i] <= right[j]: True in some iterations, False in others
def test_mergesort_multiple_elements_mixed():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# left[i] <= right[j]: True (equal elements, tests <= vs <)
def test_mergesort_with_duplicates():
    arr = [5, 3, 5, 3, 5]
    result = mergesort(arr)
    # A correct mergesort must preserve all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert result.count(5) == arr.count(5)
    assert result.count(3) == arr.count(3)

# Tests that result.extend uses left[i:] when left has remaining elements
# (i < len(left) loop exits because j >= len(right), so right[j:] is empty)
def test_mergesort_left_remainder():
    arr = [1, 3, 5, 2]
    result = mergesort(arr)
    # A correct mergesort should return all elements sorted
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Tests that result.extend uses right[j:] when right has remaining elements
# (i < len(left) loop exits because i >= len(left), so left[i:] is empty)
def test_mergesort_right_remainder():
    arr = [4, 1, 2, 3]
    result = mergesort(arr)
    # A correct mergesort should return all elements sorted
    assert result == sorted(arr)
    assert len(result) == len(arr)

# len(arr) == 0: False; larger array exercising all sub-conditions
def test_mergesort_larger_array():
    arr = [10, -3, 0, 7, 5, -1, 8, 2, 4, 6]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# All negative numbers
def test_mergesort_all_negative():
    arr = [-5, -1, -3, -4, -2]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Already sorted array: left[i] <= right[j] stays True throughout merge
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5, 6]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Reverse sorted array: left[i] <= right[j] stays False throughout merge
def test_mergesort_reverse_sorted():
    arr = [6, 5, 4, 3, 2, 1]
    result = mergesort(arr)
    # A correct mergesort should return elements in ascending order
    assert result == sorted(arr)
    assert len(result) == len(arr)