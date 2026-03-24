import pytest
from correct_python_programs.gcd import gcd

def test_gcd_base_case_b_zero():
    # b == 0 should return a directly
    assert gcd(5, 0) == 5

def test_gcd_single_recursion_divisible():
    # single recursion when a is a multiple of b
    assert gcd(14, 7) == 7

def test_gcd_multi_recursion_nontrivial():
    # multiple recursion steps to compute a nontrivial GCD
    assert gcd(21, 6) == 3

def test_gcd_a_zero_b_nonzero():
    # a == 0 should return b
    assert gcd(0, 5) == 5

def test_gcd_both_zero():
    # both a and b zero returns zero under this implementation
    assert gcd(0, 0) == 0

def test_gcd_invalid_type():
    # non-integer type for b should raise a TypeError
    with pytest.raises(TypeError):
        gcd(5, "3")