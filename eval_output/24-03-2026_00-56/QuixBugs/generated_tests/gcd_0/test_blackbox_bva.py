import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_is_zero():
    assert gcd(12, 0) == 12

def test_gcd_a_is_zero():
    assert gcd(0, 12) == 12

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_small_positive_numbers():
    assert gcd(6, 8) == 2

def test_gcd_large_positive_numbers():
    assert gcd(48, 18) == 6

def test_gcd_equal_numbers():
    assert gcd(7, 7) == 7

def test_gcd_with_one_negative_number():
    # gcd should handle negatives via modulo; typical Euclidean algorithm works with negatives
    # a % b with negative a may produce negative remainder, but recursion continues
    # Testing boundary: one negative, one positive
    assert gcd(-12, 18) == 6 or gcd(-12, 18) == -6  # Allow either sign convention

def test_gcd_both_negative_numbers():
    assert gcd(-12, -18) == -6 or gcd(-12, -18) == 6  # Allow either sign convention

def test_gcd_with_one():
    assert gcd(1, 100) == 1

def test_gcd_with_prime_numbers():
    assert gcd(17, 13) == 1

def test_gcd_a_smaller_than_b():
    assert gcd(8, 12) == 4