import pytest
from boltons.iterutils import flatten

# path: flatten_iter yields all items from nested iterable
def test_flatten_nested_lists():
    nested = [[1, 2], [[3], [4, 5]]]
    assert flatten(nested) == [1, 2, 3, 4, 5]

# path: flatten_iter yields items from empty outer iterable
def test_flatten_empty():
    assert flatten([]) == []

# path: flatten_iter yields items from flat iterable (no nesting)
def test_flatten_flat():
    assert flatten([1, 2, 3]) == [1, 2, 3]

# path: flatten_iter yields items from mixed nesting
def test_flatten_mixed():
    mixed = [1, [2, [3]], 4]
    assert flatten(mixed) == [1, 2, 3, 4]

# path: flatten_iter yields items from deeply nested single element
def test_flatten_deep_single():
    deep = [[[[[5]]]]]
    assert flatten(deep) == [5]

# path: flatten_iter yields items from iterable with empty sub‑iterables
def test_flatten_with_empty_subiterables():
    data = [[], [1, 2], [], [3], []]
    assert flatten(data) == [1, 2, 3]

# path: flatten_iter yields items from non‑list iterable (e.g., tuple)
def test_flatten_tuple():
    tup = ([1, 2], (3, 4))
    assert flatten(tup) == [1, 2, 3, 4]

# path: flatten_iter yields items from generator
def test_flatten_generator():
    gen = (x for x in [[1], [2, 3]])
    assert flatten(gen) == [1, 2, 3]