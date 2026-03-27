import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_equals_zero():
    assert gcd(5, 0) == 5

def test_gcd_a_equals_zero():
    assert gcd(0, 5) == 5

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_a_equals_one():
    assert gcd(1, 5) == 1

def test_gcd_b_equals_one():
    assert gcd(5, 1) == 1

def test_gcd_both_equal_one():
    assert gcd(1, 1) == 1

def test_gcd_a_equals_b():
    assert gcd(7, 7) == 7

def test_gcd_a_is_multiple_of_b():
    assert gcd(12, 4) == 4

def test_gcd_b_is_multiple_of_a():
    assert gcd(4, 12) == 4

def test_gcd_coprime_small_values():
    assert gcd(3, 5) == 1

def test_gcd_coprime_adjacent_values():
    assert gcd(7, 8) == 1

def test_gcd_common_factor_two():
    assert gcd(14, 10) == 2

def test_gcd_large_values_with_gcd_one():
    assert gcd(999999999, 1000000000) == 1

def test_gcd_large_values_with_common_factor():
    assert gcd(1000000, 500000) == 500000

def test_gcd_a_equals_two():
    assert gcd(2, 2) == 2

def test_gcd_b_equals_two_a_equals_one():
    assert gcd(1, 2) == 1

def test_gcd_a_equals_two_b_equals_one():
    assert gcd(2, 1) == 1

def test_gcd_typical_case():
    assert gcd(48, 18) == 6

def test_gcd_fibonacci_adjacent():
    assert gcd(89, 55) == 1

def test_gcd_same_large_value():
    assert gcd(1000000, 1000000) == 1000000