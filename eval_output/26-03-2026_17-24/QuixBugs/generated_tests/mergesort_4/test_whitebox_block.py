from python_programs.mergesort import mergesort

# covers: outer block - len(arr) == 0, return arr
def test_empty_array():
    assert mergesort([]) == []

# covers: outer else block (len > 0), merge called with single element arrays
# merge: while loop not entered (one side empty after split), extend with remaining
def test_single_element():
    assert mergesort([42]) == [42]

# covers: outer else block, merge with left[i] <= right[j] branch (left taken first)
def test_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: outer else block, merge with else branch (right[j] < left[i])
def test_two_elements_reverse():
    assert mergesort([2, 1]) == [1, 2]

# covers: all merge branches - left taken, right taken, extend with left remainder
def test_multiple_elements_left_remainder():
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# covers: all merge branches - extend with right remainder
def test_multiple_elements_right_remainder():
    assert mergesort([3, 1, 2, 4]) == [1, 2, 3, 4]

# covers: equal elements (left[i] <= right[j] with equality)
def test_duplicate_elements():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]

# covers: larger array exercising all blocks repeatedly through recursion
def test_larger_array():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: already sorted array
def test_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: single element repeated (all equal)
def test_all_equal():
    assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]

# covers: two elements equal
def test_two_equal_elements():
    assert mergesort([4, 4]) == [4, 4]

# covers: extend with right[j:] when left is exhausted first
def test_right_remainder():
    assert mergesort([4, 5, 1, 2, 3]) == [1, 2, 3, 4, 5]