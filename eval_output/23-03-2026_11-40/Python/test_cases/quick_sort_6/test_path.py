import pytest
from sorts.quick_sort import quick_sort

# path: base case True (len < 2) → return collection (empty list)
def test_quick_sort_empty():
    assert quick_sort([]) == []

# path: base case True (len < 2) → return collection (single element)
def test_quick_sort_single():
    assert quick_sort([5]) == [5]

# path: base case False → pivot selection → lesser empty, greater empty → two recursive base cases (both True) → return
# This path requires collection of length 2 where after removing pivot, the remaining element equals pivot,
# so both lesser and greater become empty. Example: [1,1]
def test_quick_sort_two_equal():
    result = quick_sort([1, 1])
    assert result == [1, 1]

# path: base case False → pivot selection → lesser non‑empty (1 element), greater empty → recursive call on lesser (base case False → then further recursion), recursive call on greater (base case True) → return
# Example: [2,1] where pivot=2 → lesser=[1], greater=[]
def test_quick_sort_two_descending():
    result = quick_sort([2, 1])
    assert result == [1, 2]

# path: base case False → pivot selection → lesser empty, greater non‑empty (1 element) → recursive call on lesser (base case True), recursive call on greater (base case False → then further recursion) → return
# Example: [1,2] where pivot=1 → lesser=[], greater=[2]
def test_quick_sort_two_ascending():
    result = quick_sort([1, 2])
    assert result == [1, 2]

# path: base case False → pivot selection → lesser non‑empty (multiple), greater empty → recursion on lesser (multiple paths inside), recursion on greater (base case True)
# Example: [3,1,2] where pivot=3 → lesser=[1,2], greater=[]
def test_quick_sort_pivot_is_max():
    result = quick_sort([3, 1, 2])
    assert result == [1, 2, 3]

# path: base case False → pivot selection → lesser empty, greater non‑empty (multiple) → recursion on lesser (base case True), recursion on greater (multiple paths inside)
# Example: [1,3,2] where pivot=1 → lesser=[], greater=[3,2]
def test_quick_sort_pivot_is_min():
    result = quick_sort([1, 3, 2])
    assert result == [1, 2, 3]

# path: base case False → pivot selection → lesser non‑empty (multiple), greater non‑empty (multiple) → recursion on both (multiple paths inside)
# Example: [3,1,4,2] → pivot random, both sides non‑empty
def test_quick_sort_general_multiple():
    result = quick_sort([3, 1, 4, 2])
    assert result == [1, 2, 3, 4]

# path: base case False → pivot selection → lesser non‑empty (with duplicates), greater non‑empty (with duplicates) → recursion on both
def test_quick_sort_with_duplicates():
    result = quick_sort([0, 5, 3, 2, 2])
    assert result == [0, 2, 2, 3, 5]

# path: base case False → pivot selection → lesser non‑empty (negative numbers), greater non‑empty (mixed) → recursion on both
def test_quick_sort_negative_numbers():
    result = quick_sort([-2, 5, 0, -45])
    assert result == [-45, -2, 0, 5]