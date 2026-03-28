import pytest
from correct_python_programs.gcd import gcd

def test_gcd_b_is_zero():
    # gcd(a, 0) should return a
    result = gcd(5, 0)
    assert result == 5
    assert 5 % result == 0

def test_gcd_a_is_zero():
    # gcd(0, b) should return b since gcd(0, n) = n
    result = gcd(0, 5)
    assert result == 5
    assert 5 % result == 0

def test_gcd_both_zero():
    # gcd(0, 0) is conventionally 0
    result = gcd(0, 0)
    assert result == 0

def test_gcd_both_equal_to_one():
    # gcd(1, 1) = 1
    result = gcd(1, 1)
    assert result == 1
    assert 1 % result == 0

def test_gcd_a_is_one():
    # gcd(1, n) = 1 for any n
    result = gcd(1, 100)
    assert result == 1
    assert 1 % result == 0
    assert 100 % result == 0

def test_gcd_b_is_one():
    # gcd(n, 1) = 1 for any n
    result = gcd(100, 1)
    assert result == 1
    assert 100 % result == 0
    assert 1 % result == 0

def test_gcd_both_equal_small():
    # gcd(n, n) = n
    result = gcd(7, 7)
    assert result == 7
    assert 7 % result == 0

def test_gcd_both_equal_large():
    # gcd(n, n) = n for large n
    result = gcd(1000000, 1000000)
    assert result == 1000000
    assert 1000000 % result == 0

def test_gcd_coprime_numbers():
    # gcd of two coprime numbers should be 1
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

def test_gcd_one_divides_other():
    # gcd(a, b) where a divides b should return a
    result = gcd(4, 8)
    assert result == 4
    assert 4 % result == 0
    assert 8 % result == 0

def test_gcd_other_divides_one():
    # gcd(a, b) where b divides a should return b
    result = gcd(8, 4)
    assert result == 4
    assert 8 % result == 0
    assert 4 % result == 0

def test_gcd_typical_case():
    # gcd(12, 18) = 6
    result = gcd(12, 18)
    assert result == 6
    assert 12 % result == 0
    assert 18 % result == 0

def test_gcd_result_divides_both_inputs():
    # Property: result must divide both a and b
    a, b = 48, 36
    result = gcd(a, b)
    assert a % result == 0
    assert b % result == 0

def test_gcd_large_prime_inputs():
    # gcd of two distinct primes = 1
    result = gcd(9973, 9967)
    assert result == 1
    assert 9973 % result == 0
    assert 9967 % result == 0

def test_gcd_large_numbers_with_common_factor():
    # gcd(100000, 75000) = 25000
    result = gcd(100000, 75000)
    assert result == 25000
    assert 100000 % result == 0
    assert 75000 % result == 0

def test_gcd_a_equals_two():
    # gcd(2, b) boundary near minimum positive even
    result = gcd(2, 4)
    assert result == 2
    assert 2 % result == 0
    assert 4 % result == 0

def test_gcd_b_equals_two():
    # gcd(a, 2) boundary near minimum positive even
    result = gcd(4, 2)
    assert result == 2
    assert 4 % result == 0
    assert 2 % result == 0

def test_gcd_commutative_property():
    # gcd(a, b) == gcd(b, a)
    a, b = 48, 36
    assert gcd(a, b) == gcd(b, a)

def test_gcd_single_step_reduction():
    # gcd where b < a and one step reduces to base case
    result = gcd(6, 3)
    assert result == 3
    assert 6 % result == 0
    assert 3 % result == 0

def test_gcd_minimum_positive_inputs():
    # gcd(1, 1) at minimum positive boundary
    result = gcd(1, 1)
    assert result == 1