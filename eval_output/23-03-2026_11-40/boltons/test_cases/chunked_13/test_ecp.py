import pytest
from boltons.iterutils import flatten

# Valid equivalence class: empty iterable
def test_flatten_empty():
    assert flatten([]) == []

# Valid equivalence class: flat list of non-iterable items
def test_flatten_flat_list():
    assert flatten([1, 2, 3]) == [1, 2, 3]

# Valid equivalence class: nested list of non-iterable items
def test_flatten_nested_list():
    assert flatten([[1, 2], [[3], [4, 5]]]) == [1, 2, 3, 4, 5]

# Valid equivalence class: mixed iterables (list and tuple)
def test_flatten_mixed_iterables():
    assert flatten([(1, 2), [3, (4, 5)]]) == [1, 2, 3, 4, 5]

# Valid equivalence class: generator as input
def test_flatten_generator():
    gen = (x for x in [[1], [2, 3]])
    assert flatten(gen) == [1, 2, 3]

# Valid equivalence class: string items (strings are iterable but treated as single items)
def test_flatten_with_strings():
    # Strings are iterable, but flatten does not break them apart.
    # This is a known behavior: flatten does not recurse into strings.
    assert flatten(["ab", ["cd"]]) == ["ab", "cd"]

# Valid equivalence class: deeply nested empty iterables
def test_flatten_deeply_nested_empty():
    assert flatten([[[[]]]]) == []

# Valid equivalence class: single non-iterable item in list
def test_flatten_single_item():
    assert flatten([42]) == [42]

# Valid equivalence class: iterable containing None
def test_flatten_with_none():
    assert flatten([None, [1, None]]) == [None, 1, None]