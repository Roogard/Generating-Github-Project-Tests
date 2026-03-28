from python_programs.quicksort import quicksort

# --- Statement Coverage ---

def test_empty_array_returns_empty():
    # Covers the `if not arr: return []` branch
    # path: empty → return []
    result = quicksort([])
    assert result == []

def test_single_element():
    # Covers pivot selection, lesser/greater (both empty), and return lesser+[pivot]+greater
    # x>0: False (arr has 1 element, arr[1:] is empty)
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

def test_multiple_elements():
    # Covers recursive calls with actual lesser/greater partitions
    # path: non-empty → recurse lesser → recurse greater → return combined
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    # A correct quicksort must produce a sorted list preserving all elements
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Block Coverage ---

def test_already_sorted():
    # Covers the case where lesser is always empty, greater recurses
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_reverse_sorted():
    # Covers the case where greater is always empty, lesser recurses
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_two_elements_lesser_branch():
    # Forces lesser to have one element, greater empty
    arr = [2, 1]
    result = quicksort(arr)
    assert result == [1, 2]
    assert len(result) == 2

def test_two_elements_greater_branch():
    # Forces greater to have one element, lesser empty
    arr = [1, 2]
    result = quicksort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# --- Condition Coverage ---

def test_condition_not_arr_true():
    # `not arr` evaluates to True (empty list)
    # not arr: True
    result = quicksort([])
    assert result == []

def test_condition_not_arr_false():
    # `not arr` evaluates to False (non-empty list)
    # not arr: False
    result = quicksort([7])
    assert result == [7]

def test_condition_x_less_than_pivot_true():
    # `x < pivot` is True for some elements → lesser is non-empty
    # x < pivot: True (1 < 3), x > pivot: False (1 not > 3)
    arr = [3, 1]
    result = quicksort(arr)
    assert result == [1, 3]

def test_condition_x_less_than_pivot_false():
    # `x < pivot` is False for all elements → lesser is empty
    # x < pivot: False (5 not < 3), x > pivot: True (5 > 3)
    arr = [3, 5]
    result = quicksort(arr)
    assert result == [3, 5]

def test_condition_x_greater_than_pivot_true():
    # `x > pivot` is True for some elements → greater is non-empty
    # x > pivot: True (10 > 3)
    arr = [3, 10]
    result = quicksort(arr)
    assert result == [3, 10]

def test_condition_x_greater_than_pivot_false_and_less_false():
    # `x < pivot` is False AND `x > pivot` is False → duplicate pivot is excluded
    # x < pivot: False (3 not < 3), x > pivot: False (3 not > 3)
    # A correct quicksort SHOULD preserve duplicates; note this implementation drops them.
    # We assert the property that sorting preserves count — to detect the bug:
    arr = [3, 3, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all elements including duplicates
    assert len(result) == len(arr)
    assert result == sorted(arr)  # [3, 3, 3]

def test_duplicates_mixed():
    # Some elements equal to pivot, some less, some greater
    # x < pivot: True, x > pivot: True, x == pivot: both False (dropped by this impl)
    arr = [3, 1, 3, 5, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all elements including duplicates
    assert len(result) == len(arr)
    assert result == sorted(arr)

# --- Path Coverage ---

def test_path_empty_immediate_return():
    # path: entry → not arr is True → return []
    result = quicksort([])
    assert result == []

def test_path_single_element_no_recursion_depth():
    # path: entry → not arr is False → pivot=arr[0] → lesser=[] → greater=[] → return [pivot]
    result = quicksort([99])
    assert result == [99]

def test_path_two_elements_lesser_only():
    # path: entry → lesser recurses once (depth 1) → greater is empty
    # [2, 1]: pivot=2, lesser=[1], greater=[]
    result = quicksort([2, 1])
    assert result == [1, 2]

def test_path_two_elements_greater_only():
    # path: entry → lesser is empty → greater recurses once (depth 1)
    # [1, 2]: pivot=1, lesser=[], greater=[2]
    result = quicksort([1, 2])
    assert result == [1, 2]

def test_path_both_lesser_and_greater_recurse():
    # path: entry → lesser recurses → greater recurses → return combined
    # [2, 1, 3]: pivot=2, lesser=[1], greater=[3]
    result = quicksort([2, 1, 3])
    assert result == [1, 2, 3]

def test_path_deep_recursion_multiple_levels():
    # path: multiple levels of recursion on both sides
    arr = [5, 3, 7, 1, 4, 6, 8]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_path_all_equal_elements():
    # path: each level has empty lesser and empty greater (all equal to pivot are dropped)
    # A correct sort must preserve count of equal elements
    arr = [4, 4, 4, 4]
    result = quicksort(arr)
    assert len(result) == len(arr)
    assert result == sorted(arr)

def test_path_negative_numbers():
    # path: ensures comparisons work correctly with negatives
    arr = [-3, -1, -4, -1, -5, -9, -2, -6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_path_mixed_positive_negative():
    # path: pivot=0, lesser=negatives, greater=positives
    arr = [0, -1, 1, -2, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)