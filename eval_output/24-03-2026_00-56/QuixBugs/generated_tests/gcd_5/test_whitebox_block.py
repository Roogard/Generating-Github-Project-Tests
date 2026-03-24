from correct_python_programs.gcd import gcd

# Block mapping:
# block 1: if b == 0:
# block 2: return a (base case)
# block 3: else: (recursive case)
# block 4: return gcd(b, a % b) (still block 3)

# covers: block 1, block 2 (base case)
def test_gcd_base_case():
    assert gcd(5, 0) == 5

# covers: block 1, block 3, block 4 (recursive case, single recursion)
def test_gcd_recursive_single_step():
    assert gcd(10, 5) == 5

# covers: block 1, block 3, block 4 (multiple recursions)
def test_gcd_recursive_multiple_steps():
    assert gcd(48, 18) == 6

# covers: block 1, block 3, block 4 (with larger numbers)
def test_gcd_large_numbers():
    assert gcd(123456, 7890) == 6

# covers: block 1, block 3, block 4 (ensures symmetry)
def test_gcd_swapped_arguments():
    assert gcd(18, 48) == 6

# covers: block 1, block 2 (both zero edge case)
def test_gcd_both_zero():
    assert gcd(0, 0) == 0