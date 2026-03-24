from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# catches: "if not strings:" mutated to "if strings:" (negation error)
def test_empty_input():
    assert longest_common_prefix_v2([]) == ""

# catches: "range(len(strings[0]))" mutated to "range(len(strings[0])+1)" (off-by-one)
def test_first_string_is_shortest():
    assert longest_common_prefix_v2(["ab", "abc", "abcd"]) == "ab"

# catches: "index == len(string)" mutated to "index >= len(string)" (boundary error)
def test_string_shorter_than_first():
    assert longest_common_prefix_v2(["abc", "ab", "a"]) == "a"

# catches: "string[index] != strings[0][index]" mutated to "string[index] == strings[0][index]" (wrong operator)
def test_no_common_prefix():
    assert longest_common_prefix_v2(["dog", "cat", "fish"]) == ""

# catches: "strings[1:]" mutated to "strings[0:]" (wrong slice, includes first string)
def test_single_string():
    assert longest_common_prefix_v2(["hello"]) == "hello"

# catches: "return strings[0][0:index]" mutated to "return strings[0][0:index+1]" (off-by-one in slice)
def test_common_prefix_exact_length_of_first():
    assert longest_common_prefix_v2(["flow", "flower", "flowing"]) == "flow"

# catches: "for string in strings[1:]" mutated to "for string in strings" (includes first string)
def test_all_identical_strings():
    assert longest_common_prefix_v2(["test", "test", "test"]) == "test"

# catches: missing final "return strings[0]" (fall-through error)
def test_first_string_is_full_prefix():
    assert longest_common_prefix_v2(["pre", "pre", "pre"]) == "pre"

# catches: "index == len(string)" mutated to "index > len(string)" (boundary error)
def test_one_empty_string_in_list():
    assert longest_common_prefix_v2(["abc", "", "ab"]) == ""

# catches: "string[index] != strings[0][index]" mutated to "string[index] != strings[1][index]" (wrong variable)
def test_mismatch_in_middle():
    assert longest_common_prefix_v2(["prefix", "prefox", "prefaz"]) == "pref"