from correct_python_programs.gcd import gcd

# catches: "b == 0" mutated to "a == 0" (wrong variable in base case)
def test_gcd_base_case_b_zero():
    assert gcd(5, 0) == 5

# catches: "return a" mutated to "return b" (wrong variable returned in base case)
def test_gcd_base_case_returns_a_not_b():
    assert gcd(7, 0) == 7

# catches: "a % b" mutated to "b % a" (swapped operands in modulo)
def test_gcd_mod_operand_order():
    # gcd(10, 3): 10 % 3 = 1, gcd(3,1)=1; if b%a used: 3%10=3, gcd(10,3) infinite or wrong
    assert gcd(10, 3) == 1

# catches: "gcd(b, a % b)" mutated to "gcd(a, a % b)" (wrong first recursive arg)
def test_gcd_recursive_first_arg():
    # gcd(12, 8): correct=4; if gcd(12, 12%8)=gcd(12,4)=4 -- use a case that diverges
    # gcd(9, 6): correct gcd(6, 9%6)=gcd(6,3)=gcd(3,0)=3
    # if mutated gcd(9, 9%6)=gcd(9,3)=gcd(3,0)=3 -- same, need different
    # gcd(14, 4): correct gcd(4, 14%4)=gcd(4,2)=gcd(2,0)=2
    # if mutated gcd(14, 14%4)=gcd(14,2)=gcd(2,0)=2 -- same
    # gcd(15, 6): correct gcd(6,3)=3; mutated gcd(15,3)=3 -- same
    # gcd(7, 3): correct gcd(3,1)=1; mutated gcd(7,1)=1 -- same
    # The mutation gcd(a, a%b) will eventually give wrong answer for:
    # gcd(4, 6): correct=2; gcd(6, 4%6)=gcd(6,4)=gcd(4,2)=2 correct path
    # mutated: gcd(4, 4%6)=gcd(4,4)=gcd(4,0)=4 -- WRONG
    assert gcd(4, 6) == 2

# catches: "gcd(b, a % b)" mutated to "gcd(b, b % a)" (wrong modulo)
def test_gcd_recursive_modulo():
    # gcd(9, 6): correct gcd(6, 9%6)=gcd(6,3)=3
    # mutated gcd(6, 6%9)=gcd(6,6)=gcd(6,0)=6 -- WRONG
    assert gcd(9, 6) == 3

# catches: base case condition "b == 0" mutated to "b != 0" (negation error)
def test_gcd_nonzero_b_does_not_return_a_immediately():
    assert gcd(6, 3) == 3

# basic known values for overall correctness
def test_gcd_coprime():
    assert gcd(7, 5) == 1

def test_gcd_same_numbers():
    assert gcd(8, 8) == 8

def test_gcd_multiple():
    assert gcd(12, 4) == 4

def test_gcd_larger_b():
    assert gcd(3, 9) == 3

def test_gcd_large_numbers():
    assert gcd(100, 75) == 25

# catches: "a % b" mutated to "a // b" (wrong operator)
def test_gcd_mod_vs_div():
    # gcd(7, 2): correct gcd(2, 1)=1; mutated gcd(2, 7//2)=gcd(2,3)=gcd(3,2%3)=...
    assert gcd(7, 2) == 1

# catches off-by-one: "b == 0" mutated to "b == 1"
def test_gcd_b_equals_one():
    # if base case fires at b==1, returns a instead of correct gcd
    assert gcd(6, 1) == 1

# catches: missing else / wrong branching
def test_gcd_both_nonzero():
    assert gcd(48, 18) == 6