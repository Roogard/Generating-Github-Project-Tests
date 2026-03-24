from python_programs.is_valid_parenthesization import is_valid_parenthesization

# '(' -> paren=='(' True ; ')' -> paren=='(' False, depth<0 False
def test_valid_simple_pair():
    assert is_valid_parenthesization("()") is True

# ')' -> paren=='(' False ; depth goes -1 -> depth<0 True
def test_single_close_returns_false():
    assert is_valid_parenthesization(")") is False

# '(' -> paren=='(' True ; no else branch -> depth<0 not evaluated (implicitly False)
def test_single_open_returns_true():
    assert is_valid_parenthesization("(") is True