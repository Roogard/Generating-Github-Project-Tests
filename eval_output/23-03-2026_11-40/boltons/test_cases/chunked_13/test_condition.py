from boltons.iterutils import flatten
import pytest

# condition: isinstance(elem, Iterable): True
def test_flatten_nested_iterable():
    nested = [[1, 2], [[3], [4, 5]]]
    assert flatten(nested) == [1, 2, 3, 4, 5]

# condition: isinstance(elem, Iterable): False
def test_flatten_non_iterable_elements():
    flat = [1, 2, 3, 4, 5]
    assert flatten(flat) == [1, 2, 3, 4, 5]

# condition: isinstance(elem, Iterable): True (string as iterable)
def test_flatten_with_strings():
    # strings are iterable, but flatten treats them as single elements
    # This test ensures that strings are not further flattened
    input_data = ["ab", ["cd"]]
    # Expected: strings are kept as is because flatten_iter checks for basestring in Python 2 or (str, bytes) in Python 3
    # In Python 3, flatten_iter uses isinstance(elem, (str, bytes)) to avoid flattening strings
    # So the result should be ["ab", "cd"]
    assert flatten(input_data) == ["ab", "cd"]

# condition: isinstance(elem, Iterable): True (empty iterable)
def test_flatten_empty_nested():
    nested = [[], [[]], 1]
    assert flatten(nested) == [1]

# condition: isinstance(elem, Iterable): True (mixed nested)
def test_flatten_mixed_nesting():
    nested = [1, [2, [3, 4]], 5]
    assert flatten(nested) == [1, 2, 3, 4, 5]

# condition: isinstance(elem, Iterable): False (single non-iterable)
def test_flatten_single_element():
    assert flatten([42]) == [42]

# condition: isinstance(elem, Iterable): True (deep nesting)
def test_flatten_deep_nesting():
    nested = [[[[[1]]]], 2]
    assert flatten(nested) == [1, 2]