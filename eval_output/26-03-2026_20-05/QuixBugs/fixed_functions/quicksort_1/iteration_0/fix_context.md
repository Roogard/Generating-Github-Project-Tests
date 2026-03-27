## Root Cause Diagnosis

Root Cause: The partition logic uses strict `x < pivot` for `lesser` and strict `x > pivot` for `greater`, which means elements equal to the pivot (other than the pivot itself) are excluded from both partitions and dropped entirely from the result. This causes duplicates to be lost and, in the case of already-sorted or reverse-sorted arrays with many equal-pivot scenarios, leads to infinite recursion because elements equal to the pivot are never consumed.

Suggestion 1: Include duplicates in the `lesser` partition
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot` so that elements equal to the pivot are included in one of the partitions. This ensures all duplicate values are preserved in the output. The `greater` partition filter (`x > pivot`) remains unchanged.

Suggestion 2: Include duplicates in the `greater` partition
Change the `greater` list comprehension from `x > pivot` to `x >= pivot` so that elements equal to the pivot are captured in the `greater` partition instead. The `lesser` filter (`x < pivot`) remains unchanged. Either suggestion correctly preserves all duplicate elements, though Suggestion 1 is the more conventional approach.

## Trigger Test(s)

```python
# test_blackbox_bva.py
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([42]) == [42]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_all_duplicates():
    assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]

def test_quicksort_two_duplicates():
    assert quicksort([2, 2]) == [2, 2]

def test_quicksort_duplicates_with_other_elements():
    assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]

def test_quicksort_negative_numbers():
    assert quicksort([-1, -3, -2]) == [-3, -2, -1]

def test_quicksort_single_negative():
    assert quicksort([-1]) == [-1]

def test_quicksort_mixed_negative_and_positive():
    assert quicksort([-1, 0, 1]) == [-1, 0, 1]

def test_quicksort_mixed_negative_and_positive_unsorted():
    assert quicksort([1, -1, 0]) == [-1, 0, 1]

def test_quicksort_with_zero():
    assert quicksort([0]) == [0]

def test_quicksort_zeros_and_positives():
    assert quicksort([0, 1, 0]) == [0, 0, 1]

def test_quicksort_large_list_boundary():
    arr = list(range(999, -1, -1))
    assert quicksort(arr) == list(range(0, 1000))

def test_quicksort_large_list_already_sorted():
    arr = list(range(0, 1000))
    assert quicksort(arr) == list(range(0, 1000))

def test_quicksort_large_single_value_repeated():
    arr = [7] * 100
    assert quicksort(arr) == [7] * 100

def test_quicksort_pivot_is_max():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_pivot_is_min():
    assert quicksort([1, 5, 4, 3, 2]) == [1, 2, 3, 4, 5]

def test_quicksort_two_elements_equal():
    assert quicksort([5, 5]) == [5, 5]

def test_quicksort_large_and_small_boundary_values():
    assert quicksort([10**9, -10**9, 0]) == [-10**9, 0, 10**9]

def test_quicksort_single_large_value():
    assert quicksort([10**9]) == [10**9]

def test_quicksort_single_small_value():
    assert quicksort([-10**9]) == [-10**9]
```

```python
# test_blackbox_mutation.py
from python_programs.quicksort import quicksort

# catches: "not arr" mutated to "arr" (negation error) - base case inverted
def test_empty_list_returns_empty():
    assert quicksort([]) == []

# catches: "arr[0]" mutated to "arr[1]" (wrong index for pivot)
def test_single_element():
    assert quicksort([42]) == [42]

# catches: "x < pivot" mutated to "x <= pivot" (duplicates lost or wrong partition)
def test_duplicate_elements_preserved():
    result = quicksort([3, 1, 3, 2, 3])
    assert result == [1, 2, 3, 3, 3]

# catches: "x < pivot" mutated to "x > pivot" (lesser/greater swapped in filter)
def test_two_element_unsorted():
    assert quicksort([2, 1]) == [1, 2]

# catches: "x > pivot" mutated to "x < pivot" (greater filter wrong)
def test_two_element_sorted():
    assert quicksort([1, 2]) == [1, 2]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (wrong order)
def test_order_is_ascending():
    result = quicksort([3, 1, 4, 1, 5, 9, 2, 6])
    assert result == [1, 1, 2, 3, 4, 5, 6, 9]

# catches: "[pivot]" omitted or pivot dropped from result
def test_pivot_included_in_result():
    result = quicksort([5, 3, 7])
    assert result == [3, 5, 7]
    assert 5 in result

# catches: "arr[1:]" mutated to "arr[0:]" or "arr[2:]" (wrong slice for partition)
def test_partition_excludes_pivot():
    result = quicksort([2, 1, 3])
    assert result == [1, 2, 3]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot missing)
def test_length_preserved():
    arr = [5, 3, 8, 1, 9, 2]
    result = quicksort(arr)
    assert len(result) == len(arr)

# catches: "x < pivot" mutated to "x <= pivot" (duplicate pivot values lost)
def test_all_same_elements():
    result = quicksort([7, 7, 7, 7])
    assert result == [7, 7, 7, 7]

# catches: missing return (function returns None instead of list)
def test_returns_list_type():
    result = quicksort([3, 1, 2])
    assert isinstance(result, list)

# catches: off-by-one returning empty base case too early
def test_two_identical_elements():
    assert quicksort([4, 4]) == [4, 4]

# catches: "greater" and "lesser" variable swap in return statement
def test_descending_input_sorted_ascending():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "x > pivot" mutated to "x >= pivot" (pivot duplicated in greater)
def test_no_duplicate_pivot_in_output():
    result = quicksort([3, 3, 1, 2])
    assert result.count(3) == 2

# catches: negative numbers handled correctly (boundary with zero)
def test_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# catches: mixed positive and negative values with zero pivot
def test_mixed_sign_numbers():
    assert quicksort([0, -1, 1, -2, 2]) == [-2, -1, 0, 1, 2]
```

```python
# test_whitebox_block.py
from python_programs.quicksort import quicksort

# covers: block 1 (empty array base case) -> return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: block 2 (non-empty array), single element (lesser and greater are both empty)
def test_quicksort_single_element():
    assert quicksort([1]) == [1]

# covers: block 2, recursive calls with lesser and greater populated
def test_quicksort_sorted_order():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: block 2, already sorted input (greater populated, lesser empty recursively)
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: block 2, reverse sorted input (lesser populated, greater empty recursively)
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 2, duplicates (elements equal to pivot are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# covers: block 2, mixed duplicates
def test_quicksort_mixed_duplicates():
    assert quicksort([2, 1, 2, 3, 2]) == [1, 2, 2, 2, 3]

# covers: block 2, negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# covers: block 2, mixed negative and positive
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, 2, -5]) == [-5, -1, 0, 2, 3]

# covers: block 2, larger list to ensure full recursive coverage
def test_quicksort_larger_list():
    input_arr = [10, 3, 7, 1, 8, 4, 6, 2, 9, 5]
    assert quicksort(input_arr) == [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
```

```python
# test_whitebox_condition.py
from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    assert quicksort([]) == []

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# condition: not arr → False, x < pivot → True (elements less than pivot exist), x > pivot → True (elements greater than pivot exist)
def test_quicksort_sorted_ascending():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# condition: not arr → False, x < pivot → True, x > pivot → True
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → False (no element less than pivot), x > pivot → True
def test_quicksort_all_greater_than_pivot():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → True, x > pivot → False (no element greater than pivot)
def test_quicksort_all_lesser_than_pivot():
    assert quicksort([5, 1, 2, 3, 4]) == [1, 2, 3, 4, 5]

# condition: not arr → False, x < pivot → False, x > pivot → False (duplicates only, all equal to pivot)
def test_quicksort_all_duplicates():
    assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed with duplicates)
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 2, 3, 4]) == [1, 2, 3, 3, 4]

# condition: not arr → False, x < pivot → True, x > pivot → True (negative numbers)
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed negative and positive)
def test_quicksort_mixed_negative_positive():
    assert quicksort([-1, 3, -2, 0, 2]) == [-2, -1, 0, 2, 3]

# condition: not arr → False, x < pivot → False, x > pivot → False (single duplicate pair)
def test_quicksort_two_equal_elements():
    assert quicksort([7, 7]) == [7, 7]

# condition: not arr → False, x < pivot → True, x > pivot → True (larger list)
def test_quicksort_larger_list():
    assert quicksort([10, 3, 7, 1, 9, 5]) == [1, 3, 5, 7, 9, 10]
```

```python
# test_whitebox_path.py
from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: empty check → False → arr[1:] empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# path: empty check → False → 1 element in arr[1:] → lesser has element, greater empty
def test_quicksort_two_elements_ascending():
    assert quicksort([2, 1]) == [1, 2]

# path: empty check → False → 1 element in arr[1:] → lesser empty, greater has element
def test_quicksort_two_elements_descending():
    assert quicksort([1, 2]) == [1, 2]

# path: empty check → False → multiple elements → elements go to both lesser and greater
def test_quicksort_multiple_elements_mixed():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# path: empty check → False → all elements less than pivot (all go to lesser)
def test_quicksort_all_lesser():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: empty check → False → all elements greater than pivot (all go to greater)
def test_quicksort_all_greater():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: empty check → False → duplicates of pivot (neither lesser nor greater, duplicates dropped)
def test_quicksort_all_duplicates():
    # duplicates equal to pivot are excluded from both lesser and greater
    assert quicksort([3, 3, 3]) == [3]

# path: empty check → False → mixed with duplicates of pivot
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 3, 2, 3]) == [1, 2, 3]

# path: empty check → False → negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

# path: empty check → False → single element list of zero
def test_quicksort_single_zero():
    assert quicksort([0]) == [0]

# path: empty check → False → mixed positive and negative
def test_quicksort_mixed_positive_negative():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]
```

```python
# test_whitebox_statement.py
from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
def test_quicksort_single():
    assert quicksort([1]) == [1]

# covers: all statements with multiple elements requiring recursive lesser and greater branches
def test_quicksort_multiple():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: all statements with duplicates (duplicate elements are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]

# covers: all statements with already sorted input
def test_quicksort_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: all statements with reverse sorted input (exercises greater branch heavily)
def test_quicksort_reverse():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: all statements with negative numbers
def test_quicksort_negatives():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]
```
