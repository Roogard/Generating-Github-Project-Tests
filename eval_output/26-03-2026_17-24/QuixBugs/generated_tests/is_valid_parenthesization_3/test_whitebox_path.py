import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True
def test_empty_string():
    assert is_valid_parenthesization('') == True

# path: loop 1 iter → paren=='(' → depth becomes 1 → return True (depth != 0 but still True)
def test_single_open_paren():
    # A single '(' leaves depth=1, function returns True (no early exit)
    # Note: this exposes that unmatched open parens still return True
    assert is_valid_parenthesization('(') == True

# path: loop 1 iter → paren != '(' → depth becomes -1 → depth < 0 → return False
def test_single_close_paren():
    assert is_valid_parenthesization(')') == False

# path: loop 2 iters → first '(' depth=1, then ')' depth=0, depth not <0 → return True
def test_matched_pair():
    assert is_valid_parenthesization('()') == True

# path: loop 2 iters → first ')' depth=-1 → depth < 0 → return False (early exit)
def test_close_before_open():
    assert is_valid_parenthesization(')(') == False

# path: loop many iters → all '(' → depth grows → return True
def test_multiple_open_parens_only():
    assert is_valid_parenthesization('(((') == True

# path: loop many iters → close parens make depth negative early → return False
def test_multiple_close_parens_early_negative():
    assert is_valid_parenthesization(')))') == False

# path: loop many iters → balanced nested parens → depth never negative → return True
def test_nested_balanced():
    assert is_valid_parenthesization('((()))') == True

# path: loop many iters → sequential balanced pairs → depth never negative → return True
def test_sequential_balanced():
    assert is_valid_parenthesization('()()()') == True

# path: loop many iters → depth goes negative mid-way → return False
def test_unbalanced_close_in_middle():
    assert is_valid_parenthesization('(()))(()') == False

# path: loop many iters → more close than open, depth eventually negative → return False
def test_more_close_than_open():
    assert is_valid_parenthesization('(()))') == False

# path: loop many iters → more open than close, depth never negative → return True
def test_more_open_than_close():
    assert is_valid_parenthesization('(((())') == True

# path: loop many iters → complex valid nesting → return True
def test_complex_valid():
    assert is_valid_parenthesization('(())(())') == True

# path: loop many iters → valid until last char causes negative depth → return False
def test_negative_depth_at_last_char():
    assert is_valid_parenthesization('()())') == False