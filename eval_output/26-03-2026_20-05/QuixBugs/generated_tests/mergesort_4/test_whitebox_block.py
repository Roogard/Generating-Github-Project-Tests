from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch (empty array return)
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: else branch, merge with single element arrays, while loop not entered,
#         result.extend with left[i:] or right[j:]
def test_mergesort_single_element():
    assert mergesort([1]) == [1]

# covers: else branch, middle split, merge while loop,
#         left[i] <= right[j] branch (left element taken), extend with right[j:]
def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: else branch, merge while loop,
#         else branch in merge (right element taken), extend with left[i:]
def test_mergesort_two_elements_reversed():
    assert mergesort([2, 1]) == [1, 2]

# covers: all blocks including recursive splits, both branches in merge comparison
def test_mergesort_multiple_elements():
    assert mergesort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# covers: already sorted array - left[i] <= right[j] always taken
def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: reverse sorted array - else branch in merge always taken
def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: duplicate elements, left[i] <= right[j] with equality
def test_mergesort_duplicates():
    assert mergesort([3, 3, 3, 1, 1]) == [1, 1, 3, 3, 3]

# covers: extend left[i:] when left has remaining elements after while loop
def test_mergesort_left_remainder():
    assert mergesort([1, 2, 5, 3, 4]) == [1, 2, 3, 4, 5]

# covers: extend right[j:] when right has remaining elements after while loop
def test_mergesort_right_remainder():
    assert mergesort([4, 5, 1, 2, 3]) == [1, 2, 3, 4, 5]

# covers: negative numbers
def test_mergesort_negative_numbers():
    assert mergesort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# covers: mixed negative and positive
def test_mergesort_mixed():
    assert mergesort([-1, 3, -2, 0, 2]) == [-2, -1, 0, 2, 3]