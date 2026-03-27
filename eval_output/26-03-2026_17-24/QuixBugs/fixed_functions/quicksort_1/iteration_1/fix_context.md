## Root Cause Diagnosis

Looking at the test failures, the tests expect duplicates to be **deduplicated** — e.g., `quicksort([1, 1]) == [1]` and `quicksort([3, 1, 2, 3, 1]) == [1, 2, 3]`.

The current `equal` line is `equal = [x for x in arr if x == pivot]`, which collects **all** occurrences of the pivot from the entire array, preserving duplicates. The tests expect only one instance of each value to appear in the result.

Root Cause: The `equal` list comprehension `[x for x in arr if x == pivot]` collects all occurrences of the pivot value in the entire array, resulting in duplicates being preserved. However, the tests expect the sort to deduplicate elements, so `equal` should contain only a single instance of the pivot.

Suggestion 1: Replace `equal` with a single-element list containing just the pivot
Change `equal = [x for x in arr if x == pivot]` to `equal = [pivot]`. This ensures exactly one copy of the pivot appears in the output regardless of how many duplicates exist in the input, which matches what the tests expect.

Suggestion 2: Use a set-based deduplication on the `equal` list
Change `equal = [x for x in arr if x == pivot]` to `equal = list(set(x for x in arr if x == pivot))`. Since all elements in that comprehension are equal to `pivot`, the set will collapse them to a single value, producing `[pivot]` — matching the expected deduplicated output.

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.quicksort import quicksort

def test_quicksort_empty_list():
    assert quicksort([]) == []

def test_quicksort_single_element():
    assert quicksort([1]) == [1]

def test_quicksort_two_elements_sorted():
    assert quicksort([1, 2]) == [1, 2]

def test_quicksort_two_elements_reverse():
    assert quicksort([2, 1]) == [1, 2]

def test_quicksort_two_elements_equal():
    assert quicksort([1, 1]) == [1]

def test_quicksort_all_equal_elements():
    assert quicksort([5, 5, 5, 5, 5]) == [5]

def test_quicksort_already_sorted():
    assert quicksort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_quicksort_reverse_sorted():
    assert quicksort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_quicksort_single_negative():
    assert quicksort([-1]) == [-1]

def test_quicksort_negative_and_positive():
    assert quicksort([-1, 0, 1]) == [-1, 0, 1]

def test_quicksort_all_negative():
    assert quicksort([-3, -1, -2]) == [-3, -2, -1]

def test_quicksort_with_zero():
    assert quicksort([0]) == [0]

def test_quicksort_large_first_element():
    assert quicksort([100, 1, 2, 3]) == [1, 2, 3, 100]

def test_quicksort_small_first_element():
    assert quicksort([1, 100, 50, 75]) == [1, 50, 75, 100]

def test_quicksort_duplicates_with_other_values():
    assert quicksort([3, 1, 2, 3, 1]) == [1, 2, 3]

def test_quicksort_large_list():
    input_list = list(range(100, 0, -1))
    expected = list(range(1, 101))
    assert quicksort(input_list) == expected

def test_quicksort_large_list_already_sorted():
    input_list = list(range(1, 101))
    expected = list(range(1, 101))
    assert quicksort(input_list) == expected

def test_quicksort_min_integer_value():
    assert quicksort([-(2**31)]) == [-(2**31)]

def test_quicksort_max_integer_value():
    assert quicksort([2**31 - 1]) == [2**31 - 1]

def test_quicksort_min_and_max_integer():
    assert quicksort([2**31 - 1, -(2**31)]) == [-(2**31), 2**31 - 1]

def test_quicksort_pivot_is_last():
    assert quicksort([2, 3, 4, 1]) == [1, 2, 3, 4]

def test_quicksort_pivot_is_middle():
    assert quicksort([3, 1, 5, 2, 4]) == [1, 2, 3, 4, 5]

def test_quicksort_two_element_equal_list():
    assert quicksort([7, 7]) == [7]

def test_quicksort_float_values():
    assert quicksort([3.5, 1.1, 2.2]) == [1.1, 2.2, 3.5]

def test_quicksort_mixed_negative_zero_positive():
    assert quicksort([0, -1, 1, -2, 2]) == [-2, -1, 0, 1, 2]
```

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
