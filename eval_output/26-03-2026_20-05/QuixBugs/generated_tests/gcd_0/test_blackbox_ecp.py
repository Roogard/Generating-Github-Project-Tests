import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: two positive integers with a non-trivial gcd
def test_gcd_two_positive_integers_with_common_factor():
    assert gcd(12, 8) == 4

# Valid equivalence class: two positive integers that are coprime (gcd == 1)
def test_gcd_coprime_positive_integers():
    assert gcd(7, 13) == 1

# Valid equivalence class: b == 0, should return a directly
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# Valid equivalence class: a == 0, should return b
def test_gcd_a_is_zero():
    assert gcd(0, 9) == 9

# Valid equivalence class: both inputs are equal (gcd should equal the number itself)
def test_gcd_equal_inputs():
    assert gcd(6, 6) == 6

# Valid equivalence class: one input is a multiple of the other
def test_gcd_one_is_multiple_of_other():
    assert gcd(20, 5) == 5

# Valid equivalence class: large positive integers
def test_gcd_large_positive_integers():
    assert gcd(1000000, 500000) == 500000

# Valid equivalence class: a < b (smaller first argument)
def test_gcd_a_less_than_b():
    assert gcd(3, 9) == 3