import pytest
from toolz.itertoolz import mapcat

def test_mapcat_empty_input_sequence():
    result = list(mapcat(lambda x: [x * 2], []))
    assert result == []

def test_mapcat_single_sequence_empty():
    result = list(mapcat(lambda s: [c.upper() for c in s], [[]]))
    assert result == []

def test_mapcat_single_sequence_single_element():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a"]]))
    assert result == ["A"]

def test_mapcat_single_sequence_multiple_elements():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"]]))
    assert result == ["A", "B"]

def test_mapcat_multiple_sequences_one_empty():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], []]))
    assert result == ["A", "B"]

def test_mapcat_multiple_sequences_all_empty():
    result = list(mapcat(lambda s: [c.upper() for c in s], [[], []]))
    assert result == []

def test_mapcat_func_returns_empty_list():
    result = list(mapcat(lambda s: [], [["a", "b"], ["c"]]))
    assert result == []

def test_mapcat_func_returns_single_element_list():
    result = list(mapcat(lambda s: [s[0].upper()] if s else [], [["a", "b"], ["c"]]))
    assert result == ["A", "C"]

def test_mapcat_func_returns_multiple_elements():
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], ["c", "d", "e"]]))
    assert result == ["A", "B", "C", "D", "E"]

def test_mapcat_with_identity_func():
    result = list(mapcat(lambda x: x, [[1, 2], [3, 4, 5]]))
    assert result == [1, 2, 3, 4, 5]

def test_mapcat_func_returns_iterator():
    result = list(mapcat(lambda s: (c.upper() for c in s), [["a", "b"], ["c"]]))
    assert result == ["A", "B", "C"]

def test_mapcat_func_returns_tuple():
    result = list(mapcat(lambda s: tuple(c.upper() for c in s), [["a", "b"], ["c"]]))
    assert result == ["A", "B", "C"]

def test_mapcat_func_returns_string_as_sequence():
    result = list(mapcat(lambda s: s.upper(), ["ab", "cd"]))
    assert result == ["A", "B", "C", "D"]