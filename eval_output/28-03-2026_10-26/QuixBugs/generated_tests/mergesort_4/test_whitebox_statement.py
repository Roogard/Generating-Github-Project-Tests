from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch (early return)
def test_mergesort_empty():
    result = mergesort([])
    assert result == []

# covers: else branch, middle computation, recursive calls, merge with both branches of if/else inside while
# left[i] <= right[j] path (left element smaller) and right[j] < left[i] path (right element smaller)
def test_mergesort_multiple_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: single element array - triggers else branch, merge called with single-element lists
def test_mergesort_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# covers: merge where left has remaining elements after while loop (result.extend(left[i:] or right[j:]))
def test_mergesort_left_remainder():
    arr = [1, 2, 10, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: merge where right has remaining elements after while loop
def test_mergesort_right_remainder():
    arr = [5, 1, 2, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: duplicate values, ensuring stable merge handles equals (left[i] <= right[j] path)
def test_mergesort_duplicates():
    arr = [3, 3, 3, 1, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: already sorted array
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: reverse sorted array, ensuring right element is always smaller (else branch in merge)
def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: two element array triggering merge with single element left and right
def test_mergesort_two_elements():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2