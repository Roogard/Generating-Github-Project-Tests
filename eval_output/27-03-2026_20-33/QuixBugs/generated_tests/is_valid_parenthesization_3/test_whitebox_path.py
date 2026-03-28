import pytest
from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: loop 0 iterations → return True (empty string)
def test_empty_string():
    result = is_valid_parenthesization("")
    assert result == True

# path: loop 1 iter → paren=='(' → depth becomes 1 → return True (but depth != 0, so actually invalid)
# A single '(' should be invalid (depth=1 at end, but the function returns True for depth>=0)
# According to the function's logic, it only returns False on negative depth, so '(' returns True
# We test what the function does structurally: single '(' hits the '(' branch once, returns True
def test_single_open_paren():
    result = is_valid_parenthesization("(")
    # The function returns True here (does not check final depth == 0)
    assert result == True

# path: loop 1 iter → paren != '(' → depth becomes -1 → depth < 0 → return False
def test_single_close_paren():
    result = is_valid_parenthesization(")")
    assert result == False

# path: loop many iters → all '(' branches → return True (unbalanced but no negatives)
def test_multiple_open_parens():
    result = is_valid_parenthesization("(((")
    assert result == True

# path: loop many iters → first paren is ')' → depth < 0 → return False early
def test_close_before_open():
    result = is_valid_parenthesization(")(")
    assert result == False

# path: loop many iters → alternating '(' then ')' → depth never negative → return True (balanced)
def test_balanced_simple():
    result = is_valid_parenthesization("()")
    assert result == True
    assert isinstance(result, bool)

# path: loop many iters → all balanced pairs → return True
def test_balanced_multiple_pairs():
    result = is_valid_parenthesization("()()()")
    assert result == True

# path: loop many iters → nested balanced → return True
def test_balanced_nested():
    result = is_valid_parenthesization("((()))")
    assert result == True

# path: loop many iters → mixed, depth goes negative partway → return False
def test_unbalanced_close_in_middle():
    result = is_valid_parenthesization("())(")
    assert result == False

# path: loop many iters → depth goes negative on last paren → return False
def test_unbalanced_one_extra_close():
    result = is_valid_parenthesization("())")
    assert result == False

# path: loop many iters → valid open/close mix but depth negative at end via close → return False
def test_more_closes_than_opens():
    result = is_valid_parenthesization(")))")
    assert result == False

# path: loop many iters → depth never negative, ends positive → return True
def test_more_opens_than_closes():
    result = is_valid_parenthesization("(()")
    assert result == True

# path: loop exactly 2 iters → '(' then ')' → depth 1 then 0 → return True
def test_two_iter_balanced():
    result = is_valid_parenthesization("()")
    assert result == True
    assert isinstance(result, bool)

# path: loop exactly 2 iters → ')' first → depth -1 → return False immediately
def test_two_iter_close_first():
    result = is_valid_parenthesization(")(")
    assert result == False