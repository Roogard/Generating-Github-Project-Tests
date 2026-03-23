import pytest
from toolz.itertoolz import mapcat

# Valid equivalence class: func returns a list, seqs is a list of sequences
def test_mapcat_func_returns_list_seqs_is_list():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], ["c", "d", "e"]]))
    assert result == ['A', 'B', 'C', 'D', 'E']

# Valid equivalence class: func returns a tuple, seqs is a tuple of sequences
def test_mapcat_func_returns_tuple_seqs_is_tuple():
    result = list(mapcat(lambda s: (c.upper() for c in s), (("a", "b"), ("c", "d", "e"))))
    assert result == ['A', 'B', 'C', 'D', 'E']

# Valid equivalence class: func returns a generator, seqs is a generator
def test_mapcat_func_returns_generator_seqs_is_generator():
    seqs_gen = (x for x in [["a", "b"], ["c", "d", "e"]])
    result = list(mapcat(lambda s: (c.upper() for c in s), seqs_gen))
    assert result == ['A', 'B', 'C', 'D', 'E']

# Valid equivalence class: empty seqs
def test_mapcat_empty_seqs():
    result = list(mapcat(lambda s: [c.upper() for c in s], []))
    assert result == []

# Valid equivalence class: seqs contains empty sequences
def test_mapcat_seqs_contains_empty_sequences():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], [], ["c"]]))
    assert result == ['A', 'B', 'C']

# Valid equivalence class: func returns empty iterable for some sequences
def test_mapcat_func_returns_empty_for_some():
    result = list(mapcat(lambda s: [] if s == ["b"] else [c.upper() for c in s], [["a"], ["b"], ["c"]]))
    assert result == ['A', 'C']

# Invalid equivalence class: seqs is not iterable
def test_mapcat_seqs_not_iterable():
    with pytest.raises(TypeError):
        list(mapcat(lambda s: [c.upper() for c in s], 123))

# Invalid equivalence class: func is not callable
def test_mapcat_func_not_callable():
    with pytest.raises(TypeError):
        list(mapcat("not a function", [["a", "b"]]))

# Invalid equivalence class: seqs contains non-iterable elements
def test_mapcat_seqs_contains_non_iterable():
    with pytest.raises(TypeError):
        list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], 123]))