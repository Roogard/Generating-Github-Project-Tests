import pytest
from correct_python_programs.gcd import gcd

# Valid equivalence class: two positive integers
def test_gcd_two_positive_integers():
    assert gcd(48, 18) == 6

# Valid equivalence class: positive and zero (b is zero)
def test_gcd_positive_and_zero():
    assert gcd(5, 0) == 5

# Valid equivalence class: zero and positive (a is zero)
def test_gcd_zero_and_positive():
    assert gcd(0, 7) == 7

# Valid equivalence class: both zero
def test_gcd_both_zero():
    assert gcd(0, 0) == 0

# Valid equivalence class: negative and positive integers
def test_gcd_negative_and_positive():
    assert gcd(-20, 30) == 10

# Invalid equivalence class: non-integer a
def test_gcd_non_integer_a():
    with pytest.raises(TypeError):
        gcd("a", 5)

# Invalid equivalence class: non-integer b
def test_gcd_non_integer_b():
    with pytest.raises(TypeError):
        gcd(5, "b")
