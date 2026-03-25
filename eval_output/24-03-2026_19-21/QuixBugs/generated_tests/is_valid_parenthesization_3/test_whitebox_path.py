from python_programs.is_valid_parenthesization import is_valid_parenthesization

# path: zero iterations → return True
def test_empty_string():
    assert is_valid_parenthesization("") is True

# path: one iteration → '(' branch → return True
def test_single_open():
    assert is_valid_parenthesization("(") is True

# path: one iteration → else branch → depth < 0 → return False
def test_single_close():
    assert is_valid_parenthesization(")") is False

# path: two iterations → '(' → else branch (depth returns to 0, no early return) → return True
def test_two_parens_balanced():
    assert is_valid_parenthesization("()") is True

# path: three iterations all '(' branches → return True
def test_three_opens():
    assert is_valid_parenthesization("(((") is True

# path: three iterations → '(' → ')' (no early return) → ')' (depth < 0) → return False
def test_early_negative_depth():
    assert is_valid_parenthesization("())") is False