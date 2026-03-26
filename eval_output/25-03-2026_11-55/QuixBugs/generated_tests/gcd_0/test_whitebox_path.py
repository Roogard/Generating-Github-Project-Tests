import pytest
from correct_python_programs.gcd import gcd

# path: b == 0 → return a
def test_gcd_base_case():
    assert gcd(5, 0) == 5
    assert gcd(0, 0) == 0

# path: b != 0 → recurse once → now b == 0 → return
def test_gcd_one_recursion():
    # gcd(2,1) → gcd(1,0) → 1
    assert gcd(2, 1) == 1
    # gcd(10, 6) → gcd(6, 4) → gcd(4, 2) → gcd(2, 0) → 2
    # This actually covers multiple recursions but confirms correctness for small inputs
    assert gcd(10, 6) == 2

# path: b != 0 → recurse multiple times → return at deeper level
def test_gcd_multiple_recursions():
    # A deeper example: gcd(106, 28) takes several steps before reaching b == 0
    assert gcd(106, 28) == 2
    # Another deeper chain
    assert gcd(255, 198) == 3