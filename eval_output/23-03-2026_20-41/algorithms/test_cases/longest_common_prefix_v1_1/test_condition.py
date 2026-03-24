from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# condition: not strings: True
def test_empty_list():
    assert longest_common_prefix_v2([]) == ""

# condition: not strings: False
# condition: index == len(string): True (for string in strings[1:])
def test_first_string_longer():
    assert longest_common_prefix_v2(["abc", "ab"]) == "ab"

# condition: not strings: False
# condition: index == len(string): False, string[index] != strings[0][index]: True
def test_mismatch_at_index():
    assert longest_common_prefix_v2(["abc", "abd", "abx"]) == "ab"

# condition: not strings: False
# condition: index == len(string): False, string[index] != strings[0][index]: False (loop completes)
def test_all_identical():
    assert longest_common_prefix_v2(["abc", "abc", "abc"]) == "abc"

# condition: not strings: False
# condition: index == len(string): True (for first inner iteration, early return)
def test_first_string_shorter():
    assert longest_common_prefix_v2(["ab", "abc", "abcd"]) == "ab"

# condition: not strings: False
# condition: index == len(string): False, string[index] != strings[0][index]: True (first inner iteration)
def test_no_common_prefix():
    assert longest_common_prefix_v2(["abc", "def", "ghi"]) == ""

# condition: not strings: False
# condition: index == len(string): False, string[index] != strings[0][index]: False (inner loop completes, outer loop completes)
def test_single_string():
    assert longest_common_prefix_v2(["alone"]) == "alone"