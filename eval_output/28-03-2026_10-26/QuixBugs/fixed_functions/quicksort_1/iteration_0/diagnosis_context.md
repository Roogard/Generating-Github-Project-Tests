_(showing 10 of 28 failures)_

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

## Error Message(s)

### [FAILURE] test_two_equal_elements (type: blackbox_bva)
Assertion: assert result == sorted(arr)
Expected: [5, 5]
Actual:   [5]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:30: in test_two_equal_elements
    assert result == sorted(arr)
E   assert [5] == [5, 5]
E     
E     Right contains one more item: 5
E     Use -v to get more diff
```

### [FAILURE] test_all_equal_elements (type: blackbox_bva)
Assertion: assert result == sorted(arr)
Expected: [7, 7, 7, 7]
Actual:   [7]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:49: in test_all_equal_elements
    assert result == sorted(arr)
E   assert [7] == [7, 7, 7, 7]
E     
E     Right contains 3 more items, first extra item: 7
E     Use -v to get more diff
```

### [FAILURE] test_duplicates_with_pivot (type: blackbox_bva)
Assertion: assert result == sorted(arr)
Expected: [1, 2, 3, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:56: in test_duplicates_with_pivot
    assert result == sorted(arr)
E   assert [1, 2, 3] == [1, 2, 3, 3, 3]
E     
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_all_elements_same_as_pivot (type: blackbox_bva)
Assertion: assert result == sorted(arr)
Expected: [3, 3, 3]
Actual:   [3]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:93: in test_all_elements_same_as_pivot
    assert result == sorted(arr)
E   assert [3] == [3, 3, 3]
E     
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_single_duplicate_pair (type: blackbox_bva)
Assertion: assert result == sorted(arr)
Expected: [2, 2]
Actual:   [2]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:99: in test_single_duplicate_pair
    assert result == sorted(arr)
E   assert [2] == [2, 2]
E     
E     Right contains one more item: 2
E     Use -v to get more diff
```

### [FAILURE] test_unsorted_distinct_elements (type: blackbox_ecp)
Assertion: assert result == sorted(arr)
Expected: [1, 1, 2, 3, 4, 5, ...]
Actual:   [1, 2, 3, 4, 5, 6, ...]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:35: in test_unsorted_distinct_elements
    assert result == sorted(arr)
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 1, 2, 3, 4, 5, ...]
E     
E     At index 1 diff: 2 != 1
E     Right contains one more item: 9
E     Use -v to get more diff
```

### [FAILURE] test_duplicate_elements (type: blackbox_ecp)
Assertion: assert result == sorted(arr)
Expected: [1, 2, 3, 5, 5, 5]
Actual:   [1, 2, 3, 5]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:43: in test_duplicate_elements
    assert result == sorted(arr)
E   assert [1, 2, 3, 5] == [1, 2, 3, 5, 5, 5]
E     
E     Right contains 2 more items, first extra item: 5
E     Use -v to get more diff
```

### [FAILURE] test_all_identical_elements (type: blackbox_ecp)
Assertion: assert result == sorted(arr)
Expected: [7, 7, 7, 7]
Actual:   [7]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:51: in test_all_identical_elements
    assert result == sorted(arr)
E   assert [7] == [7, 7, 7, 7]
E     
E     Right contains 3 more items, first extra item: 7
E     Use -v to get more diff
```

### [FAILURE] test_negative_numbers (type: blackbox_ecp)
Assertion: assert result == sorted(arr)
Expected: [-5, -4, -3, -1, -1]
Actual:   [-5, -4, -3, -1]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:58: in test_negative_numbers
    assert result == sorted(arr)
E   assert [-5, -4, -3, -1] == [-5, -4, -3, -1, -1]
E     
E     Right contains one more item: -1
E     Use -v to get more diff
```

### [FAILURE] test_two_identical_elements (type: blackbox_ecp)
Assertion: assert result == sorted(arr)
Expected: [4, 4]
Actual:   [4]
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:73: in test_two_identical_elements
    assert result == sorted(arr)
E   assert [4] == [4, 4]
E     
E     Right contains one more item: 4
E     Use -v to get more diff
```
