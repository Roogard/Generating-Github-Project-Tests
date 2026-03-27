_(showing 10 of 21 failures)_

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

## Error Message(s)

### [FAILURE] test_quicksort_all_duplicates (type: blackbox_bva)
Assertion: assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]
Expected: [3, 3, 3, 3]
Actual:   [3]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:22: in test_quicksort_all_duplicates
    assert quicksort([3, 3, 3, 3]) == [3, 3, 3, 3]
E   assert [3] == [3, 3, 3, 3]
E     
E     Right contains 3 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_two_duplicates (type: blackbox_bva)
Assertion: assert quicksort([2, 2]) == [2, 2]
Expected: [2, 2]
Actual:   [2]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:25: in test_quicksort_two_duplicates
    assert quicksort([2, 2]) == [2, 2]
E   assert [2] == [2, 2]
E     
E     Right contains one more item: 2
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_duplicates_with_other_elements (type: blackbox_bva)
Assertion: assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]
Expected: [1, 2, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:28: in test_quicksort_duplicates_with_other_elements
    assert quicksort([3, 1, 3, 2]) == [1, 2, 3, 3]
E   assert [1, 2, 3] == [1, 2, 3, 3]
E     
E     Right contains one more item: 3
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_zeros_and_positives (type: blackbox_bva)
Assertion: assert quicksort([0, 1, 0]) == [0, 0, 1]
Expected: [0, 0, 1]
Actual:   [0, 1]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:46: in test_quicksort_zeros_and_positives
    assert quicksort([0, 1, 0]) == [0, 0, 1]
E   assert [0, 1] == [0, 0, 1]
E     
E     At index 1 diff: 1 != 0
E     Right contains one more item: 1
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_large_list_boundary (type: blackbox_bva)
Assertion: assert quicksort(arr) == list(range(0, 1000))
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:50: in test_quicksort_large_list_boundary
    assert quicksort(arr) == list(range(0, 1000))
           ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
  ...truncated...
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_quicksort_large_list_already_sorted (type: blackbox_bva)
Assertion: assert quicksort(arr) == list(range(0, 1000))
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:54: in test_quicksort_large_list_already_sorted
    assert quicksort(arr) == list(range(0, 1000))
           ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
  ...truncated...
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:7: in quicksort
    greater = quicksort([x for x in arr[1:] if x > pivot])
              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpst9jchh7\python_programs\quicksort.py:6: in quicksort
    lesser = quicksort([x for x in arr[1:] if x < pivot])
                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_quicksort_large_single_value_repeated (type: blackbox_bva)
Assertion: assert quicksort(arr) == [7] * 100
Expected: [7, 7, 7, 7, 7, 7, ...]
Actual:   [7]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:58: in test_quicksort_large_single_value_repeated
    assert quicksort(arr) == [7] * 100
E   assert [7] == [7, 7, 7, 7, 7, 7, ...]
E     
E     Right contains 99 more items, first extra item: 7
E     Use -v to get more diff
```

### [FAILURE] test_quicksort_two_elements_equal (type: blackbox_bva)
Assertion: assert quicksort([5, 5]) == [5, 5]
Expected: [5, 5]
Actual:   [5]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_bva.py:67: in test_quicksort_two_elements_equal
    assert quicksort([5, 5]) == [5, 5]
E   assert [5] == [5, 5]
E     
E     Right contains one more item: 5
E     Use -v to get more diff
```

### [FAILURE] test_duplicate_elements_preserved (type: blackbox_mutation)
Assertion: assert result == [1, 2, 3, 3, 3]
Expected: [1, 2, 3, 3, 3]
Actual:   [1, 2, 3]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_mutation.py:14: in test_duplicate_elements_preserved
    assert result == [1, 2, 3, 3, 3]
E   assert [1, 2, 3] == [1, 2, 3, 3, 3]
E     
E     Right contains 2 more items, first extra item: 3
E     Use -v to get more diff
```

### [FAILURE] test_order_is_ascending (type: blackbox_mutation)
Assertion: assert result == [1, 1, 2, 3, 4, 5, 6, 9]
Expected: [1, 1, 2, 3, 4, 5, ...]
Actual:   [1, 2, 3, 4, 5, 6, ...]
```
eval_output\26-03-2026_20-05\QuixBugs\generated_tests\quicksort_1\test_blackbox_mutation.py:27: in test_order_is_ascending
    assert result == [1, 1, 2, 3, 4, 5, 6, 9]
E   assert [1, 2, 3, 4, 5, 6, ...] == [1, 1, 2, 3, 4, 5, ...]
E     
E     At index 1 diff: 2 != 1
E     Right contains one more item: 9
E     Use -v to get more diff
```
