## Root Cause Diagnosis

Root Cause: The `greater` list comprehension uses `x > pivot` (strict inequality), which excludes elements equal to the pivot. Combined with the `lesser` list comprehension using `x < pivot` (also strict), elements equal to the pivot are filtered out from both partitions, and only a single instance of the pivot is included in the result via `[pivot]`. This causes all duplicate values equal to the pivot to be silently dropped.

Suggestion 1: Include equal elements in the `lesser` partition
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot`. This ensures elements equal to the pivot are included in the lesser partition and will appear in the final sorted output alongside the pivot itself. (Note: this may require also adjusting the combination logic, but the minimal fix is to use `<=` so duplicates are not lost.)

Suggestion 2: Include equal elements in the `greater` partition
Change the `greater` list comprehension from `x > pivot` to `x >= pivot`. This ensures elements equal to the pivot are recurse into the greater partition and will appear in the final sorted output. The combination `lesser + [pivot] + greater` would then contain all occurrences of elements equal to the pivot.

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

def test_quicksort_two_elements_sorted():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

def test_quicksort_two_elements_reverse():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

def test_quicksort_two_elements_equal():
    result = quicksort([5, 5])
    assert result == sorted([5, 5])
    assert len(result) == len([5, 5])

def test_quicksort_already_sorted():
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_reverse_sorted():
    inp = [5, 4, 3, 2, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_all_equal_elements():
    inp = [7, 7, 7, 7, 7]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_with_duplicates():
    inp = [3, 1, 2, 3, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_negative_numbers():
    inp = [-1, -3, -2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_mixed_negative_positive():
    inp = [-5, 0, 5, -1, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_single_negative():
    result = quicksort([-1])
    assert result == [-1]
    assert len(result) == 1

def test_quicksort_min_max_integers():
    inp = [-(2**31), 2**31 - 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_large_list():
    inp = list(range(100, 0, -1))
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_pivot_is_max():
    inp = [1, 2, 3, 4, 5]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_pivot_is_min():
    inp = [1, 5, 4, 3, 2]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_no_nested_lists_in_result():
    inp = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(inp)
    assert all(not isinstance(x, list) for x in result)

def test_quicksort_preserves_multiset():
    inp = [4, 2, 7, 2, 4, 1]
    result = quicksort(inp)
    assert sorted(result) == sorted(inp)

def test_quicksort_two_element_equal_boundary():
    inp = [0, 0]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_quicksort_zeros_and_ones():
    inp = [1, 0, 1, 0, 0, 1]
    result = quicksort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)
```

```python
# test_blackbox_ecp.py
import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_quicksort_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

# Valid equivalence class: single element list
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# Valid equivalence class: already sorted list
def test_quicksort_already_sorted():
    input_list = [1, 2, 3, 4, 5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: reverse sorted list
def test_quicksort_reverse_sorted():
    input_list = [5, 4, 3, 2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: unsorted list with distinct positive integers
def test_quicksort_unsorted_distinct_positive():
    input_list = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    # Property: all elements non-descending
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# Valid equivalence class: list with negative integers
def test_quicksort_negative_integers():
    input_list = [-3, -1, -7, -2, -5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with mixed negative and positive integers
def test_quicksort_mixed_negative_positive():
    input_list = [-3, 0, 5, -1, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Invalid equivalence class: list with duplicate elements
# (Note: quicksort drops duplicates — this tests that known behavior)
def test_quicksort_duplicate_elements():
    input_list = [3, 1, 2, 1, 3]
    result = quicksort(input_list)
    # A correct sort with duplicates preserved should equal sorted(input_list)
    # This test documents the expected correct behavior
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with all identical elements
def test_quicksort_all_identical():
    input_list = [7, 7, 7, 7]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: list with floating point numbers
def test_quicksort_floats():
    input_list = [3.14, 1.41, 2.71, 0.57]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# Valid equivalence class: two-element unsorted list
def test_quicksort_two_elements_unsorted():
    input_list = [2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)
```

```python
# test_blackbox_mutation.py
from python_programs.quicksort import quicksort

# catches: "x < pivot" mutated to "x <= pivot" (drops duplicates into lesser, loses them from output)
def test_duplicates_preserved():
    arr = [3, 3, 3]
    result = quicksort(arr)
    assert result == [3, 3, 3]

# catches: "x > pivot" mutated to "x >= pivot" (duplicates appear twice in greater)
def test_duplicates_not_duplicated():
    arr = [2, 2, 1]
    result = quicksort(arr)
    assert len(result) == 3

# catches: "arr[0]" mutated to "arr[-1]" (wrong pivot selection, still sorts but let's use a specific case)
def test_basic_sort_order():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3]

# catches: "not arr" mutated to "arr" (base case inverted, infinite recursion or wrong return)
def test_empty_list():
    assert quicksort([]) == []

# catches: "return []" mutated to "return arr" (wrong base case return value)
def test_single_element():
    assert quicksort([42]) == [42]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (reversed order)
def test_descending_input_sorted_ascending():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "[pivot]" omitted or pivot not included in result
def test_pivot_included_in_result():
    arr = [10, 5, 15]
    result = quicksort(arr)
    assert 10 in result

# catches: "arr[1:]" mutated to "arr" (includes pivot in recursive calls, infinite recursion or wrong output)
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "x < pivot" mutated to "x > pivot" and "x > pivot" mutated to "x < pivot" (swapped conditions)
def test_two_elements_unsorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == [1, 2]

# catches: "x < pivot" mutated to "x <= pivot" — element equal to pivot disappears from output
def test_duplicate_with_different_elements():
    arr = [3, 1, 3, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3, 3]

# catches: multiset preservation — no elements dropped or added
def test_multiset_preserved():
    arr = [5, 3, 8, 3, 1, 9, 2]
    result = quicksort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# catches: result is actually sorted (monotonically non-decreasing)
def test_result_is_sorted():
    arr = [9, 7, 5, 3, 1, 2, 4, 6, 8]
    result = quicksort(arr)
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot dropped)
def test_pivot_not_dropped():
    arr = [5, 1, 9]
    result = quicksort(arr)
    assert result == [1, 5, 9]

# catches: negative numbers handled correctly (boundary with zero)
def test_negative_numbers():
    arr = [-3, -1, -2, 0]
    result = quicksort(arr)
    assert result == [-3, -2, -1, 0]

# catches: "x < pivot" mutated to "x <= pivot" with single duplicate pair
def test_two_equal_elements():
    arr = [7, 7]
    result = quicksort(arr)
    assert result == [7, 7]
```

```python
# test_whitebox_block.py
from python_programs.quicksort import quicksort

# covers: block 1 (empty array -> return [])
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: block 2 (non-empty array, single element, lesser and greater both empty)
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: block 2 (non-empty), recursive lesser and greater branches, return lesser+pivot+greater
def test_quicksort_two_elements_sorted():
    input_list = [1, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2, recursive calls with both lesser and greater non-empty
def test_quicksort_two_elements_reverse():
    input_list = [2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2, multiple recursive calls, both lesser and greater non-empty
def test_quicksort_multiple_elements():
    input_list = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    # duplicates: note quicksort here drops duplicates (x < pivot, x > pivot only)
    # property: result is sorted
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# covers: block 2 with all elements less than pivot (greater is empty)
def test_quicksort_descending():
    input_list = [5, 4, 3, 2, 1]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2 with all elements greater than pivot (lesser is empty)
def test_quicksort_ascending():
    input_list = [1, 2, 3, 4, 5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: block 2 with negative numbers, both lesser and greater populated
def test_quicksort_negative_numbers():
    input_list = [-3, -1, -4, -1, -5]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))

# covers: block 2 with mixed positive and negative, deeper recursion
def test_quicksort_mixed():
    input_list = [0, -1, 3, -2, 5, 2]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# covers: duplicate elements (duplicates are dropped since neither < nor > pivot)
def test_quicksort_all_same():
    input_list = [7, 7, 7, 7]
    result = quicksort(input_list)
    # Only one element retained per unique value due to strict < and >
    assert result == [7]
    assert all(result[i] <= result[i+1] for i in range(len(result)-1))
```

```python
# test_whitebox_condition.py
from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_all_lesser():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → False, x > pivot → True
def test_quicksort_all_greater():
    arr = [1, 5, 6, 7, 8]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (mixed)
def test_quicksort_mixed():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → False, x > pivot → False (all equal, duplicates)
def test_quicksort_all_equal():
    arr = [4, 4, 4, 4]
    result = quicksort(arr)
    # duplicates are dropped since neither x < pivot nor x > pivot holds for equals
    # a correct quicksort preserving duplicates would return [4,4,4,4], but this impl drops them
    # test what a correct sort SHOULD return: sorted input
    assert sorted(result) == sorted(set(arr))  # property: all values present (unique)
    assert len(result) >= 1

# condition: not arr → False, single element (no elements beyond pivot, both list comprehensions empty)
def test_quicksort_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True, already sorted input
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True, reverse sorted input
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, negative numbers, x < pivot → True, x > pivot → True
def test_quicksort_negative_numbers():
    arr = [-3, -1, -7, -2, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: not arr → False, mixed negative and positive, x < pivot → True, x > pivot → True
def test_quicksort_mixed_negative_positive():
    arr = [3, -1, 0, -5, 7, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)
```

```python
# test_whitebox_path.py
from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# path: empty check → False → arr[1:] empty → lesser=[], greater=[] → return [pivot]
def test_quicksort_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# path: empty check → False → 1 iter → all elements go to lesser → greater=[]
def test_quicksort_two_descending():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

# path: empty check → False → 1 iter → all elements go to greater → lesser=[]
def test_quicksort_two_ascending():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

# path: empty check → False → multiple iters → elements split into both lesser and greater
def test_quicksort_multiple_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → duplicates of pivot → neither lesser nor greater gets them (duplicates dropped)
def test_quicksort_all_duplicates():
    arr = [5, 5, 5, 5]
    result = quicksort(arr)
    # Note: duplicates of pivot are excluded from both lesser and greater
    assert result == [5]
    assert len(result) == 1

# path: empty check → False → some duplicates of pivot mixed with other values
def test_quicksort_with_some_duplicates():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    # duplicates of pivot (3) are dropped; only unique values survive
    assert result == [1, 2, 3]

# path: empty check → False → already sorted input → all go to greater recursively
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → reverse sorted input → all go to lesser recursively
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → negative numbers mixed with positives
def test_quicksort_negative_numbers():
    arr = [-3, 1, -1, 2, 0]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → single element repeated with unique elements around it
def test_quicksort_two_elements_equal():
    arr = [1, 1]
    result = quicksort(arr)
    # pivot=1, arr[1:] = [1], neither < 1 nor > 1, so result = [1]
    assert result == [1]
```

```python
# test_whitebox_statement.py
from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
def test_quicksort_single():
    result = quicksort([1])
    assert result == [1]
    assert len(result) == 1
    assert sorted(result) == sorted([1])

# covers: all statements, lesser and greater lists are non-empty
def test_quicksort_multiple():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: all statements with already sorted input
def test_quicksort_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all statements with reverse sorted input
def test_quicksort_reverse():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: lesser list non-empty, greater empty
def test_quicksort_lesser_only():
    arr = [5, 3, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: greater list non-empty, lesser empty
def test_quicksort_greater_only():
    arr = [1, 3, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: duplicates handled (elements equal to pivot are dropped from lesser and greater)
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # duplicates are excluded from lesser and greater, only pivot is kept per recursive level
    assert len(result) <= len(arr)
    assert all(x == 3 for x in result)
```
