_(showing 10 of 92 failures)_

## Trigger Test(s)

```python
# test_blackbox_bva.py
import pytest
from python_programs.mergesort import mergesort

def test_empty_array():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

def test_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

def test_two_elements_sorted():
    inp = [1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_two_elements_reverse_sorted():
    inp = [2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_three_elements():
    inp = [3, 1, 2]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_already_sorted():
    inp = [1, 2, 3, 4, 5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_reverse_sorted():
    inp = [5, 4, 3, 2, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_all_equal_elements():
    inp = [7, 7, 7, 7]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_duplicate_elements():
    inp = [3, 1, 2, 3, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_negative_numbers():
    inp = [-3, -1, -4, -1, -5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_mixed_negative_and_positive():
    inp = [-2, 3, -1, 0, 4, -5]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_large_array():
    import random
    random.seed(0)
    inp = random.sample(range(10000), 1000)
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_large_array_boundary_size_two_power():
    inp = list(range(16, 0, -1))
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_odd_length_array():
    inp = [5, 3, 8, 1, 9]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_even_length_array():
    inp = [5, 3, 8, 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_min_max_integers():
    inp = [2**31 - 1, -(2**31), 0, 2**31 - 2, -(2**31) + 1]
    result = mergesort(inp)
    assert result == sorted(inp)
    assert len(result) == len(inp)

def test_preserves_all_elements_no_drops():
    inp = [4, 2, 2, 8, 5, 5, 1]
    result = mergesort(inp)
    assert sorted(result) == sorted(inp)
    assert len(result) == len(inp)

def test_result_is_non_nested():
    inp = [3, 1, 2]
    result = mergesort(inp)
    assert all(not isinstance(x, list) for x in result)

def test_two_elements_equal():
    inp = [5, 5]
    result = mergesort(inp)
    assert result == [5, 5]
    assert len(result) == 2

def test_single_negative_element():
    result = mergesort([-1])
    assert result == [-1]
    assert len(result) == 1

def test_single_zero():
    result = mergesort([0])
    assert result == [0]
    assert len(result) == 1
```

## Error Message(s)

### [FAILURE] test_single_element (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:10: in test_single_element
    result = mergesort([42])
             ^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_two_elements_sorted (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:16: in test_two_elements_sorted
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_two_elements_reverse_sorted (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:22: in test_two_elements_reverse_sorted
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_three_elements (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:28: in test_three_elements
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_already_sorted (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:34: in test_already_sorted
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_reverse_sorted (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:40: in test_reverse_sorted
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_all_equal_elements (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:46: in test_all_equal_elements
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_duplicate_elements (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:52: in test_duplicate_elements
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_negative_numbers (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:58: in test_negative_numbers
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mixed_negative_and_positive (type: blackbox_bva)
```
eval_output\27-03-2026_20-33\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:64: in test_mixed_negative_and_positive
    result = mergesort(inp)
             ^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmpg4u_3tdm\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```
