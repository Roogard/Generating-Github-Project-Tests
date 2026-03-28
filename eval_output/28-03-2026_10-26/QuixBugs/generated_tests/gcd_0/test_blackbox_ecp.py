import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: both positive integers with a non-trivial GCD
def test_gcd_both_positive_common_divisor():
    result = gcd(12, 8)
    assert result == 4
    assert 12 % result == 0
    assert 8 % result == 0

# Valid equivalence class: coprime positive integers (GCD == 1)
def test_gcd_coprime_positive_integers():
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

# Valid equivalence class: one argument is a multiple of the other
def test_gcd_one_multiple_of_other():
    result = gcd(18, 6)
    assert result == 6
    assert 18 % result == 0
    assert 6 % result == 0

# Valid equivalence class: b == 0 (base case, GCD should be a)
def test_gcd_second_arg_zero():
    result = gcd(9, 0)
    assert result == 9
    assert 9 % result == 0

# Valid equivalence class: a == b (GCD should equal a and b)
def test_gcd_equal_arguments():
    result = gcd(5, 5)
    assert result == 5
    assert 5 % result == 0

# Valid equivalence class: a == 1 (GCD must be 1 for any b > 0)
def test_gcd_first_arg_one():
    result = gcd(1, 15)
    assert result == 1
    assert 1 % result == 0
    assert 15 % result == 0

# Valid equivalence class: large positive integers
def test_gcd_large_positive_integers():
    result = gcd(1000000, 500000)
    assert result == 500000
    assert 1000000 % result == 0
    assert 500000 % result == 0

# Property-based: result always divides both inputs for arbitrary valid pair
def test_gcd_divides_both_inputs():
    a, b = 56, 98
    result = gcd(a, b)
    assert a % result == 0
    assert b % result == 0

# Property-based: gcd is commutative
def test_gcd_commutative():
    assert gcd(36, 48) == gcd(48, 36)