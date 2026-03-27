## Root Cause Diagnosis

Root Cause: The `equal` line is `[x for x in arr if x == pivot]`, which iterates over the full `arr` (including `arr[0]`, the pivot itself). However, since `lesser` and `greater` only look at `arr[1:]`, duplicates of the pivot that appear in `arr[1:]` are excluded from both `lesser` and `greater` (strict `<` and `>`), and `equal` should capture all of them. The bug is that `equal` collects from `arr` correctly, so the original `equal` line is actually fine — the real issue is that `equal` should use `arr[1:]` plus the pivot, or equivalently keep the current `equal = [x for x in arr if x == pivot]`. Wait — re-examining: the original code with `equal = [x for x in arr if x == pivot]` DOES preserve duplicates and should work correctly. The problem revealed by Attempt 2 (which changed `equal` to `[pivot]`) shows 15 failures. The original code only had failures related to duplicates being dropped. Looking more carefully: the original `equal` collects all pivot-equal elements from `arr` (including `arr[0]`), while `lesser` and `greater` use `arr[1:]` with strict comparisons — so duplicates in `arr[1:]` equal to pivot are captured in `equal`. This IS correct. The actual bug must be that `equal` uses `arr` instead of `arr[1:]` combined with the pivot — but that gives the same result. The true bug is none of the above: the original code is actually correct, and the previous Attempt 2 broke it by replacing `equal` with `[pivot]`. The original function is correct — the fix should restore `equal = [x for x in arr if x == pivot]`.

Suggestion 1: Restore the equal list to collect all pivot-equal elements from arr
Change `equal = [pivot]` back to `equal = [x for x in arr if x == pivot]`. This correctly collects all occurrences of the pivot value from the entire array (including `arr[0]` and any duplicates in `arr[1:]`), since duplicates equal to pivot are excluded from both `lesser` and `greater` by the strict `<` and `>` comparisons.

Suggestion 2: Collect equal elements from arr[1:] and prepend pivot
Change `equal` to be `[pivot] + [x for x in arr[1:] if x == pivot]`. This is semantically equivalent to `[x for x in arr if x == pivot]` but makes it explicit that we start with the pivot and then add any duplicates from the rest of the array, achieving the same correct result while being slightly more transparent about the logic.

## Trigger Test(s)

```python
# test_blackbox_ecp.py
import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_quicksort_empty_list():
    assert quicksort([]) == []

# Valid equivalence class: single element list
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# Valid equivalence class: already sorted list
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# Valid equivalence class: reverse sorted list
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# Valid equivalence class: unsorted list with distinct elements
def test_quicksort_unsorted_distinct():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 2, 3, 4, 5, 6, 9]

# Valid equivalence class: list with duplicate elements
def test_quicksort_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# Valid equivalence class: list with negative numbers
def test_quicksort_negative_numbers():
    assert quicksort([-3, -1, -4, -2]) == [-4, -3, -2, -1]

# Valid equivalence class: list with mixed negative and positive numbers
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]

# Valid equivalence class: list with all identical elements
def test_quicksort_all_identical():
    assert quicksort([7, 7, 7, 7]) == [7, 7, 7, 7]

# Valid equivalence class: list with two elements in wrong order
def test_quicksort_two_elements_unsorted():
    assert quicksort([2, 1]) == [1, 2]
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

# catches: "x < pivot" mutated to "x <= pivot" (boundary mutation in lesser)
def test_duplicate_elements_not_duplicated():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# catches: "x < pivot" mutated to "x > pivot" (wrong operator in lesser filter)
def test_lesser_partition_correct():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# catches: "x > pivot" mutated to "x < pivot" (wrong operator in greater filter)
def test_greater_partition_correct():
    assert quicksort([1, 3, 2]) == [1, 2, 3]

# catches: "lesser + [pivot] + greater" mutated to "greater + [pivot] + lesser" (wrong order)
def test_order_is_ascending():
    assert quicksort([5, 3, 8, 1, 9, 2]) == [1, 2, 3, 5, 8, 9]

# catches: "[pivot]" omitted or mutated to "[]" (missing pivot in result)
def test_pivot_included_in_result():
    result = quicksort([2, 1, 3])
    assert result == [1, 2, 3]
    assert len(result) == 3

# catches: "arr[1:]" mutated to "arr[0:]" or "arr[:]" (including pivot in recursive calls)
def test_no_infinite_recursion_single_pivot():
    assert quicksort([5]) == [5]

# catches: "x < pivot" mutated to "x <= pivot" causing duplicates to be lost
def test_duplicates_preserved_correctly():
    assert quicksort([4, 2, 4, 1, 4]) == [1, 2, 4, 4, 4]

# catches: "x > pivot" mutated to "x >= pivot" causing duplicates to appear in greater
def test_duplicates_not_added_to_greater():
    result = quicksort([3, 3, 3, 3])
    assert result == [3, 3, 3, 3]
    assert len(result) == 4

# catches: lesser and greater swapped — full reverse order
def test_reverse_sorted_input():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# catches: "arr[1:]" mutated to "arr[2:]" (skipping an element)
def test_all_elements_present_after_sort():
    input_list = [7, 3, 5, 1, 9, 2, 8, 4, 6]
    result = quicksort(input_list)
    assert result == sorted(input_list)
    assert len(result) == len(input_list)

# catches: wrong base case condition allowing single element to recurse
def test_two_element_sorted():
    assert quicksort([2, 1]) == [1, 2]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (pivot dropped)
def test_result_length_equals_input_length():
    input_list = [10, 20, 30]
    result = quicksort(input_list)
    assert len(result) == 3
    assert result == [10, 20, 30]

# catches: negative numbers handled correctly (wrong comparison direction)
def test_negative_numbers():
    assert quicksort([-3, -1, -4, -1, -5, -9, -2]) == sorted([-3, -1, -4, -1, -5, -9, -2])

# catches: mixed positive and negative
def test_mixed_positive_negative():
    assert quicksort([-1, 3, -2, 0, 2, -3, 1]) == [-3, -2, -1, 0, 1, 2, 3]
```

```python
# test_whitebox_block.py
from python_programs.quicksort import quicksort

# covers: block 1 (empty array -> return [])
def test_empty_array():
    assert quicksort([]) == []

# covers: block 2 (single element, lesser and greater are both empty)
def test_single_element():
    assert quicksort([1]) == [1]

# covers: block 2, recursive lesser and greater paths
def test_sorted_array():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: block 2, recursive lesser and greater paths with unsorted input
def test_unsorted_array():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# covers: block 2 with reverse sorted input (exercises greater path heavily)
def test_reverse_sorted_array():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: block 2, duplicates (elements equal to pivot are excluded from lesser and greater)
def test_all_duplicates():
    assert quicksort([3, 3, 3]) == [3, 3, 3]

# covers: block 2 with negative numbers
def test_negative_numbers():
    assert quicksort([-3, -1, -2, 0]) == [-3, -2, -1, 0]

# covers: block 2 with mixed negative and positive
def test_mixed_positive_negative():
    assert quicksort([3, -1, 0, -5, 2]) == [-5, -1, 0, 2, 3]

# covers: block 2 with two elements (lesser empty, greater non-empty)
def test_two_elements_ascending():
    assert quicksort([1, 2]) == [1, 2]

# covers: block 2 with two elements (lesser non-empty, greater empty)
def test_two_elements_descending():
    assert quicksort([2, 1]) == [1, 2]
```

```python
# test_whitebox_condition.py
from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    assert quicksort([]) == []

# condition: not arr → False (non-empty list); x < pivot → True for some elements
def test_quicksort_single_element():
    assert quicksort([42]) == [42]

# condition: not arr → False; x < pivot → True, x > pivot → True (elements on both sides)
def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

# condition: not arr → False; x < pivot → False (all greater), x > pivot → True
def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

# condition: not arr → False; x < pivot → True, x > pivot → True
def test_quicksort_multiple_elements():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# condition: not arr → False; x < pivot → False for all (already sorted ascending)
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# condition: not arr → False; x > pivot → False for all (reverse sorted, all lesser)
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# condition: not arr → False; x < pivot → False, x > pivot → False (all duplicates)
def test_quicksort_all_duplicates():
    assert quicksort([7, 7, 7, 7]) == [7, 7, 7, 7]

# condition: not arr → False; x < pivot → True, x > pivot → True (negative numbers)
def test_quicksort_with_negatives():
    assert quicksort([-3, -1, -4, -1, -5]) == [-5, -4, -3, -1, -1]

# condition: not arr → False; x < pivot → True, x > pivot → True (mixed negative and positive)
def test_quicksort_mixed_negative_positive():
    assert quicksort([3, -1, 0, 5, -2]) == [-2, -1, 0, 3, 5]

# condition: not arr → False; x < pivot → True only (pivot is maximum)
def test_quicksort_pivot_is_max():
    assert quicksort([9, 1, 2, 3]) == [1, 2, 3, 9]

# condition: not arr → False; x > pivot → True only (pivot is minimum)
def test_quicksort_pivot_is_min():
    assert quicksort([1, 9, 8, 7]) == [1, 7, 8, 9]
```

```python
# test_whitebox_path.py
from python_programs.quicksort import quicksort

# path: empty check → True → return []
def test_quicksort_empty():
    assert quicksort([]) == []

# path: empty check → False → single element → lesser=[], greater=[] → return [pivot]
def test_quicksort_single():
    assert quicksort([1]) == [1]

# path: empty check → False → two elements → pivot larger → lesser has element, greater empty
def test_quicksort_two_ascending():
    assert quicksort([1, 2]) == [1, 2]

# path: empty check → False → two elements → pivot smaller → lesser empty, greater has element
def test_quicksort_two_descending():
    assert quicksort([2, 1]) == [1, 2]

# path: empty check → False → multiple elements → all lesser (pivot is max)
def test_quicksort_pivot_is_max():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# path: empty check → False → multiple elements → all greater (pivot is min)
def test_quicksort_pivot_is_min():
    assert quicksort([1, 3, 2]) == [1, 2, 3]

# path: empty check → False → multiple elements → elements on both sides of pivot
def test_quicksort_mixed():
    assert quicksort([3, 1, 4, 1, 5, 9, 2, 6]) == [1, 1, 2, 3, 4, 5, 6, 9]

# path: empty check → False → duplicate elements equal to pivot → lesser=[], greater=[] (duplicates excluded)
def test_quicksort_all_duplicates():
    assert quicksort([5, 5, 5]) == [5, 5, 5]

# path: empty check → False → already sorted input → recursive calls with progressively smaller arrays
def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: empty check → False → reverse sorted input → recursive calls with progressively smaller arrays
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# path: empty check → False → negative numbers mixed with positives
def test_quicksort_negative_numbers():
    assert quicksort([-3, 1, -1, 2, 0]) == [-3, -1, 0, 1, 2]

# path: empty check → False → single element repeated with unique pivot
def test_quicksort_duplicates_with_unique():
    assert quicksort([2, 2, 1, 2, 3]) == [1, 2, 2, 2, 3]
```

```python
# test_whitebox_statement.py
from python_programs.quicksort import quicksort

# covers: empty list check (True branch), return []
def test_quicksort_empty():
    assert quicksort([]) == []

# covers: empty list check (False branch), pivot assignment,
# lesser/greater recursive calls, return lesser + [pivot] + greater
def test_quicksort_single_element():
    assert quicksort([1]) == [1]

# covers: all statements with multiple elements requiring actual partitioning
def test_quicksort_multiple_elements():
    assert quicksort([3, 1, 2]) == [1, 2, 3]

# covers: all statements with duplicates (duplicates are excluded from lesser and greater)
def test_quicksort_with_duplicates():
    assert quicksort([3, 3, 1, 2]) == [1, 2, 3, 3]

# covers: all statements with already sorted input
def test_quicksort_sorted_input():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# covers: all statements with reverse sorted input
def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

# covers: all statements ensuring greater branch is populated
def test_quicksort_lesser_and_greater_populated():
    assert quicksort([2, 1, 3]) == [1, 2, 3]
```
