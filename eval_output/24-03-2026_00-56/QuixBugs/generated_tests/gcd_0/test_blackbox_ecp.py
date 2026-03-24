import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: both positive integers, b != 0
def test_gcd_both_positive():
    assert gcd(48, 18) == 6

# Valid equivalence class: a positive, b zero
def test_gcd_b_zero():
    assert gcd(7, 0) == 7

# Valid equivalence class: a zero, b positive
def test_gcd_a_zero():
    assert gcd(0, 5) == 5

# Valid equivalence class: both zero
def test_gcd_both_zero():
    assert gcd(0, 0) == 0

# Valid equivalence class: a negative, b positive (function uses modulo, works with negatives)
def test_gcd_a_negative():
    assert gcd(-48, 18) == 6

# Valid equivalence class: a positive, b negative
def test_gcd_b_negative():
    assert gcd(48, -18) == 6

# Valid equivalence class: both negative
def test_gcd_both_negative():
    assert gcd(-48, -18) == 6

# Valid equivalence class: a and b are equal
def test_gcd_equal_numbers():
    assert gcd(15, 15) == 15

# Valid equivalence class: a and b are co‑prime
def test_gcd_coprime():
    assert gcd(17, 13) == 1