from correct_python_programs.gcd import gcd

# path: b == 0 → return a
def test_gcd_b_is_zero():
    assert gcd(5, 0) == 5

# path: b != 0 → recurse once (a % b == 0 on next call)
def test_gcd_one_recursion():
    assert gcd(10, 5) == 5

# path: b != 0 → recurse multiple times before b == 0
def test_gcd_multiple_recursions():
    assert gcd(48, 18) == 6

# path: b != 0 → recurse with coprime numbers (gcd == 1)
def test_gcd_coprime():
    assert gcd(7, 13) == 1

# path: b != 0 → a < b initially (swap via recursion), then resolve
def test_gcd_a_less_than_b():
    assert gcd(3, 9) == 3

# path: b != 0 → a == b (gcd is a itself)
def test_gcd_equal_values():
    assert gcd(6, 6) == 6

# path: b != 0 → large values requiring multiple recursions
def test_gcd_large_values():
    assert gcd(1071, 462) == 21

# path: a == 0, b != 0 → recurse with (b, 0) → return b
def test_gcd_a_is_zero():
    assert gcd(0, 7) == 7