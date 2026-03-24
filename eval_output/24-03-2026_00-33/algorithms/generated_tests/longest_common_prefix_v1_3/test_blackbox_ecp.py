import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# Valid equivalence class: list with multiple strings having a common prefix
def test_multiple_strings_with_common_prefix():
    assert longest_common_prefix_v2(["flower", "flow", "flight"]) == "fl"

# Valid equivalence class: list with identical strings
def test_all_strings_identical():
    assert longest_common_prefix_v2(["abc", "abc", "abc"]) == "abc"

# Valid equivalence class: list with single string
def test_single_string():
    assert longest_common_prefix_v2(["alone"]) == "alone"

# Valid equivalence class: list with empty strings
def test_all_empty_strings():
    assert longest_common_prefix_v2(["", "", ""]) == ""

# Valid equivalence class: list where first string is shortest and is the full prefix
def test_first_string_is_full_prefix():
    assert longest_common_prefix_v2(["ab", "abc", "abcd"]) == "ab"

# Valid equivalence class: list where first string is longer than common prefix
def test_first_string_longer_than_prefix():
    assert longest_common_prefix_v2(["abcde", "abxy", "abz"]) == "ab"

# Valid equivalence class: list with no common prefix
def test_no_common_prefix():
    assert longest_common_prefix_v2(["dog", "racecar", "car"]) == ""

# Invalid equivalence class: empty list
def test_empty_list():
    assert longest_common_prefix_v2([]) == ""