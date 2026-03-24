from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# condition: not strings: True
def test_empty_list():
    assert longest_common_prefix_v2([]) == ""

# condition: not strings: False
# condition: index == len(string): True (when index exceeds length of shorter string)
def test_index_equals_len_string():
    assert longest_common_prefix_v2(["ab", "a"]) == "a"

# condition: index == len(string): False, string[index] != strings[0][index]: True
def test_char_mismatch():
    assert longest_common_prefix_v2(["abc", "abd", "abx"]) == "ab"

# condition: index == len(string): False, string[index] != strings[0][index]: False (loop completes)
def test_full_match():
    assert longest_common_prefix_v2(["abc", "abc", "abc"]) == "abc"

# condition: index == len(string): False, string[index] != strings[0][index]: False (for all strings)
# condition: for index in range(len(strings[0])): loop completes without early return
def test_single_string():
    assert longest_common_prefix_v2(["hello"]) == "hello"

# condition: index == len(string): True (when first string is longer than others)
def test_first_string_longer():
    assert longest_common_prefix_v2(["abcdef", "abc", "abcd"]) == "abc"

# condition: index == len(string): False, string[index] != strings[0][index]: True (at first index)
def test_no_common_prefix():
    assert longest_common_prefix_v2(["dog", "cat", "fish"]) == ""