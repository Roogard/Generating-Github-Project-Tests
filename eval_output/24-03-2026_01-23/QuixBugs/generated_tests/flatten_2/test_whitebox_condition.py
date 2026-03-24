from python_programs.flatten import flatten
import types

# condition: isinstance(x, list) = False
def test_flatten_single_nonlist_element():
    # Input has one non-list element -> False branch once
    result = list(flatten([42]))
    assert len(result) == 1
    # The function yields flatten(42), which is a generator object
    assert isinstance(result[0], types.GeneratorType)

# condition: isinstance(x, list) = True
def test_flatten_single_nested_list():
    # Input has one list element -> True branch once
    input_list = [[1, 2, 3]]
    result = list(flatten(input_list))
    # Should yield three items (flattening [1,2,3]), each a generator
    assert len(result) == 3
    assert all(isinstance(item, types.GeneratorType) for item in result)

# Mixed case to ensure both branches in one call
def test_flatten_mixed_elements():
    # First and last are non-lists (False), middle is list (True)
    mixed = [7, [8, 9], 10]
    result = list(flatten(mixed))
    # Should yield four items total: flatten(7), flatten(8), flatten(9), flatten(10)
    assert len(result) == 4
    assert all(isinstance(item, types.GeneratorType) for item in result)