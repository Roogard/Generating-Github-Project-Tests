from correct_python_programs.gcd import gcd
import math

# --- Statement Coverage ---

def test_statement_base_case():
    # b == 0: True → returns a immediately
    # A correct gcd(5, 0) should return 5
    result = gcd(5, 0)
    assert result == 5

def test_statement_recursive_case():
    # b != 0: enters recursion
    # A correct gcd(12, 8) should equal math.gcd(12, 8)
    result = gcd(12, 8)
    assert result == math.gcd(12, 8)

# --- Block Coverage ---

def test_block_else_branch():
    # Ensures the else block is entered (b != 0)
    # A correct gcd(9, 3) should equal math.gcd(9, 3) == 3
    result = gcd(9, 3)
    assert result == math.gcd(9, 3)

def test_block_base_case_return():
    # Ensures the if-block return is reached (b == 0)
    # A correct gcd(7, 0) should return 7
    result = gcd(7, 0)
    assert result == 7

# --- Condition Coverage ---

def test_condition_b_equals_zero_true():
    # b == 0: True
    # A correct gcd(1, 0) should return 1
    result = gcd(1, 0)
    assert result == 1

def test_condition_b_equals_zero_false():
    # b == 0: False → recurse
    # A correct gcd(10, 5) should equal math.gcd(10, 5) == 5
    result = gcd(10, 5)
    assert result == math.gcd(10, 5)

def test_condition_b_nonzero_leading_to_zero():
    # b == 0: False initially, True in recursive call
    # A correct gcd(6, 3) should equal math.gcd(6, 3) == 3
    result = gcd(6, 3)
    assert result == math.gcd(6, 3)

# --- Path Coverage ---

def test_path_direct_base_case():
    # path: b==0 True → return a (single step, no recursion)
    # A correct gcd(42, 0) should return 42
    result = gcd(42, 0)
    assert result == 42

def test_path_one_recursion():
    # path: b!=0 → recurse once with (b, a%b) where a%b == 0 → base case
    # gcd(4, 2): first call b=2!=0, recurse gcd(2, 0) → returns 2
    result = gcd(4, 2)
    assert result == math.gcd(4, 2)
    assert result == 2

def test_path_multiple_recursions():
    # path: b!=0 → recurse multiple times before reaching base case
    # gcd(48, 18): multiple steps needed
    result = gcd(48, 18)
    assert result == math.gcd(48, 18)
    assert result == 6

def test_path_coprime_numbers():
    # path: multiple recursions, gcd == 1
    # gcd(13, 7): coprime, requires several recursive steps
    result = gcd(13, 7)
    assert result == math.gcd(13, 7)
    assert result == 1

def test_path_equal_numbers():
    # path: b != 0, a % b == 0 immediately (a == b)
    # gcd(5, 5): recurse with gcd(5, 0) → returns 5
    result = gcd(5, 5)
    assert result == math.gcd(5, 5)
    assert result == 5

def test_property_commutativity():
    # A correct gcd is commutative: gcd(a, b) == gcd(b, a)
    assert gcd(12, 8) == gcd(8, 12)

def test_property_divisibility():
    # A correct gcd must divide both a and b
    a, b = 56, 98
    result = gcd(a, b)
    assert a % result == 0
    assert b % result == 0

def test_property_gcd_of_one():
    # gcd(1, n) should always be 1 for any positive n
    result = gcd(1, 100)
    assert result == 1

def test_property_large_numbers():
    # A correct gcd on large inputs should match math.gcd
    a, b = 123456, 789012
    result = gcd(a, b)
    assert result == math.gcd(a, b)
    assert a % result == 0
    assert b % result == 0