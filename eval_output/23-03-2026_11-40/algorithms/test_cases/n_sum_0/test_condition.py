from algorithms.array.n_sum import _sum_closure_default

def test_sum_closure_default_integers():
    assert _sum_closure_default(1, 2) == 3

def test_sum_closure_default_strings():
    assert _sum_closure_default("a", "b") == "ab"

def test_sum_closure_default_lists():
    assert _sum_closure_default([1], [2]) == [1, 2]