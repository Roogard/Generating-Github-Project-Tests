from python_programs.gcd import gcd
import pytest

# covers: stmt1 (b == 0 True), stmt2 (return a)
def test_gcd_base_case():
    assert gcd(42, 0) == 42

# covers: stmt1 (b == 0 False), stmt4 (recursive call)
def test_gcd_recursion_branch_raises_recursion_error():
    with pytest.raises(RecursionError):
        gcd(1, 1)  # triggers infinite recursion due to flawed implementation