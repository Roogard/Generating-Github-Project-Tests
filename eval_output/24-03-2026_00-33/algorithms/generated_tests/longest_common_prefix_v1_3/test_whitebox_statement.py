from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# covers: if not strings: return ""
def test_empty_list():
    assert longest_common_prefix_v2([]) == ""

# covers: for index in range(len(strings[0])):, for string in strings[1:]:,
#         if index == len(string) or string[index] != strings[0][index]:,
#         return strings[0][0:index]
def test_early_return_on_mismatch():
    result = longest_common_prefix_v2(["flower", "flow", "flight"])
    assert result == "fl"

# covers: the full outer loop completes, return strings[0]
def test_full_match():
    result = longest_common_prefix_v2(["abc", "abc", "abc"])
    assert result == "abc"

# covers: if index == len(string) branch (shorter string encountered)
def test_early_return_on_shorter_string():
    result = longest_common_prefix_v2(["ab", "a", "ac"])
    assert result == "a"

# covers: single string input (outer loop runs, inner loop over empty strings[1:])
def test_single_string():
    result = longest_common_prefix_v2(["alone"])
    assert result == "alone"