import pytest
from toolz.itertoolz import mapcat

# Path analysis for mapcat(func, seqs):
# 1. Branch: none (no if/else, loops, or try/except in function body)
# 2. Function calls: map(func, seqs) → concat(...)
# 3. Since there are no branches, there is exactly one execution path.
# 4. However, we should consider edge cases for input sequences:
#    - Empty seqs list
#    - Single sequence in seqs
#    - Multiple sequences in seqs
#    - Sequences of varying lengths (including empty sequences)
#    - Different func behaviors (returning empty list, returning multiple items)

# path: single path through function
def test_mapcat_empty_seqs():
    # seqs is empty list, map returns empty iterator, concat returns empty iterator
    result = list(mapcat(lambda s: [x.upper() for x in s], []))
    assert result == []

def test_mapcat_single_seq():
    # seqs has one sequence, func processes it, concat yields results
    result = list(mapcat(lambda s: [x * 2 for x in s], [[1, 2, 3]]))
    assert result == [2, 4, 6]

def test_mapcat_multiple_seqs():
    # seqs has multiple sequences, func processes each, concat concatenates
    result = list(mapcat(lambda s: [x.upper() for x in s], [["a", "b"], ["c", "d", "e"]]))
    assert result == ['A', 'B', 'C', 'D', 'E']

def test_mapcat_with_empty_sequences_in_seqs():
    # seqs contains empty sequences, func returns empty lists, concat handles them
    result = list(mapcat(lambda s: [x + 1 for x in s], [[], [1, 2], [], [3]]))
    assert result == [2, 3, 4]

def test_mapcat_func_returns_empty():
    # func returns empty list for some sequences
    result = list(mapcat(lambda s: [] if len(s) == 0 else [sum(s)], [[], [1, 2, 3], [4, 5]]))
    assert result == [6, 9]

def test_mapcat_func_returns_multiple_items():
    # func returns variable number of items per sequence
    result = list(mapcat(lambda s: list(range(len(s))), [[], ['a'], ['b', 'c'], ['d', 'e', 'f']]))
    assert result == [0, 0, 1, 0, 1, 2]

def test_mapcat_large_sequences():
    # stress test with larger sequences
    result = list(mapcat(lambda s: [x ** 2 for x in s], [[1, 2, 3], [4, 5], [6]]))
    assert result == [1, 4, 9, 16, 25, 36]