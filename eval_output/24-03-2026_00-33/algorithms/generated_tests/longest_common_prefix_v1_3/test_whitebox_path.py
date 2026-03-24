import pytest
from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# path: empty check → True → return ""
def test_longest_common_prefix_v2_empty():
    assert longest_common_prefix_v2([]) == ""

# path: empty check → False → outer loop 0 iterations → return strings[0]
def test_longest_common_prefix_v2_single_string():
    assert longest_common_prefix_v2(["abc"]) == "abc"

# path: empty check → False → outer loop 1 iteration → inner loop 1 iteration → inner if True (index == len(string)) → return prefix
def test_longest_common_prefix_v2_first_string_longer():
    assert longest_common_prefix_v2(["ab", "a"]) == "a"

# path: empty check → False → outer loop 1 iteration → inner loop 1 iteration → inner if True (string[index] != strings[0][index]) → return prefix
def test_longest_common_prefix_v2_mismatch_first_char():
    assert longest_common_prefix_v2(["ab", "cd"]) == ""

# path: empty check → False → outer loop 1 iteration → inner loop 1 iteration → inner if False → outer loop ends → return strings[0]
def test_longest_common_prefix_v2_two_strings_full_match():
    assert longest_common_prefix_v2(["ab", "ab"]) == "ab"

# path: empty check → False → outer loop many iterations → inner loop 1 iteration → inner if True (index == len(string)) → return prefix
def test_longest_common_prefix_v2_multi_string_first_longer():
    assert longest_common_prefix_v2(["flower", "flow", "flo"]) == "flo"

# path: empty check → False → outer loop many iterations → inner loop 1 iteration → inner if True (string[index] != strings[0][index]) → return prefix
def test_longest_common_prefix_v2_multi_string_mismatch():
    assert longest_common_prefix_v2(["flower", "flow", "flight"]) == "fl"

# path: empty check → False → outer loop many iterations → inner loop 1 iteration → inner if False → outer loop ends → return strings[0]
def test_longest_common_prefix_v2_all_identical():
    assert longest_common_prefix_v2(["abc", "abc", "abc"]) == "abc"

# path: empty check → False → outer loop 1 iteration → inner loop many iterations → inner if True (index == len(string)) on second inner iteration → return prefix
def test_longest_common_prefix_v2_three_strings_second_shorter():
    assert longest_common_prefix_v2(["ab", "a", "ac"]) == "a"

# path: empty check → False → outer loop 1 iteration → inner loop many iterations → inner if True (string[index] != strings[0][index]) on second inner iteration → return prefix
def test_longest_common_prefix_v2_three_strings_mismatch_second():
    assert longest_common_prefix_v2(["ab", "ac", "ad"]) == "a"

# path: empty check → False → outer loop many iterations → inner loop many iterations → inner if True (index == len(string)) on later inner iteration → return prefix
def test_longest_common_prefix_v2_mixed_lengths():
    assert longest_common_prefix_v2(["flowering", "flower", "flow"]) == "flow"

# path: empty check → False → outer loop many iterations → inner loop many iterations → inner if True (string[index] != strings[0][index]) on later inner iteration → return prefix
def test_longest_common_prefix_v2_complex_mismatch():
    assert longest_common_prefix_v2(["interspecies", "interstellar", "interstate"]) == "inters"

# path: empty check → False → outer loop many iterations → inner loop many iterations → inner if False always → outer loop completes → return strings[0]
def test_longest_common_prefix_v2_all_same_length_full_match():
    assert longest_common_prefix_v2(["hello", "hello", "hello"]) == "hello"