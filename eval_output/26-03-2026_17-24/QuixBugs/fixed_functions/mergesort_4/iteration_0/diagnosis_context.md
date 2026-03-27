_(showing 10 of 97 failures)_

## Trigger Test(s)

```python
# test_blackbox_bva.py
from python_programs.mergesort import mergesort

def test_mergesort_empty_array():
    assert mergesort([]) == []

def test_mergesort_single_element():
    assert mergesort([42]) == [42]

def test_mergesort_two_elements_sorted():
    assert mergesort([1, 2]) == [1, 2]

def test_mergesort_two_elements_unsorted():
    assert mergesort([2, 1]) == [1, 2]

def test_mergesort_two_equal_elements():
    assert mergesort([5, 5]) == [5, 5]

def test_mergesort_three_elements_sorted():
    assert mergesort([1, 2, 3]) == [1, 2, 3]

def test_mergesort_three_elements_reverse_sorted():
    assert mergesort([3, 2, 1]) == [1, 2, 3]

def test_mergesort_three_elements_middle_boundary():
    assert mergesort([2, 1, 3]) == [1, 2, 3]

def test_mergesort_all_equal_elements():
    assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]

def test_mergesort_already_sorted():
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

def test_mergesort_reverse_sorted():
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]

def test_mergesort_single_negative_element():
    assert mergesort([-1]) == [-1]

def test_mergesort_negative_and_positive():
    assert mergesort([-1, 0, 1]) == [-1, 0, 1]

def test_mergesort_negative_boundary_values():
    assert mergesort([0, -1]) == [-1, 0]

def test_mergesort_min_int_boundary():
    import sys
    assert mergesort([sys.maxsize, -sys.maxsize]) == [-sys.maxsize, sys.maxsize]

def test_mergesort_min_int_single():
    import sys
    assert mergesort([-sys.maxsize]) == [-sys.maxsize]

def test_mergesort_max_int_single():
    import sys
    assert mergesort([sys.maxsize]) == [sys.maxsize]

def test_mergesort_large_array():
    arr = list(range(1000, 0, -1))
    assert mergesort(arr) == list(range(1, 1001))

def test_mergesort_large_array_already_sorted():
    arr = list(range(1, 1001))
    assert mergesort(arr) == list(range(1, 1001))

def test_mergesort_two_elements_equal():
    assert mergesort([3, 3]) == [3, 3]

def test_mergesort_left_boundary_element_smaller():
    assert mergesort([1, 3, 2]) == [1, 2, 3]

def test_mergesort_right_boundary_element_smaller():
    assert mergesort([3, 1, 2]) == [1, 2, 3]

def test_mergesort_duplicates_with_boundary():
    assert mergesort([2, 2, 1, 1]) == [1, 1, 2, 2]

def test_mergesort_preserves_stability_boundary():
    assert mergesort([1, 1, 1]) == [1, 1, 1]
```

## Error Message(s)

### [FAILURE] test_mergesort_single_element (type: blackbox_bva)
Assertion: assert mergesort([42]) == [42]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:7: in test_mergesort_single_element
    assert mergesort([42]) == [42]
           ^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_elements_sorted (type: blackbox_bva)
Assertion: assert mergesort([1, 2]) == [1, 2]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:10: in test_mergesort_two_elements_sorted
    assert mergesort([1, 2]) == [1, 2]
           ^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_elements_unsorted (type: blackbox_bva)
Assertion: assert mergesort([2, 1]) == [1, 2]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:13: in test_mergesort_two_elements_unsorted
    assert mergesort([2, 1]) == [1, 2]
           ^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_two_equal_elements (type: blackbox_bva)
Assertion: assert mergesort([5, 5]) == [5, 5]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:16: in test_mergesort_two_equal_elements
    assert mergesort([5, 5]) == [5, 5]
           ^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_three_elements_sorted (type: blackbox_bva)
Assertion: assert mergesort([1, 2, 3]) == [1, 2, 3]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:19: in test_mergesort_three_elements_sorted
    assert mergesort([1, 2, 3]) == [1, 2, 3]
           ^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_three_elements_reverse_sorted (type: blackbox_bva)
Assertion: assert mergesort([3, 2, 1]) == [1, 2, 3]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:22: in test_mergesort_three_elements_reverse_sorted
    assert mergesort([3, 2, 1]) == [1, 2, 3]
           ^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_three_elements_middle_boundary (type: blackbox_bva)
Assertion: assert mergesort([2, 1, 3]) == [1, 2, 3]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:25: in test_mergesort_three_elements_middle_boundary
    assert mergesort([2, 1, 3]) == [1, 2, 3]
           ^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_all_equal_elements (type: blackbox_bva)
Assertion: assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:28: in test_mergesort_all_equal_elements
    assert mergesort([7, 7, 7, 7]) == [7, 7, 7, 7]
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_already_sorted (type: blackbox_bva)
Assertion: assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:31: in test_mergesort_already_sorted
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```

### [FAILURE] test_mergesort_reverse_sorted (type: blackbox_bva)
Assertion: assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
```
eval_output\26-03-2026_17-24\QuixBugs\generated_tests\mergesort_4\test_blackbox_bva.py:34: in test_mergesort_reverse_sorted
    assert mergesort([5, 4, 3, 2, 1]) == [1, 2, 3, 4, 5]
           ^^^^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
  ...truncated...
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:22: in mergesort
    right = mergesort(arr[middle:])
            ^^^^^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Local\Temp\tmp16f0wnsl\python_programs\mergesort.py:21: in mergesort
    left = mergesort(arr[:middle])
           ^^^^^^^^^^^^^^^^^^^^^^^
E   RecursionError: maximum recursion depth exceeded
```
