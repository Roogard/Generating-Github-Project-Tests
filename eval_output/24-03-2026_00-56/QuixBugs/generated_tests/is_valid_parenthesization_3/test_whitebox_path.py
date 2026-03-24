import pytest
from correct_python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return depth == 0 (True)
def test_empty_string():
    assert is_valid_parenthesization("") == True

# path: loop 1 iteration → paren == '(' → depth += 1 → loop ends → return depth == 0 (False)
def test_single_open():
    assert is_valid_parenthesization("(") == False

# path: loop 1 iteration → paren != '(' → depth -= 1 → depth < 0 → return False
def test_single_close():
    assert is_valid_parenthesization(")") == False

# path: loop 2 iterations → both '(' → depth increments twice → loop ends → return depth == 0 (False)
def test_two_opens():
    assert is_valid_parenthesization("((") == False

# path: loop 2 iterations → first '(' → second ')' → depth increments then decrements → depth == 0 at end → return True
def test_matching_pair():
    assert is_valid_parenthesization("()") == True

# path: loop 2 iterations → first ')' → depth decrements → depth < 0 → return False
def test_close_first():
    assert is_valid_parenthesization(")(") == False

# path: loop 2 iterations → first ')' → depth decrements → depth < 0 → return False (same path as above, different input)
def test_two_closes():
    assert is_valid_parenthesization("))") == False

# path: loop many iterations → all '(' → depth increments each time → loop ends → return depth == 0 (False)
def test_many_opens():
    assert is_valid_parenthesization("(((") == False

# path: loop many iterations → alternating '(' and ')' starting with '(' → depth never negative → ends with depth == 0 → return True
def test_nested_valid():
    assert is_valid_parenthesization("(()())") == True

# path: loop many iterations → at some point depth goes negative → return False
def test_invalid_intermediate_depth():
    assert is_valid_parenthesization("())(") == False

# path: loop many iterations → depth never negative → ends with depth > 0 → return False
def test_valid_prefix_but_extra_open():
    assert is_valid_parenthesization("(()") == False

# path: loop many iterations → depth never negative → ends with depth < 0 (impossible because depth<0 triggers early return)
# This path is infeasible because depth < 0 triggers immediate False return.
# Instead we test a path where depth becomes negative after many iterations.
def test_valid_prefix_then_extra_close():
    assert is_valid_parenthesization("())") == False