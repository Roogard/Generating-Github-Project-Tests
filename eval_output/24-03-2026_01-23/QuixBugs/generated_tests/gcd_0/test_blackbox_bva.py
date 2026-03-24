import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_zero():
    assert gcd(5, 0) == 5

def test_gcd_a_zero():
    assert gcd(0, 7) == 7

def test_gcd_zero_zero():
    assert gcd(0, 0) == 0

def test_gcd_b_one():
    assert gcd(10, 1) == 1

def test_gcd_a_one():
    assert gcd(1, 10) == 1

def test_gcd_coprime_inputs():
    assert gcd(8, 15) == 1

def test_gcd_common_divisor():
    assert gcd(14, 21) == 7

def test_gcd_swapped_arguments():
    assert gcd(21, 14) == 7