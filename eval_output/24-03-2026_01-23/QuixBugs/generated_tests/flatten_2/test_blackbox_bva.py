from python_programs.flatten import flatten

def test_flatten_empty_list():
    assert list(flatten([])) == []

def test_flatten_single_element_list():
    assert list(flatten([1])) == [1]

def test_flatten_flat_list_multiple_elements():
    assert list(flatten([1, 2, 3])) == [1, 2, 3]

def test_flatten_nested_one_level():
    assert list(flatten([1, [2, 3], 4])) == [1, 2, 3, 4]

def test_flatten_nested_multiple_levels():
    assert list(flatten([1, [2, [3, [4]]], 5])) == [1, 2, 3, 4, 5]