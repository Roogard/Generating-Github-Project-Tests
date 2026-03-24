import pytest
from python_programs.gcd import gcd

# covers: block 1 (b == 0 branch)
def test_gcd_b_zero():
    assert gcd(10, 0) == 10
    assert gcd(0, 0) == 0

# covers: block 2 (else branch leading to recursion)
def test_gcd_recursive_call_raises():
    with pytest.raises(RecursionError):
        gcd(1, 2)  # b != 0 triggers recursive branch leading to RecursionError