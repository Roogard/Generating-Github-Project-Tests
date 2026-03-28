from python_programs.mergesort import mergesort

# covers: outer else block, merge with left[i] <= right[j] path, result.extend with remaining left
def test_mergesort_basic_sorted():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: base case len(arr) == 0
def test_mergesort_empty():
    arr = []
    result = mergesort(arr)
    assert result == []
    assert len(result) == 0

# covers: single element (recursive base via len==0 not triggered, but reaches merge with empty halves)
def test_mergesort_single_element():
    arr = [42]
    result = mergesort(arr)
    assert result == [42]
    assert len(result) == 1

# covers: else branch in merge (right[j] < left[i]), result.extend with remaining right
def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: duplicate elements, left[i] <= right[j] equality branch
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: already sorted input, extend with remaining left elements
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: two elements where left > right (hits else in merge, extend with remaining left)
def test_mergesort_two_elements_reversed():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# covers: two elements already sorted (hits left[i] <= right[j] in merge, extend remaining right)
def test_mergesort_two_elements_sorted():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# covers: larger array with mixed values ensuring all merge branches hit
def test_mergesort_larger_array():
    arr = [10, -1, 0, 5, 3, 8, -3, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: all same elements (equality in merge)
def test_mergesort_all_same():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == [7, 7, 7, 7]
    assert len(result) == 4

# covers: result.extend with remaining right (right exhausted before left case)
def test_mergesort_extend_remaining_right():
    arr = [1, 3, 5, 2, 4, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)