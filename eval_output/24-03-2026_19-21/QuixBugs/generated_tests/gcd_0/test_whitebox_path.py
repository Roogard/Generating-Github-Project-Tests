from correct_python_programs.gcd import gcd

# path: b == 0 → return a (no recursion)
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# path: b == 0 → return a when both zero
def test_gcd_zero_zero():
    assert gcd(0, 0) == 0

# path: b != 0 → b == 0 (one recursion)
def test_gcd_one_recursion():
    # gcd(14,7) → gcd(7,14%7=0) → return 7
    assert gcd(14, 7) == 7

# path: b != 0 → b != 0 → b != 0 → b != 0 → b == 0 (multiple recursions)
def test_gcd_multiple_recursions():
    # gcd(270,192) path: (270,192)→(192,78)→(78,36)→(36,6)→(6,0)→return 6
    assert gcd(270, 192) == 6