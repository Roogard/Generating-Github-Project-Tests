from python_programs.gcd import gcd
import pytest

# b==0: True
def test_gcd_b_zero_returns_a():
    assert gcd(7, 0) == 7

# b==0: False
def test_gcd_b_not_zero_recursionerror():
    with pytest.raises(RecursionError):
        gcd(3, 5)