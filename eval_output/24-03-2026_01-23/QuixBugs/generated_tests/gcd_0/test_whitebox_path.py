from correct_python_programs.gcd import gcd

# path: if b == 0 → True
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# path: if b == 0 → False → recursive call → if b == 0 → True
def test_gcd_one_recursion():
    # 4 % 2 == 0 so one recursive step then base
    assert gcd(4, 2) == 2

# path: if b == 0 → False → recursive call → if b == 0 → False → recursive call → if b == 0 → True
def test_gcd_two_recursions():
    # 10 % 4 == 2 → 4 % 2 == 0
    assert gcd(10, 4) == 2

# path: if b == 0 → False → recursive call x3 → finally if b == 0 → True
def test_gcd_three_recursions():
    # 30 % 18 == 12 → 18 % 12 == 6 → 12 % 6 == 0
    assert gcd(30, 18) == 6