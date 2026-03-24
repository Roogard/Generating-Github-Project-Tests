from correct_python_programs.gcd import gcd

# Block analysis:
# block 1: if b == 0: (function entry)
# block 2: return a (then exit)
# block 3: else: return gcd(b, a % b) (then exit)

# covers: block 1, block 2 (base case)
def test_gcd_base_case():
    assert gcd(12, 0) == 12

# covers: block 1, block 3 (recursive case)
def test_gcd_recursive_case():
    assert gcd(12, 8) == 4

# additional test to ensure full coverage with different values
def test_gcd_another_recursive():
    assert gcd(54, 24) == 6