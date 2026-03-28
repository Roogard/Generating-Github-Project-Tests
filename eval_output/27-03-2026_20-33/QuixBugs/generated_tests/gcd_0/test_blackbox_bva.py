import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_equals_zero():
    result = gcd(5, 0)
    assert result == 5
    assert 5 % result == 0

def test_gcd_a_equals_zero():
    result = gcd(0, 5)
    assert result == 5
    assert 5 % result == 0

def test_gcd_both_zero():
    result = gcd(0, 0)
    assert result == 0

def test_gcd_a_equals_one():
    result = gcd(1, 7)
    assert result == 1
    assert 1 % result == 0
    assert 7 % result == 0

def test_gcd_b_equals_one():
    result = gcd(7, 1)
    assert result == 1
    assert 7 % result == 0
    assert 1 % result == 0

def test_gcd_equal_values():
    result = gcd(6, 6)
    assert result == 6
    assert 6 % result == 0

def test_gcd_a_equals_b_plus_one():
    result = gcd(7, 6)
    assert result == 1
    assert 7 % result == 0
    assert 6 % result == 0

def test_gcd_a_equals_b_minus_one():
    result = gcd(6, 7)
    assert result == 1
    assert 6 % result == 0
    assert 7 % result == 0

def test_gcd_a_multiple_of_b():
    result = gcd(12, 4)
    assert result == 4
    assert 12 % result == 0
    assert 4 % result == 0

def test_gcd_b_multiple_of_a():
    result = gcd(4, 12)
    assert result == 4
    assert 4 % result == 0
    assert 12 % result == 0

def test_gcd_coprime_values():
    result = gcd(13, 17)
    assert result == 1
    assert 13 % result == 0
    assert 17 % result == 0

def test_gcd_large_values():
    result = gcd(1000000, 999999)
    assert result == 1
    assert 1000000 % result == 0
    assert 999999 % result == 0

def test_gcd_large_common_factor():
    result = gcd(1000000, 500000)
    assert result == 500000
    assert 1000000 % result == 0
    assert 500000 % result == 0

def test_gcd_small_values_min_boundary():
    result = gcd(1, 1)
    assert result == 1
    assert 1 % result == 0

def test_gcd_typical_case():
    result = gcd(48, 18)
    assert result == 6
    assert 48 % result == 0
    assert 18 % result == 0

def test_gcd_result_divides_both_inputs():
    a, b = 252, 105
    result = gcd(a, b)
    assert a % result == 0
    assert b % result == 0

def test_gcd_symmetry():
    result_ab = gcd(36, 24)
    result_ba = gcd(24, 36)
    assert result_ab == result_ba

def test_gcd_prime_inputs():
    result = gcd(7, 11)
    assert result == 1
    assert 7 % result == 0
    assert 11 % result == 0

def test_gcd_one_is_prime():
    result = gcd(2, 100)
    assert result == 2
    assert 2 % result == 0
    assert 100 % result == 0

def test_gcd_max_single_digit_boundary():
    result = gcd(9, 9)
    assert result == 9
    assert 9 % result == 0