from python_programs.is_valid_parenthesization import is_valid_parenthesization

# covers: depth=0, loop body with '(' branch, depth += 1, return True
def test_single_open_paren():
    assert is_valid_parenthesization('(') == False

# covers: depth=0, loop with '(' and ')', depth += 1, depth -= 1, return True
def test_balanced_parens():
    assert is_valid_parenthesization('()') == True

# covers: else branch, depth -= 1, depth < 0 => True, return False
def test_unbalanced_close_first():
    assert is_valid_parenthesization(')(') == False

# covers: empty string, no loop body executed, return True
def test_empty_string():
    assert is_valid_parenthesization('') == True

# covers: multiple opens and closes, depth never negative, return True
def test_nested_balanced():
    assert is_valid_parenthesization('(())') == True

# covers: else branch with depth going negative mid-string
def test_extra_close():
    assert is_valid_parenthesization('())') == False

# covers: multiple pairs all balanced, return True
def test_multiple_balanced_pairs():
    assert is_valid_parenthesization('()()') == True

# covers: unmatched open parens (depth > 0 at end), return True is wrong — function returns True
def test_unmatched_open():
    # A valid parenthesization requires all opens to be closed; depth > 0 means invalid
    # The function returns True here (potential bug), but we test what it SHOULD return
    assert is_valid_parenthesization('(()') == False