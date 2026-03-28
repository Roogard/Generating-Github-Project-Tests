_(showing 10 of 88 failures)_

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.mergesort import mergesort

# --- Empty collection boundary ---

def test_mergesort_empty_array():
    arr = []
    result = mergesort(arr)
    assert result == []
    assert len(result) == 0

# --- Single element boundary ---

def test_mergesort_single_element():
    arr = [42]
    result = mergesort(arr)
    assert result == [42]
    assert len(result) == len(arr)

# --- Two elements already sorted ---

def test_mergesort_two_elements_sorted():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Two elements reverse sorted ---

def test_mergesort_two_elements_reverse():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Three elements (min size to exercise both split sides) ---

def test_mergesort_three_elements():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- All elements identical (duplicates must all be preserved) ---

def test_mergesort_all_duplicates():
    arr = [5, 5, 5, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Array with two duplicates at boundary ---

def test_mergesort_two_duplicate_elements():
    arr = [7, 7]
    result = mergesort(arr)
    assert result == [7, 7]
    assert len(result) == 2

# --- Already sorted array ---

def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Reverse sorted array ---

def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Array with duplicates mixed in ---

def test_mergesort_with_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Negative numbers boundary ---

def test_mergesort_all_negative():
    arr = [-3, -1, -4, -1, -5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Mixed negative and positive ---

def test_mergesort_negative_and_positive():
    arr = [-2, 3, -1, 0, 2, -3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Single negative number ---

def test_mergesort_single_negative():
    arr = [-1]
    result = mergesort(arr)
    assert result == [-1]
    assert len(result) == 1

# --- Large array (near upper practical boundary) ---

def test_mergesort_large_array():
    import random
    random.seed(0)
    arr = list(range(999, -1, -1))  # 1000 elements reversed
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Array with zero ---

def test_mergesort_contains_zero():
    arr = [0, -1, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# --- Array with only zeros ---

def test_mergesort_all_zeros():
    arr = [0, 0, 0]
    result = mergesort(arr)
    assert result == [0, 0, 0]
    assert len(result) == 3

# --- Property: result contains same multiset as input ---

def test_mergesort_preserves_all_elements_including_duplicates():
    arr = [4, 2, 4, 1, 3, 2]
    result = mergesort(arr)
    assert sorted(result) == sorted(arr)
    assert len(result) == len(arr)

# --- Two elements equal (boundary between strict and non-strict ordering) ---

def test_mergesort_two_equal_elements():
    arr = [3, 3]
    result = mergesort(arr)
    assert result == [3, 3]
    assert len(result) == 2
```

## Error Message(s)

### [FAILURE] test_mergesort_single_element (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:16: in test_mergesort_single_element
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_elements_sorted (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:24: in test_mergesort_two_elements_sorted
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_elements_reverse (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:32: in test_mergesort_two_elements_reverse
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_three_elements (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:40: in test_mergesort_three_elements
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_all_duplicates (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:48: in test_mergesort_all_duplicates
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_duplicate_elements (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:56: in test_mergesort_two_duplicate_elements
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_already_sorted (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:64: in test_mergesort_already_sorted
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_reverse_sorted (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:72: in test_mergesort_reverse_sorted
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_with_duplicates (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:80: in test_mergesort_with_duplicates
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_all_negative (type: blackbox_bva)
```
eval_output\28-03-2026_10-26\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:88: in test_mergesort_all_negative
    result = mergesort(arr)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmppsx9bm9y\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```
