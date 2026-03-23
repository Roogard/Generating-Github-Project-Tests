import pytest
from algorithms.array.n_sum import n_sum

def test_sum_closure_default_integers():
    # The n_sum function returns a closure that uses _sum_closure_default internally
    # For two numbers, n_sum should return their sum
    assert n_sum(5, 3) == 8

def test_sum_closure_default_strings():
    assert n_sum("hello", " world") == "hello world"

def test_sum_closure_default_floats():
    assert n_sum(2.5, 3.5) == 6.0

def test_sum_closure_default_mixed_numeric():
    assert n_sum(2, 3.5) == 5.5

def test_sum_closure_default_lists():
    assert n_sum([1, 2], [3, 4]) == [1, 2, 3, 4]