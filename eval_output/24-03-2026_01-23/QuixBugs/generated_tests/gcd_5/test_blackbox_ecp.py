import pytest
from python_programs.gcd import gcd

def test_gcd_both_positive_common_divisor():
    assert gcd(8, 12) == 4

def test_gcd_both_positive_coprime():
    assert gcd(7, 5) == 1

def test_gcd_one_zero_first_operand():
    assert gcd(0, 5) == 5

def test_gcd_one_zero_second_operand():
    assert gcd(5, 0) == 5

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_negative_and_positive():
    assert gcd(-6, 9) == 3

def test_gcd_invalid_float_operands():
    with pytest.raises(RecursionError):
        gcd(5.5, 2.1)

def test_gcd_invalid_string_operands():
    with pytest.raises(TypeError):
        gcd("8", "12")

def test_gcd_invalid_none_operands():
    with pytest.raises(TypeError):
        gcd(None, None)