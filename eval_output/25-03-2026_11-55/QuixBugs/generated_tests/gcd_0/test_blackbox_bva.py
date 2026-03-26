import pytest
from correct_python_programs.gcd import gcd

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_first_just_below_zero():
    # a = -1 (just below zero), b = typical positive
    assert gcd(-1, 5) == 1

def test_gcd_first_at_zero():
    # a = 0, b = typical positive
    assert gcd(0, 5) == 5

def test_gcd_first_just_above_zero():
    # a = 1 (just above zero), b = typical positive
    assert gcd(1, 5) == 1

def test_gcd_second_just_below_zero():
    # a = typical positive, b = -1 (just below zero)
    assert gcd(5, -1) == -1

def test_gcd_second_at_zero():
    # a = typical positive, b = 0
    assert gcd(5, 0) == 5

def test_gcd_second_just_above_zero():
    # a = typical positive, b = 1 (just above zero)
    assert gcd(5, 1) == 1

def test_gcd_typical_nontrivial():
    # both a and b positive with a common divisor > 1
    assert gcd(12, 18) == 6

def test_gcd_coprime_values():
    # both a and b positive and coprime
    assert gcd(8, 15) == 1