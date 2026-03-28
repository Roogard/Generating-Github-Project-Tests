from python_programs.mergesort import mergesort

# Block map:
# Block 1: merge - result=[], i=0, j=0
# Block 2: while loop condition (i < len(left) and j < len(right))
# Block 3: if left[i] <= right[j] -> append left[i], i += 1
# Block 4: else -> append right[j], j += 1
# Block 5: result.extend(left[i:] or right[j:]), return result
# Block 6: outer if len(arr) == 0 -> return arr
# Block 7: outer else -> middle, left, right, return merge(left, right)

# covers: block 6 (empty array)
def test_mergesort_empty():
    result = mergesort([])
    assert result == []

# covers: block 7, block 1, block 2 (loop skipped since single elem),
# block 5, and recursion bottoms out to block 6
def test_mergesort_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# covers: block 7, block 1, block 2, block 3 (left[i] <= right[j]),
# block 5 (left remainder extended)
def test_mergesort_two_elements_sorted():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 4 (else branch: right[j] < left[i]),
# block 5 (right remainder extended)
def test_mergesort_two_elements_reversed():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all blocks including block 3, block 4, block 5 with both
# left and right remainders exercised across recursive calls
def test_mergesort_multiple_elements():
    arr = [5, 3, 8, 1, 9, 2, 7, 4, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 5 with right remainder (left exhausted first)
def test_mergesort_left_exhausted_first():
    arr = [1, 5, 6, 2, 3, 4]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 5 with left remainder (right exhausted first)
def test_mergesort_right_exhausted_first():
    arr = [3, 4, 5, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 3 (equal elements, left[i] <= right[j] handles equality)
def test_mergesort_with_duplicates():
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: already sorted array — exercises block 3 heavily
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5, 6, 7, 8]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: reverse sorted array — exercises block 4 heavily
def test_mergesort_reverse_sorted():
    arr = [8, 7, 6, 5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: negative numbers and mixed signs
def test_mergesort_negative_numbers():
    arr = [-3, -1, -7, 0, 5, -2, 4]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all same elements (block 3: <= always true)
def test_mergesort_all_same():
    arr = [7, 7, 7, 7, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)