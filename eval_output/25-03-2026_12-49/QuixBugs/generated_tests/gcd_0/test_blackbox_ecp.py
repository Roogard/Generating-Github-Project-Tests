import pytest
from correct_python_programs.gcd import gcd

def test_gcd_positive_numbers():
    assert gcd(48, 18) == 6

def test_gcd_b_zero():
    assert gcd(5, 0) == 5

def test_gcd_a_zero():
    assert gcd(0, 7) == 7

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_negative_and_positive():
    assert gcd(-8, 12) == 4

def test_gcd_invalid_type_a():
    with pytest.raises(TypeError):
        gcd("a", 5)

def test_gcd_invalid_type_b():
    with pytest.raises(TypeError):
        gcd(5, [1, 2])