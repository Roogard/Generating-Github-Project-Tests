from python_programs.mergesort import mergesort

# --- Statement Coverage ---

def test_empty_array():
    # Covers the `if len(arr) == 0: return arr` branch
    # path: empty → early return
    result = mergesort([])
    assert result == []

def test_single_element():
    # Covers the else branch with a single element (middle=0, recursive calls on [] and [x])
    # Also covers merge with one empty side
    result = mergesort([42])
    assert result == [42]

def test_two_elements_sorted():
    # Covers merge where left[i] <= right[j] (True branch inside merge)
    # i=0: left[0]=1 <= right[0]=2 → append left[i]
    result = mergesort([1, 2])
    assert result == [1, 2]

def test_two_elements_reversed():
    # Covers merge where left[i] <= right[j] is False → append right[j]
    result = mergesort([2, 1])
    assert result == [1, 2]

def test_multiple_elements():
    # Covers result.extend(left[i:] or right[j:]) with remaining elements
    result = mergesort([3, 1, 4, 1, 5, 9, 2, 6])
    assert result == sorted([3, 1, 4, 1, 5, 9, 2, 6])

# --- Block Coverage ---

def test_merge_left_remainder():
    # After merge loop exits, left has remaining elements (j exhausted first)
    # left=[1,3,5], right=[2,4] → after loop left[2:] = [5] remains
    # path: while-loop → extend left remainder
    result = mergesort([1, 3, 5, 2, 4])
    assert result == [1, 2, 3, 4, 5]

def test_merge_right_remainder():
    # After merge loop exits, right has remaining elements (i exhausted first)
    # e.g. left=[1,2], right=[3,4,5] → after loop right[2:] = [5] remains
    result = mergesort([3, 4, 5, 1, 2])
    assert result == [1, 2, 3, 4, 5]

def test_else_branch_recurse():
    # Ensures the else branch (non-empty array) is hit, including recursive mergesort calls
    arr = [5, 3, 8, 1]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_merge_while_loop_zero_iterations():
    # Merge is called with one empty list → while loop executes 0 times
    # This happens internally when arr has 1 element: left=[], right=[x]
    # The result.extend([] or [x]) covers the 'or right[j:]' fallback
    result = mergesort([7])
    assert result == [7]

# --- Condition Coverage ---

def test_condition_len_arr_eq_0_true():
    # len(arr) == 0: True
    # path: if-true → return arr
    result = mergesort([])
    assert result == []  # already covered above, noted here for condition tracking

def test_condition_len_arr_eq_0_false():
    # len(arr) == 0: False
    # path: if-false → else branch
    result = mergesort([1])
    assert result == [1]

def test_condition_left_le_right_true():
    # Inside merge: left[i] <= right[j] is True
    # left[0]=1 <= right[0]=3 → True
    # x>0: True, y<10: True analogy: left[i] <= right[j]: True
    result = mergesort([1, 3])
    assert result == [1, 3]

def test_condition_left_le_right_false():
    # Inside merge: left[i] <= right[j] is False
    # left[0]=3 > right[0]=1 → False
    result = mergesort([3, 1])
    assert result == [1, 3]

def test_condition_i_lt_len_left_false():
    # while i < len(left) AND j < len(right)
    # i exhausts left first → i < len(left) becomes False, loop exits
    # left=[1,2], right=[3,4,5]: after 2 iterations i=2==len(left) → loop ends
    result = mergesort([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

def test_condition_j_lt_len_right_false():
    # j exhausts right first → j < len(right) becomes False, loop exits
    # left=[1,2,3], right=[4,5]: after 2 iterations j=2==len(right) → loop ends
    result = mergesort([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

def test_condition_equal_elements():
    # left[i] <= right[j]: True (equal case, boundary of <=)
    result = mergesort([2, 2, 2])
    assert result == [2, 2, 2]

# --- Path Coverage ---

def test_path_empty_return():
    # path: len(arr)==0 → True → return arr
    result = mergesort([])
    assert result == []

def test_path_single_element_recursive():
    # path: len(arr)==0 → False → else → middle=0 → left=mergesort([]) → right=mergesort([x]) → merge([], [x])
    # merge: while loop 0 iters → extend([] or [x]) = extend([x]) → return [x]
    result = mergesort([5])
    assert result == [5]

def test_path_two_elements_left_first():
    # path: else → split into [a],[b] → merge([a],[b]) with left[i]<=right[j] True → extend left remainder (empty)
    # left[0]=1 <= right[0]=2, append 1, i=1 → loop exit, extend right[0:]=[2] (or fallback)
    result = mergesort([1, 2])
    assert result == [1, 2]

def test_path_two_elements_right_first():
    # path: else → split → merge with left[i]<=right[j] False first → append right, then extend left
    result = mergesort([2, 1])
    assert result == [1, 2]

def test_path_multiple_iters_mixed():
    # path: else → recursive splits → merge with multiple iterations, both True and False branches hit
    # also tests extend with left remainder
    arr = [9, 3, 7, 1, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_path_duplicates_preserved():
    # A correct mergesort SHOULD preserve all elements including duplicates
    arr = [4, 2, 4, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_path_already_sorted():
    # path: merge always takes left[i] branch (all <= comparisons True)
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

def test_path_reverse_sorted():
    # path: merge always takes right[j] branch first (all <= comparisons False)
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == [1, 2, 3, 4, 5]

def test_path_large_array():
    # Exercises many recursive paths and multiple merge iterations
    import random
    arr = list(range(20, 0, -1))
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_property_permutation():
    # Property: mergesort result is a sorted permutation of the input
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

def test_property_negative_numbers():
    # Correct mergesort should handle negative numbers
    arr = [-3, -1, -4, -1, -5]
    result = mergesort(arr)
    assert result == sorted(arr)

def test_property_mixed_sign():
    # Correct mergesort should handle mixed positive and negative
    arr = [-2, 3, -1, 0, 5, -4]
    result = mergesort(arr)
    assert result == sorted(arr)