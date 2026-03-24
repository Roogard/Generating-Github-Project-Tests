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

# Valid equivalence class: negative a, positive b (function uses modulo, works with negatives)
def test_gcd_negative_a():
    assert gcd(-48, 18) == 6

# Valid equivalence class: positive a, negative b
def test_gcd_negative_b():
    assert gcd(48, -18) == 6

# Valid equivalence class: both negative
def test_gcd_both_negative():
    assert gcd(-48, -18) == 6

# Valid equivalence class: a and b are equal (positive)
def test_gcd_equal_positive():
    assert gcd(12, 12) == 12

# Valid equivalence class: a and b are equal (negative)
def test_gcd_equal_negative():
    assert gcd(-12, -12) == 12

# Valid equivalence class: large integers
def test_gcd_large_integers():
    assert gcd(123456789, 987654321) == 9