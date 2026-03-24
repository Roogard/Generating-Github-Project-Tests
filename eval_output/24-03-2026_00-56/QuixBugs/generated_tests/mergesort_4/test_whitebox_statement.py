from correct_python_programs.mergesort import mergesort

# covers: len(arr) <= 1 (True), return arr
def test_mergesort_empty():
    assert mergesort([]) == []

# covers: len(arr) <= 1 (True), return arr
def test_mergesort_single():
    assert mergesort([5]) == [5]

# covers: len(arr) <= 1 (False), middle = len(arr) // 2, left = mergesort(arr[:middle]), right = mergesort(arr[middle:]), return merge(left, right)
# inside merge: result = [], i = 0, j = 0, while i < len(left) and j < len(right): (True), left[i] <= right[j] (True), result.append(left[i]), i += 1, while i < len(left) and j < len(right): (False), result.extend(left[i:] or right[j:]), return result
def test_mergesort_two_sorted():
    assert mergesort([1, 2]) == [1, 2]

# covers: while i < len(left) and j < len(right): (True), left[i] <= right[j] (False), result.append(right[j]), j += 1
def test_mergesort_two_reversed():
    assert mergesort([2, 1]) == [1, 2]

# covers: while i < len(left) and j < len(right): (True) multiple times, left[i] <= right[j] (True and False alternating), and eventually while condition becomes False, then result.extend(left[i:] or right[j:]) with left[i:] non-empty
def test_mergesort_longer_left_remaining():
    assert mergesort([1, 3, 5, 2, 4]) == [1, 2, 3, 4, 5]

# covers: result.extend(left[i:] or right[j:]) with right[j:] non-empty (when left is exhausted first)
def test_mergesort_longer_right_remaining():
    assert mergesort([2, 4, 1, 3, 5]) == [1, 2, 3, 4, 5]