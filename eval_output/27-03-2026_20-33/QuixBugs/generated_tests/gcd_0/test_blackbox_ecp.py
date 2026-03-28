import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: both positive integers with a non-trivial gcd
def test_gcd_both_positive_common_divisor():
    result = gcd(12, 8)
    assert result == 4
    assert 12 % result == 0
    assert 8 % result == 0

# Valid equivalence class: coprime positive integers (gcd == 1)
def test_gcd_coprime_positive_integers():
    result = gcd(7, 13)
    assert result == 1
    assert 7 % result == 0
    assert 13 % result == 0

# Valid equivalence class: one argument is a multiple of the other
def test_gcd_one_multiple_of_other():
    result = gcd(20, 5)
    assert result == 5
    assert 20 % result == 0
    assert 5 % result == 0

# Valid equivalence class: b == 0 (base case, gcd should return a)
def test_gcd_second_arg_zero():
    result = gcd(9, 0)
    assert result == 9
    assert 9 % result == 0

# Valid equivalence class: both arguments are equal
def test_gcd_both_args_equal():
    result = gcd(6, 6)
    assert result == 6
    assert 6 % result == 0

# Valid equivalence class: a == 1 (gcd must be 1)
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

# Valid equivalence class: a < b (arguments reversed relative to typical order)
def test_gcd_first_arg_smaller_than_second():
    result = gcd(8, 12)
    assert result == 4
    assert 8 % result == 0
    assert 12 % result == 0