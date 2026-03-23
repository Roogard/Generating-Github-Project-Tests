import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v3

def test_empty_list():
    assert longest_common_prefix_v3([]) == ""

def test_single_string():
    assert longest_common_prefix_v3(["abc"]) == "abc"

def test_two_strings_no_common_prefix():
    assert longest_common_prefix_v3(["abc", "def"]) == ""

def test_two_strings_with_common_prefix():
    assert longest_common_prefix_v3(["abc", "abd"]) == "ab"

def test_all_strings_identical():
    assert longest_common_prefix_v3(["abc", "abc", "abc"]) == "abc"

def test_common_prefix_shorter_than_all():
    assert longest_common_prefix_v3(["flower", "flow", "flight"]) == "fl"

def test_one_string_empty():
    assert longest_common_prefix_v3(["", "abc"]) == ""

def test_all_strings_empty():
    assert longest_common_prefix_v3(["", "", ""]) == ""

def test_single_character_strings():
    assert longest_common_prefix_v3(["a", "a", "a"]) == "a"

def test_single_character_strings_no_match():
    assert longest_common_prefix_v3(["a", "b", "c"]) == ""