import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

def test_gcd_a_is_zero():
    assert gcd(0, 5) == 5

def test_gcd_both_zero():
    assert gcd(0, 0) == 0

def test_gcd_small_positive_numbers():
    assert gcd(6, 8) == 2

def test_gcd_large_numbers():
    assert gcd(48, 18) == 6

def test_gcd_negative_a():
    assert gcd(-6, 8) == 2

def test_gcd_negative_b():
    assert gcd(6, -8) == 2

def test_gcd_both_negative():
    assert gcd(-6, -8) == 2

def test_gcd_a_equals_b():
    assert gcd(7, 7) == 7

def test_gcd_one_is_one():
    assert gcd(1, 10) == 1

def test_gcd_one_is_one_reverse():
    assert gcd(10, 1) == 1

def test_gcd_coprime_numbers():
    assert gcd(8, 15) == 1

def test_gcd_a_multiple_of_b():
    assert gcd(20, 5) == 5

def test_gcd_b_multiple_of_a():
    assert gcd(5, 20) == 5