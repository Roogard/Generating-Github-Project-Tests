from algorithms.string.longest_common_prefix import longest_common_prefix_v3

# condition: not strings: True → return ""
def test_empty_list():
    assert longest_common_prefix_v3([]) == ""

# condition: not strings: False → proceed to recursive call
def test_single_string():
    assert longest_common_prefix_v3(["abc"]) == "abc"

def test_all_identical():
    assert longest_common_prefix_v3(["abc", "abc", "abc"]) == "abc"

def test_common_prefix():
    assert longest_common_prefix_v3(["flower", "flow", "flight"]) == "fl"

def test_no_common_prefix():
    assert longest_common_prefix_v3(["dog", "racecar", "car"]) == ""