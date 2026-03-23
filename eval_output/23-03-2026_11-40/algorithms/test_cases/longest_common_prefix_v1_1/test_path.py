import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v3

# path: empty check → True → return ""
def test_longest_common_prefix_v3_empty():
    assert longest_common_prefix_v3([]) == ""

# path: empty check → False → recursive base case (low == high) → return strings[low]
def test_longest_common_prefix_v3_single_string():
    assert longest_common_prefix_v3(["abc"]) == "abc"

# path: empty check → False → recursive split (low < high) → left recursion → right recursion → merge
def test_longest_common_prefix_v3_two_strings_common():
    assert longest_common_prefix_v3(["ab", "ac"]) == "a"

# path: empty check → False → recursive split (low < high) → left recursion → right recursion → merge with no common prefix
def test_longest_common_prefix_v3_two_strings_no_common():
    assert longest_common_prefix_v3(["ab", "cd"]) == ""

# path: empty check → False → recursive split (low < high) → left recursion (multiple splits) → right recursion (multiple splits) → merge
def test_longest_common_prefix_v3_multiple_strings_common():
    assert longest_common_prefix_v3(["flower", "flow", "flight"]) == "fl"

# path: empty check → False → recursive split (low < high) → left recursion (multiple splits) → right recursion (multiple splits) → merge with empty prefix
def test_longest_common_prefix_v3_multiple_strings_no_common():
    assert longest_common_prefix_v3(["dog", "racecar", "car"]) == ""