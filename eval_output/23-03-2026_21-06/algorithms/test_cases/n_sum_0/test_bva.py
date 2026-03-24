import pytest
from algorithms.array.n_sum import _union

def test_union_empty_input():
    assert _union([]) == []

def test_union_single_element():
    assert _union([[1, 2]]) == [[1, 2]]

def test_union_two_identical_elements():
    assert _union([[1, 2], [1, 2]]) == [[1, 2]]

def test_union_two_distinct_elements():
    assert _union([[1, 2], [3, 4]]) == [[1, 2], [3, 4]]

def test_union_three_with_duplicates_at_start():
    assert _union([[1, 2], [1, 2], [3, 4]]) == [[1, 2], [3, 4]]

def test_union_three_with_duplicates_in_middle():
    assert _union([[1, 2], [3, 4], [3, 4]]) == [[1, 2], [3, 4]]

def test_union_three_with_duplicates_at_end():
    assert _union([[1, 2], [3, 4], [3, 4]]) == [[1, 2], [3, 4]]

def test_union_all_identical():
    duplicate_results = [[5, 6] for _ in range(5)]
    assert _union(duplicate_results) == [[5, 6]]

def test_union_mixed_order_becomes_sorted():
    assert _union([[3, 4], [1, 2], [3, 4]]) == [[1, 2], [3, 4]]

def test_union_with_empty_sublist():
    assert _union([[], []]) == [[]]

def test_union_with_single_element_sublists():
    assert _union([[1], [2], [1]]) == [[1], [2]]