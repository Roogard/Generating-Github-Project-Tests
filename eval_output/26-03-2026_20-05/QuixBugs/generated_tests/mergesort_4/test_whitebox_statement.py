from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch -> return arr
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: else branch, middle calculation, recursive calls, merge called
# merge: while loop not entered (single element lists), result.extend with left[i:] or right[j:]
# left[i] <= right[j] True branch, append left[i], i += 1
def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: else branch in merge (left[i] > right[j]), append right[j], j += 1
def test_mergesort_two_elements_reverse():
    assert mergesort([2, 1]) == [1, 2]

# covers: all branches including remaining right[j:] extension after while loop
def test_mergesort_multiple_elements():
    assert mergesort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# covers: already sorted array
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: reverse sorted array (maximizes right-element picks)
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: single element (len(arr) != 0, middle=0, left=[], right=[single])
def test_mergesort_single_element():
    assert mergesort([42]) == [42]

# covers: result.extend with remaining left elements (left[i:] is non-empty)
def test_mergesort_remaining_left():
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# covers: duplicate elements
def test_mergesort_duplicates():
    assert mergesort([3, 3, 3]) == [3, 3, 3]