import pytest
from algorithms.array.n_sum import _sum_closure_default

def test_sum_closure_default_with_integers_at_zero():
    assert _sum_closure_default(0, 0) == 0

def test_sum_closure_default_with_integers_at_positive_boundary():
    assert _sum_closure_default(1, 1) == 2

def test_sum_closure_default_with_integers_at_negative_boundary():
    assert _sum_closure_default(-1, -1) == -2

def test_sum_closure_default_with_floats_at_zero():
    assert _sum_closure_default(0.0, 0.0) == 0.0

def test_sum_closure_default_with_floats_at_small_positive():
    assert _sum_closure_default(0.1, 0.2) == pytest.approx(0.3)

def test_sum_closure_default_with_floats_at_small_negative():
    assert _sum_closure_default(-0.1, -0.2) == pytest.approx(-0.3)

def test_sum_closure_default_with_strings_empty():
    assert _sum_closure_default("", "") == ""

def test_sum_closure_default_with_strings_single_char():
    assert _sum_closure_default("a", "b") == "ab"

def test_sum_closure_default_with_lists_empty():
    assert _sum_closure_default([], []) == []

def test_sum_closure_default_with_lists_single_element():
    assert _sum_closure_default([1], [2]) == [1, 2]

def test_sum_closure_default_with_none():
    with pytest.raises(TypeError):
        _sum_closure_default(None, None)

def test_sum_closure_default_mixed_types_raises():
    with pytest.raises(TypeError):
        _sum_closure_default(1, "a")