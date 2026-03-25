import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_zero_returns_a():
    assert gcd(5, 0) == 5

def test_gcd_a_zero_returns_b():
    assert gcd(0, 7) == 7

def test_gcd_both_zero_returns_zero():
    assert gcd(0, 0) == 0

def test_gcd_common_divisor():
    assert gcd(48, 18) == 6

def test_gcd_coprime():
    assert gcd(17, 13) == 1

def test_gcd_negative_and_positive():
    assert gcd(-4, 6) == 2

def test_gcd_invalid_a_type():
    with pytest.raises(TypeError):
        gcd('a', 5)

def test_gcd_invalid_b_type():
    with pytest.raises(TypeError):
        gcd(5, 'b')