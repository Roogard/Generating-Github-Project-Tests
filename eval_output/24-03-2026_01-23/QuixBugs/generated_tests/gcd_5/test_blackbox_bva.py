import pytest
from python_programs.gcd import gcd

def test_gcd_both_zero():
    # boundary: a = 0 (min), b = 0 (min)
    assert gcd(0, 0) == 0

def test_gcd_a_zero_b_min_plus_one():
    # boundary: a = 0 (min), b = 1 (min+1)
    assert gcd(0, 1) == 1

def test_gcd_a_min_plus_one_b_zero():
    # boundary: a = 1 (min+1), b = 0 (min)
    assert gcd(1, 0) == 1

def test_gcd_min_plus_one_each():
    # boundary: a = 1 (min+1), b = 1 (min+1)
    assert gcd(1, 1) == 1

def test_gcd_coprime_values():
    # typical: two coprime numbers
    assert gcd(14, 15) == 1

def test_gcd_common_divisor():
    # typical: non-trivial common divisor
    assert gcd(56, 42) == 14

def test_gcd_large_numbers():
    # larger values to ensure performance on big ints
    assert gcd(1000000, 250000) == 250000