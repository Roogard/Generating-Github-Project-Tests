_(showing 10 of 13 failures)_

## Trigger Test(s)

```python
# test_blackbox.py
from python_programs.quicksort import quicksort

# --- BVA ---

def test_bva_empty_array():
    # Boundary: empty collection
    result = quicksort([])
    assert result == []

def test_bva_single_element():
    # Boundary: single element collection
    result = quicksort([42])
    assert result == [42]

def test_bva_two_elements_sorted():
    # Boundary: two elements already sorted
    result = quicksort([1, 2])
    assert result == [1, 2]

def test_bva_two_elements_reverse():
    # Boundary: two elements in reverse order
    result = quicksort([2, 1])
    assert result == [1, 2]

def test_bva_large_sorted_input():
    # Boundary: already sorted large input (worst-case pivot selection)
    inp = list(range(1, 101))
    result = quicksort(inp)
    assert result == list(range(1, 101))

def test_bva_large_reverse_sorted():
    # Boundary: reverse sorted large input
    inp = list(range(100, 0, -1))
    result = quicksort(inp)
    assert result == list(range(1, 101))

def test_bva_all_identical_elements():
    # Boundary: all elements equal — a correct quicksort preserves all elements
    # Note: this implementation drops duplicates (keeps only pivot), which is a known bug
    # We test against the correct specification: sorted output preserving all elements
    inp = [5, 5, 5, 5]
    result = quicksort(inp)
    # A correct quicksort SHOULD return all elements sorted
    assert result == sorted(inp)

def test_bva_negative_numbers():
    # Boundary: all negative values
    inp = [-3, -1, -4, -1, -5]
    result = quicksort(inp)
    assert result == sorted(inp)

def test_bva_min_max_integers():
    # Boundary: very large and very small integers
    inp = [10**9, -10**9, 0]
    result = quicksort(inp)
    assert result == [-10**9, 0, 10**9]

# --- ECP ---

def test_ecp_valid_typical_unsorted():
    # Valid class: typical unsorted list of distinct integers
    inp = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(inp)
    assert result == sorted(inp)

def test_ecp_valid_already_sorted():
    # Valid class: already sorted input (distinct elements)
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_reverse_sorted():
    # Valid class: reverse sorted input
    inp = [5, 4, 3, 2, 1]
    result = quicksort(inp)
    assert result == [1, 2, 3, 4, 5]

def test_ecp_valid_with_duplicates():
    # Valid class: list with duplicate elements
    # A correct quicksort MUST preserve all elements including duplicates
    inp = [3, 1, 2, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_ecp_valid_mixed_positive_negative():
    # Valid class: mix of positive, negative, and zero
    inp = [-5, 0, 3, -2, 7]
    result = quicksort(inp)
    assert result == [-5, -2, 0, 3, 7]

def test_ecp_valid_floats():
    # Valid class: floating point numbers
    inp = [3.14, 1.0, 2.71, 0.5]
    result = quicksort(inp)
    assert result == [0.5, 1.0, 2.71, 3.14]

def test_ecp_valid_single_duplicate_pair():
    # Valid class: exactly two equal elements
    inp = [7, 7]
    result = quicksort(inp)
    # A correct quicksort SHOULD return [7, 7]
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_ecp_valid_pivot_is_largest():
    # Valid class: pivot (first element) is the largest
    inp = [9, 1, 3, 5, 7]
    result = quicksort(inp)
    assert result == [1, 3, 5, 7, 9]

def test_ecp_valid_pivot_is_smallest():
    # Valid class: pivot (first element) is the smallest
    inp = [1, 9, 7, 5, 3]
    result = quicksort(inp)
    assert result == [1, 3, 5, 7, 9]

# --- Mutation Detection ---

def test_mutation_offbyone_lesser_boundary():
    # Detects: '<' changed to '<=' in lesser partition
    # If '<=' is used, pivot duplicates go to lesser, causing wrong output
    inp = [3, 1, 3, 5]
    result = quicksort(inp)
    # A correct quicksort SHOULD return sorted(inp) with all elements
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_offbyone_greater_boundary():
    # Detects: '>' changed to '>=' in greater partition
    # If '>=' is used, pivot duplicates go to greater, causing wrong output
    inp = [3, 5, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_wrong_variable_arr1_instead_of_arr0():
    # Detects: pivot = arr[1] instead of arr[0]
    # With arr = [10, 1, 2], correct pivot is 10, giving [1, 2, 10]
    # Wrong pivot arr[1]=1 gives [1, 2, 10] only by accident; use a case that differs
    # arr = [5, 1, 9]: correct pivot 5 -> [1, 5, 9]; wrong pivot 1 -> [1, 5, 9] same
    # Use arr = [3, 9, 1]: correct pivot 3 -> [1, 3, 9]; wrong pivot 9 -> [1, 3, 9] same
    # Better: arr = [2, 8, 1]: correct pivot 2 -> lesser=[1], greater=[8] -> [1,2,8]
    #         wrong pivot arr[1]=8 -> lesser=[2,1], greater=[] -> quicksort([2,1])+[8] -> [1,2,8] same
    # Use arr = [5, 1]: correct -> [1, 5]; wrong pivot arr[1]=1 -> lesser=[], greater=[5] -> [1, 5] same
    # Use arr = [1, 5, 3]: correct pivot=1 -> lesser=[], greater=[5,3] -> [1,3,5]
    #          wrong pivot=5 -> lesser=[1,3], greater=[] -> [1,3,5] same
    # The function result is [1,3,5] in both cases; use full correctness check instead
    inp = [4, 2, 6, 1, 5]
    result = quicksort(inp)
    assert result == [1, 2, 4, 5, 6]

def test_mutation_wrong_operator_plus_instead_of_concat():
    # Detects: return order changed, e.g., greater + [pivot] + lesser instead of lesser + [pivot] + greater
    inp = [3, 1, 5]
    result = quicksort(inp)
    assert result == [1, 3, 5]
    assert result[0] < result[1] < result[2]

def test_mutation_negation_not_arr_removed():
    # Detects: base case `if not arr` changed to `if arr` (always returns [] for non-empty)
    inp = [1]
    result = quicksort(inp)
    assert result == [1]  # Would return [] if condition is flipped

def test_mutation_constant_wrong_initial_pivot_index():
    # Detects: arr[0] changed to arr[-1] (last element as pivot)
    # For most inputs result is still sorted; test correctness property
    inp = [5, 3, 8, 1, 9, 2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mutation_preserves_all_elements_including_duplicates():
    # Detects: duplicate elements silently dropped (common quicksort bug with strict < and >)
    # A correct quicksort MUST NOT lose elements
    inp = [4, 4, 4, 2, 2, 6, 6]
    result = quicksort(inp)
    assert len(result) == len(inp), "A correct quicksort must preserve all elements including duplicates"
    assert result == sorted(inp)

def test_mutation_output_is_sorted_property():
    # General mutation catcher: output must be non-decreasing
    inp = [10, -3, 0, 7, 2, -1, 4]
    result = quicksort(inp)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1], "A correct quicksort must produce non-decreasing output"

def test_mutation_length_preserved_no_drops():
    # Detects any mutation that causes element loss (e.g., missing pivot in return)
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert len(result) == len(inp)

def test_mutation_pivot_included_in_output():
    # Detects: return lesser + greater (pivot omitted)
    inp = [5, 3, 7]
    result = quicksort(inp)
    assert 5 in result
    assert result == [3, 5, 7]
```

```python
# test_whitebox.py
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
```

## Error Message(s)

### [FAILURE] test_bva_all_identical_elements (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [5, 5, 5, 5]
Actual:   [5]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:44: in test_bva_all_identical_elements
    assert result == sorted(inp)
E   assert [5] == [5, 5, 5, 5]
E     
E     Right contains 3 more items, first extra item: 5
E     Use -v to get more diff
```

### [FAILURE] test_bva_negative_numbers (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [-5, -4, -3, -1, -1]
Actual:   [-5, -4, -3, -1]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:50: in test_bva_negative_numbers
    assert result == sorted(inp)
E   assert [-5, -4, -3, -1] == [-5, -4, -3, -1, -1]
E     
E     Right contains one more item: -1
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_typical_unsorted (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [1, 1, 2, 3, 4, 5, ...]
Actual:   [1, 2, 3, 4, 5, 6, ...]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:64: in test_ecp_valid_typical_unsorted
    assert result == sorted(inp)
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 1, 2, 3, 4, 5, ...]
E     
E     At index 1 diff: 2 != 1
E     Right contains one more item: 9
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_with_duplicates (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [1, 1, 2, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:83: in test_ecp_valid_with_duplicates
    assert result == sorted(inp)
E   assert [1, 2, 3] == [1, 1, 2, 3, 3]
E     
E     At index 1 diff: 2 != 1
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_ecp_valid_single_duplicate_pair (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [7, 7]
Actual:   [7]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:103: in test_ecp_valid_single_duplicate_pair
    assert result == sorted(inp)
E   assert [7] == [7, 7]
E     
E     Right contains one more item: 7
E     Use -v to get more diff
```

### [FAILURE] test_mutation_offbyone_lesser_boundary (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [1, 3, 3, 5]
Actual:   [1, 3, 5]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:126: in test_mutation_offbyone_lesser_boundary
    assert result == sorted(inp)
E   assert [1, 3, 5] == [1, 3, 3, 5]
E     
E     At index 2 diff: 5 != 3
E     Right contains one more item: 5
E     Use -v to get more diff
```

### [FAILURE] test_mutation_offbyone_greater_boundary (type: blackbox)
Assertion: assert result == sorted(inp)
Expected: [1, 3, 3, 5]
Actual:   [1, 3, 5]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:134: in test_mutation_offbyone_greater_boundary
    assert result == sorted(inp)
E   assert [1, 3, 5] == [1, 3, 3, 5]
E     
E     At index 2 diff: 5 != 3
E     Right contains one more item: 5
E     Use -v to get more diff
```

### [FAILURE] test_mutation_preserves_all_elements_including_duplicates (type: blackbox)
Assertion: assert len(result) == len(inp), "A correct quicksort must preserve all elements including duplicates"
Expected: 7
Actual:   3
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_blackbox.py:179: in test_mutation_preserves_all_elements_including_duplicates
    assert len(result) == len(inp), "A correct quicksort must preserve all elements including duplicates"
E   AssertionError: A correct quicksort must preserve all elements including duplicates
E   assert 3 == 7
E    +  where 3 = len([2, 4, 6])
E    +  and   7 = len([4, 4, 4, 2, 2, 6, ...])
```

### [FAILURE] test_multiple_elements (type: whitebox)
Assertion: assert result == sorted(arr)
Expected: [1, 1, 2, 3, 4, 5, ...]
Actual:   [1, 2, 3, 4, 5, 6, ...]
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_whitebox.py:24: in test_multiple_elements
    assert result == sorted(arr)
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 1, 2, 3, 4, 5, ...]
E     
E     At index 1 diff: 2 != 1
E     Right contains one more item: 9
E     Use -v to get more diff
```

### [FAILURE] test_condition_x_greater_than_pivot_false_and_less_false (type: whitebox)
Assertion: assert len(result) == len(arr)
Expected: 3
Actual:   1
```
eval_output\28-03-2026_12-06\QuixBugs\generated_tests\quicksort_1\test_whitebox.py:100: in test_condition_x_greater_than_pivot_false_and_less_false
    assert len(result) == len(arr)
E   assert 1 == 3
E    +  where 1 = len([3])
E    +  and   3 = len([3, 3, 3])
```
