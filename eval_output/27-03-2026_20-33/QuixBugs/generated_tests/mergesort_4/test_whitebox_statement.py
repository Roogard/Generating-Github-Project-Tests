from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch, returns arr
def test_mergesort_empty():
    result = mergesort([])
    assert result == []

# covers: else branch, middle, left/right recursive calls, merge called
# merge: result=[], i=0, j=0, while loop (left[i]<=right[j] true), append left[i], i+=1
# result.extend, return result
# single element (base case via empty, then merge of single elements)
def test_mergesort_single():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# covers: else branch with multi-element array, merge with left[i] <= right[j] path
# and result.extend(left[i:] or right[j:]) when left has remainder
def test_mergesort_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: else branch in merge (left[i] > right[j]), append right[j], j+=1
# also covers result.extend with right[j:] remainder
def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: merge with equal elements (left[i] <= right[j] both branches),
# duplicate values, result.extend path
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: result.extend when right[j:] is non-empty (right has remainder)
def test_mergesort_right_remainder():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: two-element array, both merge branches
def test_mergesort_two_elements():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2
    assert sorted(result) == sorted(arr)

# covers: larger random-like array for full statement coverage confidence
def test_mergesort_larger():
    arr = [9, 3, 7, 1, 8, 2, 6, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)