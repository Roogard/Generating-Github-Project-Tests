## Root Cause Diagnosis

Root Cause: The base case on line 15 only returns when `len(arr) == 0`, but it fails to handle the single-element case (`len(arr) == 1`). When a single-element array is passed, `middle = 1 // 2 = 0`, so `arr[middle:]` equals the full array again, causing infinite recursion on the `right = mergesort(arr[middle:])` call.

Suggestion 1: Change the base case to also handle single-element arrays
Change the condition `if len(arr) == 0` to `if len(arr) <= 1` on line 15. This ensures that both empty arrays and single-element arrays are returned immediately without further recursion, which is the correct base case for mergesort.

Suggestion 2: Change the base case to check length less than 2
Replace `if len(arr) == 0` with `if len(arr) < 2` on line 15. This is semantically equivalent to suggestion 1 but uses a slightly different comparison, ensuring that any array with fewer than 2 elements is returned as-is without attempting to split and recurse further.

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

```python
# test_blackbox_ecp.py
import pytest
from python_programs.mergesort import mergesort

# Valid equivalence class: single-element array (already sorted, trivial)
def test_single_element():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# Valid equivalence class: already sorted array
def test_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert all(not isinstance(x, list) for x in result)

# Valid equivalence class: reverse sorted array
def test_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with duplicate elements
def test_with_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with all identical elements
def test_all_identical():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with negative numbers
def test_negative_numbers():
    arr = [-3, -1, -7, -2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with mixed positive and negative numbers
def test_mixed_positive_negative():
    arr = [3, -1, 0, -5, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: array with two elements (smallest non-trivial merge)
def test_two_elements():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# Valid equivalence class: empty array
def test_empty_array():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# Valid equivalence class: array with floating point numbers
def test_float_elements():
    arr = [3.14, 1.41, 2.71, 0.57]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# Valid equivalence class: large array (stress test for recursion correctness)
def test_large_array():
    import random
    random.seed(0)
    arr = random.sample(range(1000), 100)
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    # Verify no elements dropped or added
    assert sorted(result) == sorted(arr)
```

```python
# test_blackbox_mutation.py
from python_programs.mergesort import mergesort

# catches: "left[i] <= right[j]" mutated to "left[i] < right[j]" (equal elements handled wrong)
def test_equal_elements_preserved():
    result = mergesort([3, 3, 3])
    assert result == [3, 3, 3]

# catches: duplicate elements dropped due to wrong comparison
def test_duplicates_across_halves():
    result = mergesort([2, 1, 2, 1])
    assert result == [1, 1, 2, 2]

# catches: "len(arr) == 0" mutated to "len(arr) <= 0" or "len(arr) < 1" — base case off-by-one
def test_single_element():
    result = mergesort([42])
    assert result == [42]

# catches: base case "== 0" mutated to "== 1" — single element never recurses
def test_two_elements_sorted():
    result = mergesort([2, 1])
    assert result == [1, 2]

# catches: "== 0" mutated to "!= 0" — always returns early
def test_empty_list():
    result = mergesort([])
    assert result == []

# catches: "arr[:middle]" mutated to "arr[:middle+1]" (off-by-one in split)
def test_even_length_split():
    result = mergesort([4, 3, 2, 1])
    assert result == [1, 2, 3, 4]

# catches: "arr[middle:]" mutated to "arr[middle+1:]" (off-by-one, element lost)
def test_no_elements_lost_even():
    arr = [4, 3, 2, 1]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: element loss in odd-length array due to index mutation
def test_no_elements_lost_odd():
    arr = [5, 3, 1, 4, 2]
    result = mergesort(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# catches: "result.extend(left[i:] or right[j:])" — if 'or' becomes 'and', remaining elements dropped
def test_remaining_left_elements_appended():
    result = mergesort([1, 2, 5, 3, 4])
    assert result == [1, 2, 3, 4, 5]

# catches: "left[i:] or right[j:]" — if only right remainder is appended and left is skipped
def test_remaining_right_elements_appended():
    result = mergesort([3, 4, 1, 2])
    assert result == [1, 2, 3, 4]

# catches: "i += 1" mutated to "j += 1" or vice versa (wrong index incremented)
def test_correct_order_maintained():
    result = mergesort([9, 1, 8, 2, 7, 3])
    assert result == [1, 2, 3, 7, 8, 9]

# catches: "len(arr) // 2" mutated to "len(arr) // 2 + 1" or "- 1"
def test_three_elements():
    result = mergesort([3, 1, 2])
    assert result == [1, 2, 3]

# catches: negative numbers handled correctly (arithmetic mutation in comparison)
def test_negative_numbers():
    result = mergesort([-3, -1, -2, 0])
    assert result == [-3, -2, -1, 0]

# catches: already sorted input is not corrupted
def test_already_sorted():
    result = mergesort([1, 2, 3, 4, 5])
    assert result == [1, 2, 3, 4, 5]

# catches: reverse sorted input
def test_reverse_sorted():
    result = mergesort([5, 4, 3, 2, 1])
    assert result == [1, 2, 3, 4, 5]

# catches: all same elements — length preserved and order trivially correct
def test_all_same_elements():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == [7, 7, 7, 7]
    assert len(result) == len(arr)

# catches: "while i < len(left) and j < len(right)" — 'and' mutated to 'or' (index out of bounds or wrong merge)
def test_merge_stops_at_shorter_list():
    result = mergesort([3, 1, 2])
    assert result[0] == 1
    assert result[-1] == 3

# catches: result is actually sorted (property check)
def test_result_is_sorted():
    arr = [10, -5, 3, 8, 0, -1, 7]
    result = mergesort(arr)
    for i in range(len(result) - 1):
        assert result[i] <= result[i + 1]
```

```python
# test_whitebox_block.py
from python_programs.mergesort import mergesort

# covers: outer else block, merge with left[i] <= right[j] path, result.extend with remaining left
def test_mergesort_basic_sorted():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: base case len(arr) == 0
def test_mergesort_empty():
    arr = []
    result = mergesort(arr)
    assert result == []
    assert len(result) == 0

# covers: single element (recursive base via len==0 not triggered, but reaches merge with empty halves)
def test_mergesort_single_element():
    arr = [42]
    result = mergesort(arr)
    assert result == [42]
    assert len(result) == 1

# covers: else branch in merge (right[j] < left[i]), result.extend with remaining right
def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: duplicate elements, left[i] <= right[j] equality branch
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: already sorted input, extend with remaining left elements
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# covers: two elements where left > right (hits else in merge, extend with remaining left)
def test_mergesort_two_elements_reversed():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# covers: two elements already sorted (hits left[i] <= right[j] in merge, extend remaining right)
def test_mergesort_two_elements_sorted():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2

# covers: larger array with mixed values ensuring all merge branches hit
def test_mergesort_larger_array():
    arr = [10, -1, 0, 5, 3, 8, -3, 7]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: all same elements (equality in merge)
def test_mergesort_all_same():
    arr = [7, 7, 7, 7]
    result = mergesort(arr)
    assert result == [7, 7, 7, 7]
    assert len(result) == 4

# covers: result.extend with remaining right (right exhausted before left case)
def test_mergesort_extend_remaining_right():
    arr = [1, 3, 5, 2, 4, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)
```

```python
# test_whitebox_condition.py
from python_programs.mergesort import mergesort

# condition: len(arr) == 0: True → return empty array
def test_mergesort_empty_array():
    # len(arr) == 0: True
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# condition: len(arr) == 0: False (single element, no merge needed)
def test_mergesort_single_element():
    # len(arr) == 0: False
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1
    assert sorted(result) == sorted([42])

# condition: len(arr) == 0: False; left[i] <= right[j]: True (left element smaller)
def test_mergesort_two_elements_sorted():
    # len(arr) == 0: False; left[i] <= right[j]: True
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False; left[i] <= right[j]: False (right element smaller)
def test_mergesort_two_elements_reversed():
    # len(arr) == 0: False; left[i] <= right[j]: False
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: left[i] <= right[j]: True (equal elements, covers <=)
def test_mergesort_equal_elements():
    # left[i] <= right[j]: True (equal case)
    arr = [3, 3, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: while i < len(left) and j < len(right): True then False
# exercises the while loop running and terminating; result.extend uses left[i:] remainder
def test_mergesort_left_remainder():
    # while i < len(left): True then exhausts right first; left[i:] is non-empty
    arr = [1, 3, 5, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: while i < len(left) and j < len(right): True then False
# exercises right[j:] remainder
def test_mergesort_right_remainder():
    # while j < len(right): True then exhausts left first; right[j:] is non-empty
    arr = [2, 1, 3, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: i < len(left): False (left exhausted), j < len(right): True
def test_mergesort_left_exhausted_first():
    # i < len(left): False before j < len(right): False
    arr = [1, 4, 5, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: i < len(left): True, j < len(right): False (right exhausted)
def test_mergesort_right_exhausted_first():
    # j < len(right): False before i < len(left): False
    arr = [3, 4, 5, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# General large array test covering multiple recursive splits
def test_mergesort_larger_array():
    # len(arr) == 0: False multiple times; left[i] <= right[j]: both True and False
    arr = [5, 3, 8, 1, 9, 2, 7, 4, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False; left[i] <= right[j]: True and False with duplicates
def test_mergesort_with_duplicates():
    # left[i] <= right[j]: True (equal and less), False (greater)
    arr = [4, 2, 4, 1, 3, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: len(arr) == 0: False with negative numbers
def test_mergesort_negative_numbers():
    # len(arr) == 0: False; left[i] <= right[j]: both True and False
    arr = [-3, -1, -4, -1, -5, -9, -2, -6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: left[i] <= right[j]: True and False with mixed positive/negative
def test_mergesort_mixed_positive_negative():
    # left[i] <= right[j]: True and False
    arr = [-2, 3, -1, 0, 4, -3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# condition: result.extend uses left[i:] or right[j:] — left[i:] non-empty (truthy)
def test_mergesort_extend_uses_left_remainder():
    # After while loop, left[i:] is non-empty → left[i:] or right[j:] evaluates left[i:]
    arr = [1, 2, 5, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)

# condition: result.extend uses left[i:] or right[j:] — left[i:] empty, right[j:] non-empty
def test_mergesort_extend_uses_right_remainder():
    # After while loop, left[i:] is empty → left[i:] or right[j:] evaluates right[j:]
    arr = [3, 1, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
```

```python
# test_whitebox_path.py
import pytest
from python_programs.mergesort import mergesort

# path: len(arr) == 0 → return arr (empty list)
def test_mergesort_empty():
    result = mergesort([])
    assert result == []
    assert len(result) == 0

# path: len(arr) != 0 → split → both halves recurse to empty/single → merge with while loop 0 iterations (one side empty after split)
# single element: middle=0, left=mergesort([])=[], right=mergesort([x])... actually middle=0 means left=[], right=[x]
# merge([], [x]): while loop 0 iters, extend with right[0:] = [x]
def test_mergesort_single():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# path: len(arr) != 0 → split → merge with while loop 1 iteration, left[i] <= right[j] branch True
def test_mergesort_two_ascending():
    arr = [1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop 1 iteration, left[i] <= right[j] branch False (else branch)
def test_mergesort_two_descending():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop many iterations, mixed True/False branches → extend left remainder
def test_mergesort_multiple_left_remainder():
    arr = [1, 3, 5, 2, 4]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: len(arr) != 0 → split → merge with while loop many iterations, mixed True/False branches → extend right remainder
def test_mergesort_multiple_right_remainder():
    arr = [3, 4, 5, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: many iterations → equal elements (left[i] <= right[j] True for equal values)
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: many iterations → all equal elements
def test_mergesort_all_equal():
    arr = [5, 5, 5, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: already sorted → many iterations mostly True branch
def test_mergesort_already_sorted():
    arr = [1, 2, 3, 4, 5, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: reverse sorted → many iterations mostly False (else) branch
def test_mergesort_reverse_sorted():
    arr = [6, 5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: negative numbers → many iterations mixed branches
def test_mergesort_negative_numbers():
    arr = [-3, -1, -4, -1, -5, -9, -2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: mixed positive and negative → many iterations mixed branches
def test_mergesort_mixed_positive_negative():
    arr = [3, -1, 4, -1, 5, -9, 2, 6]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: two elements equal → while loop 1 iteration, left[i] <= right[j] True (equal case)
def test_mergesort_two_equal():
    arr = [7, 7]
    result = mergesort(arr)
    assert result == [7, 7]
    assert len(result) == 2

# path: extend uses left[i:] (non-empty left remainder after while exits)
def test_mergesort_left_tail_extends():
    # After merge, left has remaining elements: e.g., [1,3,5] merged with [2]
    arr = [5, 3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# path: extend uses right[j:] (non-empty right remainder after while exits)
def test_mergesort_right_tail_extends():
    # After merge, right has remaining elements: e.g., [1] merged with [3,4,5]
    arr = [4, 5, 1, 2, 3]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)
```

```python
# test_whitebox_statement.py
from python_programs.mergesort import mergesort

# covers: len(arr) == 0 branch, returns arr
def test_mergesort_empty():
    result = mergesort([])
    assert result == []

# covers: else branch, middle, left/right recursive calls, merge called
# merge: result=[], i=0, j=0, while loop (left[i]<=right[j] true), append left[i], i+=1
# result.extend, return result
# single element (base case via empty, then merge of single elements)
def test_mergesort_single():
    result = mergesort([42])
    assert result == [42]
    assert len(result) == 1

# covers: else branch with multi-element array, merge with left[i] <= right[j] path
# and result.extend(left[i:] or right[j:]) when left has remainder
def test_mergesort_sorted():
    arr = [1, 2, 3, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: else branch in merge (left[i] > right[j]), append right[j], j+=1
# also covers result.extend with right[j:] remainder
def test_mergesort_reverse_sorted():
    arr = [5, 4, 3, 2, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: merge with equal elements (left[i] <= right[j] both branches),
# duplicate values, result.extend path
def test_mergesort_duplicates():
    arr = [3, 1, 2, 3, 1]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: result.extend when right[j:] is non-empty (right has remainder)
def test_mergesort_right_remainder():
    arr = [3, 1, 2]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)

# covers: two-element array, both merge branches
def test_mergesort_two_elements():
    arr = [2, 1]
    result = mergesort(arr)
    assert result == [1, 2]
    assert len(result) == 2
    assert sorted(result) == sorted(arr)

# covers: larger random-like array for full statement coverage confidence
def test_mergesort_larger():
    arr = [9, 3, 7, 1, 8, 2, 6, 4, 5]
    result = mergesort(arr)
    assert result == sorted(arr)
    assert len(result) == len(arr)
    assert sorted(result) == sorted(arr)
```
