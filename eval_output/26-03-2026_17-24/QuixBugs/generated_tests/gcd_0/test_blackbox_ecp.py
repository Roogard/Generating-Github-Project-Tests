import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: two positive integers with a common divisor > 1
def test_gcd_two_positive_integers_with_common_divisor():
    assert gcd(12, 8) == 4

# Valid equivalence class: two positive integers that are coprime (gcd = 1)
def test_gcd_coprime_positive_integers():
    assert gcd(7, 13) == 1

# Valid equivalence class: b == 0 (base case, returns a)
def test_gcd_second_arg_zero():
    assert gcd(5, 0) == 5

# Valid equivalence class: a == 0 (gcd should be b)
def test_gcd_first_arg_zero():
    assert gcd(0, 9) == 9

# Valid equivalence class: both arguments are equal (gcd equals either)
def test_gcd_equal_arguments():
    assert gcd(6, 6) == 6

# Valid equivalence class: one argument is a multiple of the other
def test_gcd_one_is_multiple_of_other():
    assert gcd(15, 5) == 5

# Valid equivalence class: large positive integers
def test_gcd_large_positive_integers():
    assert gcd(1000000, 500000) == 500000

# Valid equivalence class: a < b (arguments in reverse order relative to size)
def test_gcd_first_arg_less_than_second():
    assert gcd(4, 16) == 4