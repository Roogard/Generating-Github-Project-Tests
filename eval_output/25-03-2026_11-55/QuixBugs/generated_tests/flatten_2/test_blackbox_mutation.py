from python_programs.flatten import flatten

# catches: simple non-nested list should remain unchanged
def test_flatten_simple():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

# catches: single-level nesting not flattened if recursive call is missing
def test_flatten_nested_once():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

# catches: multi-level nesting only flattened one level (off-by-one recursion depth)
def test_flatten_deeply_nested():
    data = [1, [2, [3, [4]]], 5]
    assert list(flatten(data)) == [1, 2, 3, 4, 5]

# catches: empty lists not being skipped or causing errors
def test_flatten_with_empty_lists():
    data = [[], [[], [1], []], []]
    assert list(flatten(data)) == [1]

# catches: using type(x) is list instead of isinstance(x, list) (list subclass case)
def test_flatten_list_subclass():
    class MyList(list):
        pass
    data = [MyList([1, 2]), 3]
    assert list(flatten(data)) == [1, 2, 3]

# catches: treating all iterables as sequences (e.g., tuple flattened if isinstance check wrong)
def test_flatten_tuple_treated_as_atomic():
    data = [(1, 2), 3]
    assert list(flatten(data)) == [(1, 2), 3]

# catches: strings accidentally iterated over if isinstance check is too broad
def test_flatten_strings_treated_as_atomic():
    data = ["abc", [["de"], ["f"]]]
    assert list(flatten(data)) == ["abc", "de", "f"]

# catches: missing generator behavior or wrong base case for an empty input
def test_flatten_empty_input():
    assert list(flatten([])) == []