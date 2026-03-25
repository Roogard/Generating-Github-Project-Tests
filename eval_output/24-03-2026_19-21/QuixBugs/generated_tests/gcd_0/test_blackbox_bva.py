import pytest
from correct_python_programs.gcd import gcd

def test_gcd_both_zero():
    # Boundary: both arguments are zero
    assert gcd(0, 0) == 0

def test_gcd_zero_first_argument():
    # Boundary: first argument zero, second positive
    assert gcd(0, 5) == 5

def test_gcd_zero_second_argument():
    # Boundary: first argument positive, second zero
    assert gcd(5, 0) == 5

def test_gcd_minimal_positive():
    # Boundary: smallest positive inputs
    assert gcd(1, 1) == 1

def test_gcd_coprime_numbers():
    # Typical: two coprime numbers
    assert gcd(13, 7) == 1

def test_gcd_common_divisor():
    # Typical: common divisor exists
    assert gcd(14, 21) == 7

def test_gcd_swapped_arguments_common_divisor():
    # Inverse order of a and b
    assert gcd(21, 14) == 7

def test_gcd_negative_first_argument():
    # Boundary: first argument just below zero
    assert gcd(-1, 5) == 1

def test_gcd_negative_second_argument():
    # Boundary: second argument just below zero
    assert gcd(5, -1) == -1

def test_gcd_negative_and_positive():
    # First argument negative, second positive non-boundary
    assert gcd(-4, 2) == 2

def test_gcd_positive_and_negative():
    # First argument positive, second negative non-boundary
    assert gcd(4, -2) == -2