from correct_python_programs.gcd import gcd

# covers: stmt2 (True), stmt3
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# covers: stmt2 (False), stmt5 (and via recursion covers stmt2 True and stmt3)
def test_gcd_recursive_case():
    assert gcd(10, 4) == 2