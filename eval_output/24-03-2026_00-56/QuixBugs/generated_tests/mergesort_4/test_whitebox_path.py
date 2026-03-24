import pytest
from correct_python_programs.mergesort import mergesort

# path: len(arr) <= 1 → True → return arr (empty list)
def test_mergesort_empty():
    assert mergesort([]) == []

# path: len(arr) <= 1 → True → return arr (single element)
def test_mergesort_single():
    assert mergesort([5]) == [5]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → True (first iteration) → then later False
#   after while: result.extend(left[i:] or right[j:]) → left[i:] non-empty
def test_mergesort_two_elements_ascending():
    assert mergesort([1, 2]) == [1, 2]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → False (first iteration) → then later True
#   after while: result.extend(left[i:] or right[j:]) → right[j:] non-empty
def test_mergesort_two_elements_descending():
    assert mergesort([2, 1]) == [1, 2]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → always True
#   after while: result.extend(left[i:] or right[j:]) → right[j:] non-empty (left exhausted)
def test_mergesort_left_exhausted_first():
    assert mergesort([1, 3, 5, 2, 4]) == [1, 2, 3, 4, 5]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → always False
#   after while: result.extend(left[i:] or right[j:]) → left[i:] non-empty (right exhausted)
def test_mergesort_right_exhausted_first():
    assert mergesort([6, 8, 1, 2]) == [1, 2, 6, 8]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → False (zero iterations because left or right empty)
#   after while: result.extend(left[i:] or right[j:]) → left[i:] non-empty (right empty)
def test_mergesort_one_side_empty_after_recursion():
    # This path occurs when one recursive call returns empty list (impossible with mergesort's base case)
    # Instead, simulate merge being called with an empty left or right from within recursion:
    # Actually, mergesort never returns empty unless input is empty, so this path is infeasible.
    # We'll test a case where one side is a single element and the other is multiple, but merge's while may still run.
    # Let's create a case where while loop runs zero iterations because one side is empty after recursion? Not possible.
    # Skip this path as infeasible.

# Alternative: test a case where while loop runs exactly one iteration
# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (exactly one iteration)
#   inner if: left[i] <= right[j] → True
#   after while: result.extend(left[i:] or right[j:]) → right[j:] non-empty
def test_mergesort_while_one_iteration_true():
    # left = [1], right = [2,3] → while runs once (1 <= 2), then left exhausted, extend right
    # To achieve this, we need arr such that after recursion we get those left/right.
    # arr = [1,2,3] → middle = 1 → left = mergesort([1]) = [1], right = mergesort([2,3]) = [2,3]
    assert mergesort([1, 2, 3]) == [1, 2, 3]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (exactly one iteration)
#   inner if: left[i] <= right[j] → False
#   after while: result.extend(left[i:] or right[j:]) → left[i:] non-empty
def test_mergesort_while_one_iteration_false():
    # left = [2], right = [1,3] → while runs once (2 <= 1 false), then right exhausted? Wait, after first iteration j becomes 1, len(right)=2, so while condition still true? Actually after first iteration: j=1, i=0, left[0]=2, right[1]=3, while runs second iteration.
    # Need left and right such that after one iteration one side becomes empty.
    # left = [2], right = [1] → while runs once (2 <= 1 false), after iteration j=1, len(right)=1, while condition false (j=1 not <1). Then extend left[i:] = left[0:] = [2].
    # arr = [2,1] → middle = 1 → left = mergesort([2]) = [2], right = mergesort([1]) = [1]
    assert mergesort([2, 1]) == [1, 2]  # same as test_mergesort_two_elements_descending, but that's okay.

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → mixed True/False
#   after while: result.extend(left[i:] or right[j:]) → both left[i:] and right[j:] empty (exact match)
def test_mergesort_while_exact_match_exhaust_both():
    # left = [1,3], right = [2,4] → while runs: 1<=2 T, 3<=2 F, 3<=4 T → after while i=2, j=2, both exhausted
    # arr = [1,3,2,4] → after recursion we get left=[1,3], right=[2,4]
    assert mergesort([1, 3, 2, 4]) == [1, 2, 3, 4]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → mixed
#   after while: result.extend(left[i:] or right[j:]) → left[i:] non-empty (right exhausted)
def test_mergesort_while_exhaust_right():
    # left = [1,4,5], right = [2,3] → while: 1<=2 T, 4<=2 F, 4<=3 F → after while i=1, j=2, right exhausted, left[i:] = [4,5]
    # arr = [1,4,5,2,3]
    assert mergesort([1, 4, 5, 2, 3]) == [1, 2, 3, 4, 5]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → True (multiple iterations)
#   inner if: left[i] <= right[j] → mixed
#   after while: result.extend(left[i:] or right[j:]) → right[j:] non-empty (left exhausted)
def test_mergesort_while_exhaust_left():
    # left = [1,2], right = [3,4,5] → while: 1<=3 T, 2<=3 T → after while i=2, j=0, left exhausted, right[j:] = [3,4,5]
    # arr = [1,2,3,4,5]
    assert mergesort([1, 2, 3, 4, 5]) == [1, 2, 3, 4, 5]

# path: len(arr) <= 1 → False → recursive left/right calls → merge with:
#   while loop: i < len(left) and j < len(right) → False (zero iterations) because left empty? Not possible.
# Actually, left or right could be empty if base case returns empty list, but base case only returns empty when input empty.
# So zero-iteration while is infeasible in mergesort. Skip.

# Additional test for larger, unsorted array to cover deeper recursion paths
def test_mergesort_large_unsorted():
    assert mergesort([5, 3, 8, 6, 2, 7, 1, 4]) == [1, 2, 3, 4, 5, 6, 7, 8]

# Test with duplicate values
def test_mergesort_duplicates():
    assert mergesort([3, 1, 2, 3, 1]) == [1, 1, 2, 3, 3]