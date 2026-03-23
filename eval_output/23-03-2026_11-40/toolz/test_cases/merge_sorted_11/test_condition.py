from toolz.itertoolz import mapcat

# condition: none (no boolean conditions in mapcat)
def test_mapcat_basic():
    # func returns list, seqs has two sequences
    result = list(mapcat(lambda s: [c.upper() for c in s], [["a", "b"], ["c", "d", "e"]]))
    assert result == ['A', 'B', 'C', 'D', 'E']

# condition: none (no boolean conditions in mapcat)
def test_mapcat_empty_seqs():
    # empty seqs list
    result = list(mapcat(lambda s: [c.upper() for c in s], []))
    assert result == []

# condition: none (no boolean conditions in mapcat)
def test_mapcat_func_returns_empty():
    # func returns empty list for one sequence
    result = list(mapcat(lambda s: [], [["a", "b"], ["c", "d"]]))
    assert result == []

# condition: none (no boolean conditions in mapcat)
def test_mapcat_single_sequence():
    # only one sequence in seqs
    result = list(mapcat(lambda s: [c.lower() for c in s], [["A", "B"]]))
    assert result == ['a', 'b']

# condition: none (no boolean conditions in mapcat)
def test_mapcat_func_returns_iterator():
    # func returns iterator instead of list
    result = list(mapcat(lambda s: (c.upper() for c in s), [["x", "y"], ["z"]]))
    assert result == ['X', 'Y', 'Z']