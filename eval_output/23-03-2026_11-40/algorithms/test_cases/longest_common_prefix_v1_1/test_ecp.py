import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v3

# Valid equivalence class: empty list
def test_empty_list():
    assert longest_common_prefix_v3([]) == ""

# Valid equivalence class: list with one string
def test_single_string():
    assert longest_common_prefix_v3(["abc"]) == "abc"

# Valid equivalence class: list with multiple strings having common prefix
def test_multiple_strings_with_common_prefix():
    assert longest_common_prefix_v3(["flower", "flow", "flight"]) == "fl"

# Valid equivalence class: list with multiple strings having no common prefix
def test_multiple_strings_no_common_prefix():
    assert longest_common_prefix_v3(["dog", "racecar", "car"]) == ""

# Valid equivalence class: list where all strings are identical
def test_all_strings_identical():
    assert longest_common_prefix_v3(["abc", "abc", "abc"]) == "abc"

# Valid equivalence class: list where common prefix is the shortest string
def test_common_prefix_is_shortest_string():
    assert longest_common_prefix_v3(["ab", "abc", "abcd"]) == "ab"

# Valid equivalence class: list containing empty strings
def test_list_with_empty_strings():
    assert longest_common_prefix_v3(["", "abc", "ab"]) == ""

# Valid equivalence class: list where all strings are empty
def test_all_strings_empty():
    assert longest_common_prefix_v3(["", "", ""]) == ""