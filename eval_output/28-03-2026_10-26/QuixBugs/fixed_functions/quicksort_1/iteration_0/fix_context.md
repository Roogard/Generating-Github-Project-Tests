## Root Cause Diagnosis

Root Cause: The `greater` list comprehension uses `x > pivot` (strict greater than), and the `lesser` list comprehension uses `x < pivot` (strict less than). This means elements equal to the pivot (other than the pivot itself) are excluded from both partitions and are dropped entirely, causing duplicates to be lost from the output.

Suggestion 1: Include duplicates in the `greater` partition
Change the `greater` list comprehension from `x > pivot` to `x >= pivot` so that elements equal to the pivot are included in the greater partition and recursively sorted. This ensures no elements are dropped.

Suggestion 2: Include duplicates in the `lesser` partition
Change the `lesser` list comprehension from `x < pivot` to `x <= pivot` so that elements equal to the pivot are included in the lesser partition and recursively sorted. This also ensures no elements are dropped.

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.quicksort import quicksort

def test_empty_list():
    result = quicksort([])
    assert result == []
    assert len(result) == 0

def test_single_element():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

def test_two_elements_sorted():
    arr = [1, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_two_elements_reverse_sorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_two_equal_elements():
    arr = [5, 5]
    result = quicksort(arr)
    # A correct sort must preserve all elements including duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_all_equal_elements():
    arr = [7, 7, 7, 7]
    result = quicksort(arr)
    # A correct sort must preserve all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_duplicates_with_pivot():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    # A correct sort preserves all elements including duplicates of the pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_negative_numbers():
    arr = [-1, -3, -2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_mixed_negative_and_positive():
    arr = [-5, 0, 3, -2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_large_list_boundary():
    arr = list(range(100, 0, -1))
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_pivot_is_max_element():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_pivot_is_min_element():
    arr = [1, 5, 4, 3, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_all_elements_same_as_pivot():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # A correct sort must return all elements, including all copies of the pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_single_duplicate_pair():
    arr = [2, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

def test_no_nested_lists_in_result():
    arr = [4, 2, 7, 1, 9]
    result = quicksort(arr)
    assert all(not isinstance(x, list) for x in result)
    assert result == sorted(arr)
```

```python
# test_blackbox_ecp.py
import pytest
from python_programs.quicksort import quicksort

# Valid equivalence class: empty list
def test_empty_list():
    result = quicksort([])
    assert result == []

# Valid equivalence class: single element list
def test_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# Valid equivalence class: already sorted list
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: reverse sorted list
def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: unsorted list with distinct elements
def test_unsorted_distinct_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    # A correct quicksort MUST preserve all elements including duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with duplicate elements
def test_duplicate_elements():
    arr = [5, 3, 5, 1, 5, 2]
    result = quicksort(arr)
    # A correct quicksort MUST preserve all duplicate values, not drop them
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: all identical elements
def test_all_identical_elements():
    arr = [7, 7, 7, 7]
    result = quicksort(arr)
    # A correct quicksort MUST return all elements including duplicates of pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with negative numbers
def test_negative_numbers():
    arr = [-3, -1, -4, -1, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with mixed positive and negative numbers
def test_mixed_positive_negative():
    arr = [-2, 3, -1, 0, 4, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: list with a single repeated pair
def test_two_identical_elements():
    arr = [4, 4]
    result = quicksort(arr)
    # A correct quicksort MUST preserve both copies
    assert result == sorted(arr)
    assert len(result) == len(arr)
```

```python
# test_blackbox_mutation.py
from python_programs.quicksort import quicksort

# catches: "x < pivot" mutated to "x <= pivot" (drops equal elements into lesser, not preserving duplicates correctly)
def test_duplicates_preserved():
    arr = [3, 3, 3]
    result = quicksort(arr)
    assert result == [3, 3, 3]

# catches: "x > pivot" mutated to "x >= pivot" (drops pivot or duplicates from result)
def test_duplicates_two_elements():
    arr = [2, 2]
    result = quicksort(arr)
    assert result == [2, 2]

# catches: "x < pivot" mutated to "x <= pivot" (pivot would appear twice, losing one instance)
def test_duplicate_with_other_elements():
    arr = [1, 2, 2, 3]
    result = quicksort(arr)
    assert result == [1, 2, 2, 3]

# catches: lesser + [pivot] + greater order mutation (e.g., greater + [pivot] + lesser)
def test_basic_sort_order():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3]

# catches: arr[0] mutated to arr[1] as pivot selection (wrong variable/index)
def test_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]

# catches: "not arr" mutated to "arr" (base case inverted - recurses forever or returns wrong)
def test_empty_list():
    result = quicksort([])
    assert result == []

# catches: arr[1:] mutated to arr[:] (includes pivot in recursive calls, infinite recursion or wrong result)
def test_sorted_result_excludes_no_elements():
    arr = [5, 3, 8, 1, 9, 2]
    result = quicksort(arr)
    assert result == [1, 2, 3, 5, 8, 9]

# catches: "lesser + [pivot] + greater" mutated to "lesser + greater" (drops pivot)
def test_all_elements_preserved():
    arr = [4, 2, 7, 1, 5]
    result = quicksort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: "x < pivot" mutated to "x > pivot" (lesser and greater swapped, wrong order)
def test_reverse_sorted_input():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: off-by-one in arr[1:] mutated to arr[0:] or arr[2:]
def test_two_element_unsorted():
    arr = [2, 1]
    result = quicksort(arr)
    assert result == [1, 2]

# catches: multiset property - no elements dropped or added
def test_multiset_preserved_with_duplicates():
    arr = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    result = quicksort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# catches: "x < pivot" mutated to "x <= pivot" causing duplicates of pivot to be misplaced
def test_pivot_duplicates_correct_position():
    arr = [3, 1, 3, 2, 3]
    result = quicksort(arr)
    assert result == [1, 2, 3, 3, 3]

# catches: "return []" mutated to "return arr" (base case returns non-empty)
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == [1, 2, 3, 4, 5]

# catches: "lesser + [pivot] + greater" mutated to "[pivot] + lesser + greater"
def test_negative_numbers():
    arr = [-3, -1, -2]
    result = quicksort(arr)
    assert result == [-3, -2, -1]

# catches: property - result must be non-decreasing
def test_sorted_property_holds():
    arr = [10, 3, 7, 1, 8, 5, 2, 9, 4, 6]
    result = quicksort(arr)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]
```

```python
# test_whitebox_block.py
from python_programs.quicksort import quicksort

# covers: block 1 (empty array, returns [])
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: block 2 (non-empty array, pivot selected, lesser/greater recursion, return)
# single element: lesser and greater are both empty
def test_quicksort_single():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: block 2 with non-trivial lesser and greater partitions
def test_quicksort_multiple_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with already sorted input (greater always empty in recursion)
def test_quicksort_sorted_input():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with reverse sorted input (lesser always empty in recursion)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with duplicate elements (elements equal to pivot are dropped from both partitions)
# a correct quicksort must preserve all elements including duplicates
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # a correct quicksort should preserve all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 with negative numbers
def test_quicksort_negative_numbers():
    arr = [-5, -1, -3, 0, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: block 2 ensuring all values are present in output (multiset preserved)
def test_quicksort_preserves_elements():
    arr = [10, 7, 8, 9, 1, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert sorted(result) == sorted(arr)
```

```python
# test_whitebox_condition.py
from python_programs.quicksort import quicksort

# condition: not arr → True (empty list)
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# condition: not arr → False (non-empty list), x < pivot → True, x > pivot → False
def test_quicksort_elements_less_than_pivot():
    arr = [3, 1, 2]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False (non-empty list), x < pivot → False, x > pivot → True
def test_quicksort_elements_greater_than_pivot():
    arr = [1, 3, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (mixed)
def test_quicksort_mixed_elements():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    # A correct quicksort should return all elements in sorted order
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → False, x > pivot → False (duplicates of pivot)
def test_quicksort_duplicates():
    arr = [5, 5, 5]
    result = quicksort(arr)
    # A correct quicksort must preserve all duplicate elements
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (already sorted)
def test_quicksort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True, x > pivot → True (reverse sorted)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False with single element (no recursive sub-conditions triggered)
def test_quicksort_single_element():
    arr = [42]
    result = quicksort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (negative numbers)
def test_quicksort_negative_numbers():
    arr = [-3, -1, -4, -1, -5, -9, -2, -6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot → True and x > pivot → True (mixed negatives and positives)
def test_quicksort_mixed_negative_positive():
    arr = [3, -1, 4, -1, 5, -9, 2, -6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: not arr → False, x < pivot: True and False, x > pivot: True and False (with duplicates mixed)
def test_quicksort_duplicates_mixed():
    arr = [4, 2, 4, 1, 4, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all elements including duplicates of pivot
    assert result == sorted(arr)
    assert len(result) == len(arr)
```

```python
# test_whitebox_path.py
import pytest
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

# path: empty check → False → 1 recursive call each side with 1 element (ascending pair)
def test_quicksort_two_elements_ascending():
    result = quicksort([1, 2])
    assert result == sorted([1, 2])
    assert len(result) == 2

# path: empty check → False → 1 recursive call each side with 1 element (descending pair)
def test_quicksort_two_elements_descending():
    result = quicksort([2, 1])
    assert result == sorted([2, 1])
    assert len(result) == 2

# path: empty check → False → all elements go to lesser (strictly descending array)
def test_quicksort_all_lesser():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → all elements go to greater (strictly ascending array)
def test_quicksort_all_greater():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → elements split across lesser and greater (mixed array)
def test_quicksort_mixed():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    # A correct quicksort preserves all elements including duplicates
    assert len(result) == len(arr)

# path: empty check → False → duplicates of pivot exist (dropped by x < pivot and x > pivot)
def test_quicksort_with_duplicates():
    arr = [3, 3, 3]
    result = quicksort(arr)
    # A correct quicksort must preserve all duplicate elements
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → duplicates mixed with other values
def test_quicksort_duplicates_mixed():
    arr = [2, 2, 1, 3, 2]
    result = quicksort(arr)
    # A correct quicksort preserves all duplicates
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → negative numbers present
def test_quicksort_negative_numbers():
    arr = [-3, -1, -4, -1, -5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → mixed negative and positive numbers
def test_quicksort_negative_and_positive():
    arr = [-2, 3, 0, -1, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# path: empty check → False → single element array that results after filtering (pivot == only remaining)
def test_quicksort_two_equal_elements():
    arr = [7, 7]
    result = quicksort(arr)
    # A correct quicksort must preserve both copies
    assert result == sorted(arr)
    assert len(result) == len(arr)
```

```python
# test_whitebox_statement.py
from python_programs.quicksort import quicksort

# covers: if not arr -> True, return []
def test_quicksort_empty():
    result = quicksort([])
    assert result == []

# covers: if not arr -> False, pivot assignment, lesser, greater, return lesser+[pivot]+greater
# with a single element: lesser and greater are both empty lists (base case reached recursively)
def test_quicksort_single():
    result = quicksort([42])
    assert result == [42]
    assert len(result) == 1

# covers: all statements with multiple elements requiring recursive calls
# lesser and greater sublists are non-empty, exercising the list comprehensions and recursion
def test_quicksort_multiple():
    arr = [3, 1, 4, 1, 5, 9, 2, 6]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(set(arr))  # duplicates dropped by > and < (property of this impl)

# covers: all statements with already-sorted input
def test_quicksort_sorted_input():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: all statements with reverse-sorted input (maximizes recursion depth on lesser)
def test_quicksort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: lesser list comprehension produces non-empty list, greater is empty
def test_quicksort_all_lesser():
    arr = [5, 1, 2, 3, 4]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: greater list comprehension produces non-empty list, lesser is empty
def test_quicksort_all_greater():
    arr = [1, 2, 3, 4, 5]
    result = quicksort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
```
