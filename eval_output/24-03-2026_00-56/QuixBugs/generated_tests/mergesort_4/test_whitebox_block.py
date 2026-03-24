from correct_python_programs.mergesort import mergesort

# Block analysis for mergesort:
# Block 1: function entry, definition of merge, if len(arr) <= 1
# Block 2: return arr (base case)
# Block 3: else branch: middle = len(arr) // 2, left = mergesort(arr[:middle]), right = mergesort(arr[middle:]), return merge(left, right)
# 
# Block analysis for inner merge function:
# Block 4: merge entry: result = [], i = 0, j = 0, while condition check
# Block 5: while body: if left[i] <= right[j]
# Block 6: if-true: result.append(left[i]), i += 1
# Block 7: if-false: result.append(right[j]), j += 1
# Block 8: after while: result.extend(left[i:] or right[j:]), return result

# covers: block 1, block 2 (base case)
def test_empty_array():
    assert mergesort([]) == []

# covers: block 1, block 2 (base case)
def test_single_element():
    assert mergesort([5]) == [5]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures the while loop executes both if and else branches
def test_two_elements():
    assert mergesort([2, 1]) == [1, 2]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures the while loop can exit without exhausting both lists
# and triggers the extend with left[i:] (since left has remaining elements)
def test_merge_with_left_remainder():
    assert mergesort([1, 3, 5, 2, 4]) == [1, 2, 3, 4, 5]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures the while loop can exit without exhausting both lists
# and triggers the extend with right[j:] (since right has remaining elements)
def test_merge_with_right_remainder():
    assert mergesort([2, 4, 1, 3, 5]) == [1, 2, 3, 4, 5]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures full recursion and merge with all blocks executed
def test_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures full recursion and merge with all blocks executed
def test_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 1, block 3, block 4, block 5, block 6, block 7, block 8
# This test ensures duplicate elements are handled
def test_duplicate_elements():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]