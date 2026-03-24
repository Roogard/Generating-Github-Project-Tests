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

def test_two_strings_partial_prefix():
    assert longest_common_prefix_v2(["hello", "helicopter"]) == "hel"

def test_multiple_strings_common_prefix():
    assert longest_common_prefix_v2(["flower", "flow", "flight"]) == "fl"

def test_all_strings_empty():
    assert longest_common_prefix_v2(["", "", ""]) == ""

def test_mixed_empty_and_nonempty():
    assert longest_common_prefix_v2(["", "abc", "ab"]) == ""

def test_first_string_empty():
    assert longest_common_prefix_v2(["", "abc"]) == ""

def test_first_string_shorter_than_others():
    assert longest_common_prefix_v2(["ab", "abc", "abcd"]) == "ab"

def test_first_string_longer_than_others():
    assert longest_common_prefix_v2(["abcd", "ab", "abc"]) == "ab"

def test_identical_strings():
    assert longest_common_prefix_v2(["prefix", "prefix", "prefix"]) == "prefix"

def test_single_character_strings():
    assert longest_common_prefix_v2(["a", "a", "a"]) == "a"

def test_no_common_prefix_different_first_chars():
    assert longest_common_prefix_v2(["apple", "banana", "cherry"]) == ""

# kills: Off-by-one in outer loop range: uses range(len(strings[0])-1) instead of range(len(strings[0])), potentially missing last character
def test_single_char_prefix_with_full_first_string_match():
    """First string exactly matches prefix, needs full length check."""
    assert longest_common_prefix_v2(["a", "ab"]) == "a"

# kills: Off-by-one in outer loop range: uses range(len(strings[0])-1) instead of range(len(strings[0])), potentially missing last character
def test_prefix_equals_first_string():
    """First string is the exact common prefix."""
    assert longest_common_prefix_v2(["abc", "abcde", "abcdef"]) == "abc"

# kills: Wrong loop variable: iterates over strings[0:] instead of strings[1:], comparing first string with itself
def test_different_strings_where_first_equals_second_but_not_third():
    """First and second match but third differs; mutation comparing first with itself would miss the mismatch."""
    assert longest_common_prefix_v2(["abc", "abc", "abd"]) == "ab"

# kills: Wrong loop variable: iterates over strings[0:] instead of strings[1:], comparing first string with itself
def test_first_string_differs_from_others_at_same_index():
    """First string differs from others at index 0; mutation would incorrectly compare first with itself and not detect difference."""
    assert longest_common_prefix_v2(["b", "a", "a"]) == ""