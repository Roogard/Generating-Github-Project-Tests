import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v2

def test_empty_list():
    assert longest_common_prefix_v2([]) == ""

def test_single_string():
    assert longest_common_prefix_v2(["hello"]) == "hello"

def test_two_strings_no_common_prefix():
    assert longest_common_prefix_v2(["hello", "world"]) == ""

def test_two_strings_full_match():
    assert longest_common_prefix_v2(["hello", "hello"]) == "hello"

def test_two_strings_partial_match():
    assert longest_common_prefix_v2(["hello", "helicopter"]) == "hel"

def test_multiple_strings_common_prefix():
    assert longest_common_prefix_v2(["flower", "flow", "flight"]) == "fl"

def test_all_strings_empty():
    assert longest_common_prefix_v2(["", "", ""]) == ""

def test_mixed_empty_and_nonempty_strings():
    assert longest_common_prefix_v2(["", "abc", "def"]) == ""

def test_first_string_empty():
    assert longest_common_prefix_v2(["", "abc"]) == ""

def test_first_string_shorter_than_others():
    assert longest_common_prefix_v2(["ab", "abc", "abcd"]) == "ab"

def test_first_string_longer_than_others():
    assert longest_common_prefix_v2(["abcd", "ab", "abc"]) == "ab"

def test_single_character_strings():
    assert longest_common_prefix_v2(["a", "a", "a"]) == "a"

def test_single_character_strings_no_match():
    assert longest_common_prefix_v2(["a", "b", "c"]) == ""

def test_very_long_strings():
    long_prefix = "a" * 1000
    strings = [long_prefix + "x", long_prefix + "y", long_prefix + "z"]
    assert longest_common_prefix_v2(strings) == long_prefix

def test_unicode_characters():
    assert longest_common_prefix_v2(["café", "cafeteria", "caffeine"]) == "caf"

def test_case_sensitivity():
    assert longest_common_prefix_v2(["Hello", "hello"]) == ""