from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch -> return arr
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: else branch (middle, left, right, merge call), single element recursion
# merge: while loop not entered, result.extend(left[i:] or right[j:])
def test_mergesort_single():
    assert mergesort([42]) == [42]

# covers: else branch, merge with left[i] <= right[j] path (result.append(left[i]), i+=1)
# and result.extend with remaining right elements
def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: else branch, merge with left[i] > right[j] path (result.append(right[j]), j+=1)
# and result.extend with remaining left elements
def test_mergesort_two_elements_reverse():
    assert mergesort([2, 1]) == [1, 2]

# covers: full merge path with multiple comparisons, both branches in while loop
def test_mergesort_multiple_elements():
    assert mergesort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# covers: already sorted list (left[i] <= right[j] path dominates)
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: reverse sorted list (right[j] < left[i] path dominates)
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: result.extend with left[i:] remaining (right exhausted first)
def test_mergesort_left_remainder():
    assert mergesort([1, 3, 5, 2]) == [1, 2, 3, 5]

# covers: result.extend with right[j:] remaining (left exhausted first)
def test_mergesort_right_remainder():
    assert mergesort([4, 1, 2, 3]) == [1, 2, 3, 4]

# covers: duplicate elements
def test_mergesort_duplicates():
    assert mergesort([3, 3, 3]) == [3, 3, 3]