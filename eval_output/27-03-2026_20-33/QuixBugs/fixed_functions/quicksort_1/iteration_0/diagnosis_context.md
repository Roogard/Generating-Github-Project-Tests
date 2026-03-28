_(showing 10 of 19 failures)_

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

## Error Message(s)

### [FAILURE] test_quicksort_two_elements_equal (type: blackbox_bva)
Assertion: assert result == sorted([5, 5])
Expected: [5, 5]
Actual:   [5]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:26: in test_quicksort_two_elements_equal
    assert result == sorted([5, 5])
E   assert [5] == [5, 5]
E     
E     Right contains one more item: 5
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_all_equal_elements (type: blackbox_bva)
Assertion: assert result == sorted(inp)
Expected: [7, 7, 7, 7, 7]
Actual:   [7]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:44: in test_quicksort_all_equal_elements
    assert result == sorted(inp)
E   assert [7] == [7, 7, 7, 7, 7]
E     
E     Right contains 4 more items, first extra item: 7
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_with_duplicates (type: blackbox_bva)
Assertion: assert result == sorted(inp)
Expected: [1, 1, 2, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:50: in test_quicksort_with_duplicates
    assert result == sorted(inp)
E   assert [1, 2, 3] == [1, 1, 2, 3, 3]
E     
E     At index 1 diff: 2 != 1
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_preserves_multiset (type: blackbox_bva)
Assertion: assert sorted(result) == sorted(inp)
Expected: [1, 2, 2, 4, 4, 7]
Actual:   [1, 2, 4, 7]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:102: in test_quicksort_preserves_multiset
    assert sorted(result) == sorted(inp)
E   assert [1, 2, 4, 7] == [1, 2, 2, 4, 4, 7]
E     
E     At index 2 diff: 4 != 2
E     Right contains 2 more items, first extra item: 4
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_two_element_equal_boundary (type: blackbox_bva)
Assertion: assert result == sorted(inp)
Expected: [0, 0]
Actual:   [0]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:107: in test_quicksort_two_element_equal_boundary
    assert result == sorted(inp)
E   assert [0] == [0, 0]
E     
E     Right contains one more item: 0
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_zeros_and_ones (type: blackbox_bva)
Assertion: assert result == sorted(inp)
Expected: [0, 0, 0, 1, 1, 1]
Actual:   [0, 1]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:113: in test_quicksort_zeros_and_ones
    assert result == sorted(inp)
E   assert [0, 1] == [0, 0, 0, 1, 1, 1]
E     
E     At index 1 diff: 1 != 0
E     Right contains 4 more items, first extra item: 0
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_unsorted_distinct_positive (type: blackbox_ecp)
Assertion: assert result == sorted(input_list)
Expected: [1, 1, 2, 3, 4, 5, ...]
Actual:   [1, 2, 3, 4, 5, 6, ...]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:34: in test_quicksort_unsorted_distinct_positive
    assert result == sorted(input_list)
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 1, 2, 3, 4, 5, ...]
E     
E     At index 1 diff: 2 != 1
E     Right contains one more item: 9
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_duplicate_elements (type: blackbox_ecp)
Assertion: assert result == sorted(input_list)
Expected: [1, 1, 2, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:59: in test_quicksort_duplicate_elements
    assert result == sorted(input_list)
E   assert [1, 2, 3] == [1, 1, 2, 3, 3]
E     
E     At index 1 diff: 2 != 1
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_all_identical (type: blackbox_ecp)
Assertion: assert result == sorted(input_list)
Expected: [7, 7, 7, 7]
Actual:   [7]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_ecp.py:66: in test_quicksort_all_identical
    assert result == sorted(input_list)
E   assert [7] == [7, 7, 7, 7]
E     
E     Right contains 3 more items, first extra item: 7
E     Use -v to get more diff
```

### [FAILURE] test_duplicates_preserved (type: blackbox_mutation)
Assertion: assert result == [3, 3, 3]
Expected: [3, 3, 3]
Actual:   [3]
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\quicksort_1\test_blackbox_mutation.py:7: in test_duplicates_preserved
    assert result == [3, 3, 3]
E   assert [3] == [3, 3, 3]
E     
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```
