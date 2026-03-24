import pytest
from python_programs.gcd import gcd

# path: b == 0 → True → return a
def test_gcd_base_case():
    assert gcd(42, 0) == 42

# path: b == 0 → False → else → recursion → RecursionError (infinite recursion due to bug)
def test_gcd_recursion_error():
    with pytest.raises(RecursionError):
        gcd(1, 1)