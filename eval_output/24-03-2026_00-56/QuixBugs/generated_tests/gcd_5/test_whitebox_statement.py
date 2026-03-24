from correct_python_programs.gcd import gcd

# covers: if condition True, return a
def test_gcd_b_zero():
    assert gcd(12, 0) == 12

# covers: if condition False, else branch, recursive call (which eventually hits base case)
def test_gcd_non_zero():
    assert gcd(54, 24) == 6