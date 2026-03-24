from algorithms.string.longest_common_prefix import longest_common_prefix_v2

# covers: block 1 (if not strings), block 2 (return "")
def test_empty_list():
    assert longest_common_prefix_v2([]) == ""

# covers: block 1 (if not strings skipped), block 3 (for index loop entry),
#         block 4 (inner for string loop entry), block 5 (if index == len(string) or mismatch),
#         block 6 (return strings[0][0:index] early)
def test_no_common_prefix():
    assert longest_common_prefix_v2(["dog", "racecar", "car"]) == ""

# covers: block 1 (if not strings skipped), block 3 (for index loop entry),
#         block 4 (inner for string loop entry), block 5 (if index == len(string) or mismatch skipped),
#         block 7 (return strings[0] after full outer loop)
def test_full_match():
    assert longest_common_prefix_v2(["flower", "flower", "flower"]) == "flower"

# covers: block 1 (if not strings skipped), block 3 (for index loop entry),
#         block 4 (inner for string loop entry), block 5 (if index == len(string) or mismatch),
#         block 6 (return strings[0][0:index] early)
def test_partial_match():
    assert longest_common_prefix_v2(["flower", "flow", "flight"]) == "fl"

# covers: block 1 (if not strings skipped), block 3 (for index loop entry),
#         block 4 (inner for string loop entry), block 5 (if index == len(string) branch true),
#         block 6 (return strings[0][0:index] early)
def test_shorter_string_ends():
    assert longest_common_prefix_v2(["apple", "ap", "ape"]) == "ap"

# covers: block 1 (if not strings skipped), block 3 (for index loop entry),
#         block 4 (inner for string loop entry), block 5 (if string[index] != strings[0][index] branch true),
#         block 6 (return strings[0][0:index] early)
def test_mismatch_at_first_char():
    assert longest_common_prefix_v2(["foo", "bar", "baz"]) == ""